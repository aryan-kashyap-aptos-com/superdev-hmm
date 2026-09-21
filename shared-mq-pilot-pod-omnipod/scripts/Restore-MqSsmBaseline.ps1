<#
.SYNOPSIS
  Restore MQ SSM parameters from a baseline JSON file (rollback).
.EXAMPLE
  .\Restore-MqSsmBaseline.ps1 -BaselineFile ..\baselines\ssm-mq-baseline-20260905.json -Environment pod/dev
  .\Restore-MqSsmBaseline.ps1 -BaselineFile ..\baselines\ssm-mq-baseline-20260905.json -Environment all
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BaselineFile,

    [ValidateSet('pod/dev', 'omnipod/qa', 'all')]
    [string]$Environment = 'all',

    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $BaselineFile)) {
    throw "Baseline file not found: $BaselineFile"
}

$data = Get-Content $BaselineFile -Raw | ConvertFrom-Json
if ($data -isnot [array]) { $data = @($data) }

function Set-SsmParam {
    param([string]$Name, [string]$Value, [switch]$Secure)
    if ($WhatIf) {
        Write-Host "[WhatIf] Would set $Name"
        return
    }
    if ($Secure) {
        aws ssm put-parameter --name $Name --value $Value --type SecureString --overwrite | Out-Null
    }
    else {
        aws ssm put-parameter --name $Name --value $Value --type String --overwrite | Out-Null
    }
    if ($LASTEXITCODE -ne 0) { throw "Failed to set $Name" }
    Write-Host "Updated $Name"
}

$secureKeys = @('applicationpassword', 'adminpassword')

foreach ($entry in $data) {
    $envKey = "$($entry.space)/$($entry.environment)"
    if ($Environment -ne 'all' -and $Environment -ne $envKey) { continue }

    Write-Host "`n=== Restoring $envKey ===" -ForegroundColor Cyan
    $prefix = $entry.ssmPrefix
    $params = $entry.parameters

    foreach ($prop in $params.PSObject.Properties) {
        $key = $prop.Name
        $val = [string]$prop.Value
        if ([string]::IsNullOrWhiteSpace($val)) { continue }
        Set-SsmParam -Name "$prefix/$key" -Value $val -Secure:($secureKeys -contains $key)
    }
}

Write-Host "`nDone. Force new ECS deployment on affected services (see runbooks/rollback-recovery.md)."
