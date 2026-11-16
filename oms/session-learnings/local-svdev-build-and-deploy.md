# Local `svdev` (IIS) build and deploy — the whole picture in one place

**Status:** verified (distilled 2026-11-16)
**Evidence:** live debugging session fixing DCOMS-30186 (Sales by User date-field alignment) end to end, from "site won't even load" to a clean login and a working report page, on `C:\oms`.
**Audience:** future sessions hitting IIS/compile errors on the local OMS checkout — read this before re-deriving any of it.

This ties together things that are otherwise scattered across the OMS Setup Wizard script, `oms-nuget-aws-setup/`, and tribal knowledge: which checkout IIS actually serves, what the wizard does and doesn't fix, the stale-`/bin`-DLL trap after switching branches, and the exact chain of version mismatches we hit and how we fixed each one.

**Related:** [databases-and-local-access.md](./databases-and-local-access.md) (tunnel ports, DB users), [iis-app-pool-and-config-cache.md](./iis-app-pool-and-config-cache.md) (remote pod2 IIS — different machine, same ideas), `C:\PROD\ConnectorSuite\oms-nuget-aws-setup\README.md` (CodeArtifact + build kit, referenced throughout below).

---

## 1. There can be more than one OMS checkout — know which one IIS serves

On this machine there were **two** clones: `C:\oms` and `C:\OMS Other\oms`. Only `C:\oms` is what the local IIS site (`svdev`) actually serves — it's also the OMS Setup Wizard's hardcoded default `ProjectPath`. Editing web.config/etc. in the wrong clone produces zero behavior change and wastes a lot of time looking like the edits "don't take."

**Before debugging any local IIS behavior, confirm the binding:** `appcmd list site` / `applicationHost.config` needs admin rights we didn't have; the fast tell is the hosts file entry plus the wizard's default path.

- Hosts file: `127.0.0.1 svdev` (in `C:\Windows\System32\drivers\etc\hosts`)
- Site URL: `http://svdev/backadmin/...`
- Real checkout: `C:\oms` (confirm with `git -C C:\oms status` / `git log -1`)

## 2. DB tunnel must be up — and it's silent-failure, not loud-failure

Site needs a Postgres tunnel on **port 1111** (see [databases-and-local-access.md](./databases-and-local-access.md)). Role/user is per environment — e.g. `shareddev_postgres` for the shared dev DB. If the tunnel isn't running, pages don't show an obvious "DB down" message — see §5 for why errors look generic instead.

## 3. The OMS Setup Wizard — what it actually does, and what it does NOT fix

GUI script at `C:\Users\<user>\OneDrive - Aptos\Documents\WORK\PROJECTS\OMS Setup\OMS Setup Wizard V3.ps1` (also a V2). Inputs: project path, AWS username, env (dev/qa), DB port. Running it (or its logic) rewrites:

| File | What changes |
|---|---|
| `EOM.ShopLogicApi/Web.config` | Adds `AWSProfileName`/`AWSProfilesLocation`/`AWSRegion`, flips `space` to `pod`, sets `env` |
| `OMS.Configuration/App.config` | Uncomments `product`/`env`/`space` keys |
| `OMS.Configuration/ConfigurationHelper.cs` | **Hardcodes a literal DB connection string** (including a **plaintext password**) directly into `GetDBConnectionString(...)`'s return statement — this is why the normal AWS-Parameter-Store-backed implementation gets bypassed locally |
| `ShopVisible.Core.ShopLogic/backadmin/login.aspx` | Rewrites the post-login `parentWindow` redirect to `http://svdev` |
| `ShopVisible.Core.ShopLogic/web.config` | Adds the same product/space/env/AWS keys, plus a batch of `<assemblyBinding>` redirects (see §6) |
| `ShopVisible.Core.ShopLogic/licenses.licx` | **Deletes it**, creates `licenses.licx.exclude` if missing |

**These are tracked files.** The wizard edits them in place with no backup and no `.gitignore` exemption. **Never commit or stage these specific files** — always check `git status` only shows these (plus your real, intended change) before any commit. The hardcoded password is a standing risk if anyone pushes a branch without checking.

**It does NOT fix:** stale `/bin` binaries, binding-redirect version drift, or anything in §6–§8 below. It's a one-time local-config wiring step, not a build/deploy tool.

## 4. `customErrors` hides the real exception — flip it to see what's actually wrong

Default is `mode="On"` in `ShopVisible.Core.ShopLogic/web.config`, which shows a generic "Server Error" page for **everything**, including a confusing **"another exception occurred while executing the custom error page"** double-fault message that tells you nothing. Temporarily set:

```xml
<customErrors mode="Off" defaultRedirect="/backadmin/error.aspx" />
```

...to get the real ASP.NET yellow-screen-of-death with an actual exception type, message, and stack trace. This is what let us actually diagnose every issue in §6. Local-only change, don't commit it either.

(Separately: `Global.vb`'s `Application_Error` has its own `IsDeveloperException(siteURL)` check that `Exit Sub`s — i.e. defers to ASP.NET's own error handling — whenever the `siteURL` web.config key contains `"localhost"` or `"svdev"`. It already does on this checkout, so that's not the blocker; `customErrors` is.)

## 5. Recompiles are slow — don't assume the site is down on timeout

Any edit to `web.config` (even just `touch`ing it to force a recycle) triggers an AppDomain restart, and the **first** request after that does a full ASP.NET batch recompile of a very large legacy Web Site project. This routinely took **60–150+ seconds**, occasionally longer, before returning anything. A `curl --max-time 60` timing out is not evidence the app is broken — retry with 150–240s before concluding anything crashed.

## 6. The stale-`/bin`-DLL trap after switching branches — and the exact chain we hit

`ShopVisible.Core.ShopLogic` is a **Web Site project**: `.aspx` markup and code-behind compile per-request from source, with **no build step of their own**. But it references many separate class-library projects (`DCEOM.Infrastructure`, `DCEOM.DataAccess`, `AmplifyTokenManager`, etc.) via their compiled DLLs sitting in `ShopVisible.Core.ShopLogic/bin/`. **`git checkout <branch>` changes source, never touches `/bin`.** If source moved forward (new types/methods referenced) since those DLLs were last built, you get a cascade of unrelated-looking compile/runtime errors, one at a time, each only visible after fixing the previous one (because the Web Site project only reports the *first* thing it chokes on).

**Pattern for every one of these:** read the exception's `Source File`/stack trace to find which assembly/type is missing-or-mismatched → build *that specific* `.csproj` directly with MSBuild (not the full solution — see §7 for why) → copy the fresh `.dll`/`.pdb` from `<Project>\bin\Debug\` (or `<Project>\bin\`, varies by project) into `ShopVisible.Core.ShopLogic\bin\` → `touch` `web.config` → retest (patiently, §5).

This is the exact sequence we worked through, in order, on one branch switch:

| Symptom | Root cause | Fix |
|---|---|---|
| `error CS0234: ... 'ServiceManagerModernizationGuard' does not exist in ... DCEOM.Infrastructure` (in `siteManager.master.cs`, used by every backadmin page) | Stale `DCEOM.Infrastructure.dll` | Build `DCEOM.Infrastructure\DCEOM.Infrastructure.csproj`; copy its output + `DCEOM.Infrastructure.Interfaces`, `DCEOM.Models`, `OMS.Configuration`, `DCEOM.Interfaces`, `EOM.Component.Authentication` DLLs |
| `TypeLoadException: Method 'GetRefundBatchIdByPspReference' ... does not have an implementation` (WCF `Reference.svcmap` parse, `DCEOM.DataAccess.AdyenPaymentTrackingRepository`) | Stale `DCEOM.DataAccess.dll` | Ran `oms-nuget-aws-setup\scripts\Build-OmsOdxSlice.ps1` (builds `DCEOM.DataAccess`, `DCEOM.Services`, `DCEOM.WebApi` (+ unit test projects), `ShopVisible.Services.Shipping`); copied outputs |
| `MissingMethodException: Void Amazon.Runtime.ClientConfig.set_ServiceId(String)` in `CognitoManager.CognitoUserManagement..ctor()` | Stale `AmplifyTokenManager.dll` / mismatched AWS SDK pair | Built `AmplifyTokenManager\CognitoManager.csproj`; copied its output + `ShopVisible.Core.HelperClasses`, `DCEOM.DataAccess.Interfaces`, `ShopVisible.Core.SerializationClasses`, `ShopVisible.WebReferences.Interfaces` **and** copied `AWSSDK.Core.dll` + `AWSSDK.CognitoIdentityProvider.dll` **as a matched pair** from `AmplifyTokenManager\bin\` — same `AssemblyVersion` string does **not** mean identical binaries for AWS SDK NuGet packages; always copy both from the same source together |
| `FileLoadException: ...System.Threading.Tasks.Extensions, Version=4.2.0.0 ... manifest definition does not match` | Deployed DLL was `4.2.0.1`, web.config `<bindingRedirect>` target was stale at `4.2.0.0` | Edited both `<bindingRedirect oldVersion="0.0.0.0-4.2.0.0" newVersion="4.2.0.0">` entries in `ShopVisible.Core.ShopLogic\web.config` → `4.2.0.1` |
| `BC32206: ... direct reference to version 2.0.1.0 and an indirect reference ... use version 2.1.0.0 (or higher) of EOM.Kernel.Infrastructure.Interfaces` | Deployed `EOM.Kernel.Infrastructure(.Interfaces).dll` was `2.0.1.0`; a dependent needed `2.1.0+` | **Binding redirects don't apply** — these assemblies are unsigned (no public key token). Instead copied both DLLs from the restored `packages\EOM.Kernel.Infrastructure.2.1.0\lib\net472\` into `ShopLogic\bin` so only one consistent version exists |
| Post-Cognito-login callback: `FileLoadException: System.Runtime.CompilerServices.Unsafe, Version=4.0.4.0 ... manifest definition does not match` (in `CognitoManager.SaveLoggedinUserData.SetSalesPersonInfoAndCookies`) | Same binding-redirect staleness as the Threading.Tasks.Extensions case — deployed `4.0.5.0`, redirect target `4.0.4.0`/`4.0.4.1` | Edited both `<bindingRedirect>` entries for `System.Runtime.CompilerServices.Unsafe` → `4.0.5.0` |

After all of the above: `login.aspx` → clean `200` with the real Cognito/Amplify login UI, full Cognito login succeeds (confirms local `oms-pod-dev-strategy-app-client` client config matches the real pod-dev user pool), and backadmin report pages render normally.

**Rule of thumb:** when you hit one of these, don't rebuild the whole solution — find the owning `.csproj`, build just that, copy outputs, retest. Only escalate to §7 if the specific-project approach can't find a project (e.g. it's a NuGet package, not a project).

## 7. Full solution build (`DCEOM.All.sln` / `Solutions\ShopVisible.ShopLogic.sln`) — still broken, use the slice instead

Plain MSBuild on the full solution currently fails for reasons **unrelated** to any application bug:

- `error MSB3202: The project file "...\<Project>.csproj" was not found` for: `ShopVisible.Core.Crypto`, `ShopVisible.Core.ParsingEngine`, `ShopVisible.JobManager.Common.Email`, `ShopVisible.JobManager.Common.Messages`, `ShopVisible.JobManager.DataLayer`, `ShopVisible.JobManager.DataObjects`, `ShopVisible.JobManager.HelperObjects`, `DCEOM.Kernel.Infrastructure`, `DCEOM.Kernel.InfrastructureVB`. These are listed in the `.sln` but don't exist as project folders on this machine — **unresolved**, didn't chase down whether they're meant to be separate repos/submodules.
- `error MSB3644: The reference assemblies for .NETFramework,Version=v4.5 were not found` for `ShopVisible.Core.ShippingUtilities.csproj` — this machine only has newer targeting packs installed. **Unresolved** (would need the .NET 4.5 Developer Pack installed).

**Don't try to fix the full solution build to unblock local dev.** `C:\PROD\ConnectorSuite\oms-nuget-aws-setup\` is the actual supported path:

```powershell
cd C:\PROD\ConnectorSuite\oms-nuget-aws-setup\scripts
.\Setup-And-Restore.ps1       # Login-CodeArtifact.ps1 + nuget restore DCEOM.All.sln -> c:\oms\packages
.\Build-OmsOdxSlice.ps1       # builds config.json's odxBuildProjects list only (currently DataAccess/Services/WebApi/Shipping + their tests)
```

Needs `NugetAWS.env` (AWS keys, gitignored, treat like a password file) and `config.json` → `omsRepoPath` pointed at the real checkout. See its `README.md` for the CodeArtifact domain/repo/feed details and troubleshooting table.

For anything **not** in `odxBuildProjects`, build that one `.csproj` directly with MSBuild (per §6's pattern) rather than fighting the full `.sln`.

## 8. Stray git worktrees inside the checkout can poison unrelated builds

Found `C:\oms\_wt-sanika-29425` — a **registered git worktree** (another engineer's in-progress branch, `feature/sanikaam/DCOMS-29425-...`) sitting nested inside the main `C:\oms` tree from some prior session. `ShopVisible.Core.HelperClasses.vbproj`'s custom Roslyn analyzer (`DCOMS29789`, a "DB connection not released" rule) picked up duplicate source through it and failed on dozens of completely unrelated files.

**Before any full/partial solution build, check:** `git -C C:\oms worktree list`. If you find a stray one:
1. `git -C <worktree-path> status --porcelain` — confirm no uncommitted changes
2. `git -C <worktree-path> branch -vv` — confirm its branch is pushed (not behind by uncommitted local-only work)
3. `git -C C:\oms worktree remove <path>` — safe, doesn't touch the branch or its commits, just the extra working-directory checkout
