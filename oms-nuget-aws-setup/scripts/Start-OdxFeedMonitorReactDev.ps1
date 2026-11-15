# ODX Feed Monitor UI — local dev with mock API (no svdev).
# Requires npm install in Shopvisible.Core.Shoplogic.Frontend.React once.
$ErrorActionPreference = 'Stop'
$setupRoot = Split-Path $PSScriptRoot -Parent
$config = Get-Content (Join-Path $setupRoot 'config.json') -Raw | ConvertFrom-Json
$reactRoot = Join-Path $config.omsRepoPath 'Shopvisible.Core.Shoplogic.Frontend.React'
$envExample = Join-Path $reactRoot '.env.development.local.example'
$envLocal = Join-Path $reactRoot '.env.development.local'
if (-not (Test-Path $envLocal) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envLocal
}
$env:BROWSER = 'none'
$env:REACT_APP_ODX_FEED_MONITOR_MOCK = 'true'
Push-Location $reactRoot
Write-Host 'Starting http://localhost:3000 (Node 18 via npx — Node 24 breaks react-scripts 1.x)'
npx -y node@18.20.4 node_modules\react-app-rewired\scripts\start.js
Pop-Location
