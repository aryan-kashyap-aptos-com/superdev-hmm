# Cursor agent: OMS local build

When the user asks to **build OMS**, **restore NuGet**, or **fix Harness compile** for the ODX feed monitor work:

1. Use this directory: `c:\PROD\ConnectorSuite\oms-nuget-aws-setup`
2. Credentials: `NugetAWS.env` in this folder (INI format, not committed if repo is ever under git)
3. Run in order:
   - `scripts\Setup-And-Restore.ps1` (login + restore)
   - `scripts\Build-OmsOdxSlice.ps1` (targeted MSBuild)
4. OMS source lives at `config.json` → `omsRepoPath` (default `c:\oms`)
5. Branch context for ODX monitor: `feature/akashyap/DCOMS-29203-odx-feed-pipeline-e2e`

Do not paste contents of `NugetAWS.env` into chat or commits.

Known compile pitfall (WebApi unit tests): `GetMessageTimeline` service signature requires `(messageId, startUtc, endUtc)` — mocks must match.
