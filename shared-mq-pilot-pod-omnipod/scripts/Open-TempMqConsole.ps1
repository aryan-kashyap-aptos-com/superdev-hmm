<#
.SYNOPSIS
  Port-forward RabbitMQ console (443) to localhost:8443 via SSM bastion.
  Requires: AWS CLI + Session Manager plugin installed.
  Keep this window open while using the browser.
#>
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$CredsFile = Join-Path $Root '.aws-temp-credentials'
$OutFile = Join-Path $Root 'baselines\temp-mq-provision-output.json'
$ProfileName = 'temp-mq-admin'
$Region = 'us-east-1'
$LocalPort = 8443

if (-not (Test-Path $OutFile)) { throw "Run Provision-TempSharedMq.ps1 and Setup-TempMqAccess.ps1 first." }
$cfg = Get-Content $OutFile -Raw | ConvertFrom-Json
$bastionId = $cfg.bastionInstanceId
if (-not $bastionId) {
    Write-Host "No bastionInstanceId - running Setup-TempMqAccess.ps1 first..." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot 'Setup-TempMqAccess.ps1')
    $cfg = Get-Content $OutFile -Raw | ConvertFrom-Json
    $bastionId = $cfg.bastionInstanceId
}

$env:AWS_SHARED_CREDENTIALS_FILE = $CredsFile
$env:AWS_PROFILE = $ProfileName
$env:AWS_DEFAULT_REGION = $Region

Write-Host "Forwarding localhost:$LocalPort -> $($cfg.endpoint):443 via bastion $bastionId"
Write-Host "Open: https://localhost:$LocalPort"
Write-Host "User: $($cfg.adminUser)  Password: see temp-mq-provision-output.json"
Write-Host "Press Ctrl+C to stop.`n" -ForegroundColor Yellow

aws ssm start-session `
    --target $bastionId `
    --document-name AWS-StartPortForwardingSessionToRemoteHost `
    --parameters "host=$($cfg.endpoint),portNumber=443,localPortNumber=$LocalPort"
