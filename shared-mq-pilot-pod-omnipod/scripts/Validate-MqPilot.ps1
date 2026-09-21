<#
.SYNOPSIS
  Validate MQ SSM endpoints and ECS MQ-related service counts for pilot environments.
.EXAMPLE
  .\Validate-MqPilot.ps1
  .\Validate-MqPilot.ps1 -Environment pod/dev
  .\Validate-MqPilot.ps1 -ExpectStandalone
#>
[CmdletBinding()]
param(
    [ValidateSet('pod/dev', 'omnipod/qa', 'all')]
    [string]$Environment = 'all',

    [switch]$ExpectStandalone,

    [string]$SharedEndpoint = 'b-5d413804-aec7-4af1-9a26-1de2f913f107.mq.us-east-1.on.aws'
)

$ErrorActionPreference = 'Continue'

$expectedStandalone = @{
    'pod/dev'     = 'b-e93a05aa-377d-441c-8e35-5b862ff6b9cd.mq.us-east-1.on.aws'
    'omnipod/qa'  = 'b-aa4f9294-525c-4c56-bdec-16dc30e652ee.mq.us-east-1.on.aws'
}

$expectedSharedVhost = @{
    'pod/dev'    = 'pod-dev'
    'omnipod/qa' = 'omnipod-qa'
}

$clusters = @{
    'pod/dev'    = 'oms-pod-dev-ecs-cluster'
    'omnipod/qa' = 'oms-omnipod-qa-ecs-cluster'
}

$mqServicePattern = 'feed|taskprocessor|scheduler|inventory'

$envs = if ($Environment -eq 'all') { @('pod/dev', 'omnipod/qa') } else { @($Environment) }

foreach ($envPath in $envs) {
    $parts = $envPath.Split('/')
    $prefix = "/oms/$($parts[0])/$($parts[1])/aws-mq-broker"

    Write-Host "`n=== $envPath ===" -ForegroundColor Cyan

    $endpoint = aws ssm get-parameter --name "$prefix/endpoint" --query 'Parameter.Value' --output text 2>$null
    $vhost = aws ssm get-parameter --name "$prefix/virtualhost" --query 'Parameter.Value' --output text 2>$null

    Write-Host "SSM endpoint:  $endpoint"
    Write-Host "SSM vhost:     $vhost"

    if ($ExpectStandalone) {
        $exp = $expectedStandalone[$envPath]
        if ($endpoint -eq $exp -and $vhost -eq '/') {
            Write-Host "OK: Standalone rollback endpoint" -ForegroundColor Green
        }
        else {
            Write-Host "WARN: Expected standalone $exp with vhost /" -ForegroundColor Yellow
        }
    }
    else {
        if ($endpoint -eq $SharedEndpoint) {
            Write-Host "OK: Points to shared broker" -ForegroundColor Green
        }
        else {
            Write-Host "INFO: Not on shared broker yet (or partial cutover)" -ForegroundColor Yellow
        }
        $expVh = $expectedSharedVhost[$envPath]
        if ($vhost -eq $expVh) {
            Write-Host "OK: Expected pilot vhost $expVh" -ForegroundColor Green
        }
    }

    $cluster = $clusters[$envPath]
    $arns = aws ecs list-services --cluster $cluster --query 'serviceArns' --output json 2>$null | ConvertFrom-Json
    if ($arns) {
        foreach ($arn in $arns) {
            $name = $arn.Split('/')[-1]
            if ($name -match $mqServicePattern) {
                $d = aws ecs describe-services --cluster $cluster --services $name `
                    --query 'services[0].{running:runningCount,desired:desiredCount}' --output json 2>$null | ConvertFrom-Json
                $status = if ($d.running -eq $d.desired -and $d.desired -gt 0) { 'OK' } else { 'CHECK' }
                $color = if ($status -eq 'OK') { 'Green' } else { 'Yellow' }
                Write-Host "ECS $name : running=$($d.running) desired=$($d.desired) [$status]" -ForegroundColor $color
            }
        }
    }
}

Write-Host "`nShared broker state:"
aws mq describe-broker --broker-id b-5d413804-aec7-4af1-9a26-1de2f913f107 `
    --query '{Name:BrokerName,State:BrokerState,Type:HostInstanceType}' --output table 2>$null
