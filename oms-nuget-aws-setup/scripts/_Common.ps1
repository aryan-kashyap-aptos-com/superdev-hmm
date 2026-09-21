# Shared helpers for OMS NuGet + AWS CodeArtifact setup.
$ErrorActionPreference = 'Stop'

function Get-OmsNuGetSetupRoot {
    $root = Split-Path -Parent $PSScriptRoot
    if (-not (Test-Path (Join-Path $root 'config.json'))) {
        throw "config.json not found. Expected setup root: $root"
    }
    return $root
}

function Get-OmsNuGetConfig {
    $root = Get-OmsNuGetSetupRoot
    $configPath = Join-Path $root 'config.json'
    return Get-Content $configPath -Raw | ConvertFrom-Json
}

function Import-NugetAwsEnv {
    param(
        [string] $EnvFile
    )

    if (-not (Test-Path $EnvFile)) {
        throw "AWS env file not found: $EnvFile. Copy NugetAWS.env.example to NugetAWS.env and fill in keys."
    }

    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -match '^\s*;\s*' -or $line -match '^\s*#' -or $line -eq '') { return }
        if ($line -match '^\s*aws_access_key_id\s*=\s*(.+)$') {
            $env:AWS_ACCESS_KEY_ID = $matches[1].Trim()
        }
        if ($line -match '^\s*aws_secret_access_key\s*=\s*(.+)$') {
            $env:AWS_SECRET_ACCESS_KEY = $matches[1].Trim()
        }
        if ($line -match '^\s*region\s*=\s*(.+)$') {
            $env:AWS_DEFAULT_REGION = $matches[1].Trim()
        }
    }

    if (-not $env:AWS_ACCESS_KEY_ID -or -not $env:AWS_SECRET_ACCESS_KEY) {
        throw 'NugetAWS.env must set aws_access_key_id and aws_secret_access_key.'
    }
}

function Get-NuGetExe {
    param(
        [string] $SetupRoot
    )

    $localNuget = Join-Path $SetupRoot 'tools\nuget.exe'
    if (Test-Path $localNuget) {
        return $localNuget
    }

    $omsTools = Join-Path (Get-OmsNuGetConfig).omsRepoPath '.tools\nuget.exe'
    if (Test-Path $omsTools) {
        return $omsTools
    }

    $toolsDir = Join-Path $SetupRoot 'tools'
    New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
    Write-Host "Downloading nuget.exe to $localNuget ..."
    Invoke-WebRequest -Uri 'https://dist.nuget.org/win-x86-commandline/latest/nuget.exe' -OutFile $localNuget
    return $localNuget
}

function Get-MsBuildExe {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path $vswhere)) {
        throw 'vswhere not found. Install Visual Studio with MSBuild.'
    }
    $msbuild = & $vswhere -latest -requires Microsoft.Component.MSBuild -find 'MSBuild\**\Bin\MSBuild.exe' | Select-Object -First 1
    if (-not $msbuild) {
        throw 'MSBuild.exe not found via vswhere.'
    }
    return $msbuild
}
