# OMS NuGet + AWS CodeArtifact (local build kit)

Self-contained folder for restoring private Aptos NuGet packages and building `c:\oms` on a fresh machine or new Cursor chat.

**Setup root:** `c:\PROD\ConnectorSuite\oms-nuget-aws-setup`

## Prerequisites

- [AWS CLI v2](https://aws.amazon.com/cli/) on PATH (`aws`)
- Visual Studio 2022+ with **MSBuild** (Desktop development workload)
- OMS repo cloned at `c:\oms` (or edit `config.json` → `omsRepoPath`)
- Valid keys in `NugetAWS.env` (copy from `NugetAWS.env.example` if missing)

## Quick start (new session)

From PowerShell:

```powershell
cd c:\PROD\ConnectorSuite\oms-nuget-aws-setup\scripts
.\Setup-And-Restore.ps1
.\Build-OmsOdxSlice.ps1
```

Or step by step:

| Step | Script | What it does |
|------|--------|----------------|
| 1 | `Login-CodeArtifact.ps1` | Loads `NugetAWS.env`, `aws sts get-caller-identity`, `aws codeartifact login --tool nuget` (~12h token) |
| 2 | `Restore-OmsSolution.ps1` | `nuget restore DCEOM.All.sln` → `c:\oms\packages` |
| 3 | `Build-OmsOdxSlice.ps1` | MSBuild ODX + `ShopVisible.Services.Shipping` projects |

## Files

| File | Purpose |
|------|---------|
| `NugetAWS.env` | Local AWS access key + region ( **do not commit** ; listed in `.gitignore`) |
| `NugetAWS.env.example` | Template without secrets |
| `config.json` | OMS path, solution name, CodeArtifact domain/repo, ODX project list |
| `scripts/` | PowerShell automation |
| `tools/nuget.exe` | Auto-downloaded on first run if missing |

## CodeArtifact feed (reference)

- Domain: `aptos-oms` (owner `767398067331`)
- Repository: `aptos-oms-nuget`
- Region: `us-east-1`
- V3 URL: see `config.json` → `codeArtifact.feedUrl`

Private package example: `EOM.Kernel.Infrastructure` 2.1.0

## For Cursor / new agent windows

Point the agent at this folder:

> Read `c:\PROD\ConnectorSuite\oms-nuget-aws-setup\README.md` and run `scripts\Setup-And-Restore.ps1` then `Build-OmsOdxSlice.ps1` before diagnosing OMS compile failures.

See also `CURSOR.md` in this folder.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `nuget was not found` during `codeartifact login` | Re-run any script here (downloads `tools\nuget.exe` and puts it on PATH) |
| `Unable to find package EOM.Kernel.Infrastructure` | Run `Login-CodeArtifact.ps1` then `Restore-OmsSolution.ps1` |
| Login expired | Re-run `Login-CodeArtifact.ps1` |
| MSBuild not found | Install VS Build Tools; verify `vswhere` exists |
| Wrong OMS path | Edit `config.json` → `omsRepoPath` |

## Security

- Treat `NugetAWS.env` like a password file.
- Prefer IAM user/role with least privilege for CodeArtifact read only.
- Rotate keys if this folder was copied to an insecure location.
