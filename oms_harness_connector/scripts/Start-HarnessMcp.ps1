# Starts Harness official MCP server (stdio) for Cursor.
# Loads secrets from ..\..\.env (oms_harness_connector\.env).

$ErrorActionPreference = 'Stop'
$ConnectorRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ConnectorRoot '.env'

function Import-DotEnv([string] $Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing $Path - copy .env.example to .env and set HARNESS_API_KEY."
    }
    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { return }
        $eq = $line.IndexOf('=')
        if ($eq -lt 1) { return }
        $name = $line.Substring(0, $eq).Trim()
        $value = $line.Substring($eq + 1).Trim()
        if ($name) { Set-Item -Path "Env:$name" -Value $value }
    }
}

Import-DotEnv $EnvFile

if (-not $env:HARNESS_API_KEY) {
    throw 'HARNESS_API_KEY is empty in .env'
}

$NodeDir = 'C:\Program Files\nodejs'
if (-not (Test-Path -LiteralPath "$NodeDir\npx.cmd")) {
    throw "npx not found at $NodeDir\npx.cmd - install Node.js or edit Start-HarnessMcp.ps1"
}

$env:PATH = "$NodeDir;$env:PATH"

# Prefer Node launcher for Cursor MCP (stdio); this script is for manual terminal smoke tests.
& "$NodeDir\node.exe" (Join-Path $ConnectorRoot 'run-harness-mcp.js')
