<#
.SYNOPSIS
  Export MQ-related SSM parameters for pilot environments to a dated baseline JSON file.
.EXAMPLE
  .\Export-MqSsmBaseline.ps1
  .\Export-MqSsmBaseline.ps1 -OutputDir ..\baselines
#>
[CmdletBinding()]
param(
    [string]$OutputDir = (Join-Path $PSScriptRoot '..\baselines'),
    [string[]]$Environments = @('pod/dev', 'omnipod/qa')
)

$ErrorActionPreference = 'Stop'
$keys = @(
    'endpoint', 'virtualhost', 'applicationusername', 'applicationpassword',
    'adminusername', 'adminpassword', 'port', 'scheme', 'sslenabled',
    'sslprotocols', 'webconsole-endpoint'
)

$baseline = foreach ($envPath in $Environments) {
    $parts = $envPath.Split('/')
    $space = $parts[0]
    $environment = $parts[1]
    $prefix = "/oms/$space/$environment/aws-mq-broker"
    $parameters = @{}

    foreach ($k in $keys) {
        try {
            $json = aws ssm get-parameter --name "$prefix/$k" --with-decryption --output json 2>$null
            if ($LASTEXITCODE -eq 0 -and $json) {
                $parameters[$k] = ($json | ConvertFrom-Json).Parameter.Value
            }
        }
        catch {
            Write-Warning "Missing parameter: $prefix/$k"
        }
    }

    $cluster = switch ($envPath) {
        'pod/dev' { 'oms-pod-dev-ecs-cluster' }
        'omnipod/qa' { 'oms-omnipod-qa-ecs-cluster' }
        default { $null }
    }

    [pscustomobject]@{
        ssmPrefix   = $prefix
        space       = $space
        environment = $environment
        ecsCluster  = $cluster
        parameters  = $parameters
        exportedAtUtc = (Get-Date).ToUniversalTime().ToString('o')
    }
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$dateStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outFile = Join-Path $OutputDir "ssm-mq-baseline-$dateStamp.json"
$baseline | ConvertTo-Json -Depth 6 | Set-Content $outFile -Encoding UTF8

# Also refresh canonical baseline name for scripts
$canonical = Join-Path $OutputDir 'ssm-mq-baseline-20260905.json'
Copy-Item $outFile $canonical -Force

aws mq list-brokers --max-results 100 --output json | Set-Content (Join-Path $OutputDir 'amazon-mq-brokers-list.json') -Encoding UTF8

Write-Host "Exported baseline: $outFile"
Write-Host "Canonical copy:   $canonical"
Write-Host "WARNING: File contains decrypted passwords. Do not commit to git."
