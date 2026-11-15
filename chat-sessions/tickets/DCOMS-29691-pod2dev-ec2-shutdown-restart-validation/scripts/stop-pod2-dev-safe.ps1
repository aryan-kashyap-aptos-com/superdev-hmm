#Requires -Version 5.1
<#
.SYNOPSIS
  Safe off-hours shutdown for oms-pod2-dev: suspend ASG replacement, then STOP instances (no terminate).

.DESCRIPTION
  DCOMS-29691 — never scale ASG to 0. Preserves disks, IIS config, and instance IDs.

.EXAMPLE
  .\stop-pod2-dev-safe.ps1
  .\stop-pod2-dev-safe.ps1 -Confirm:$false
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Region = "us-east-1",
    [switch]$SkipAsgSuspend
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$StateFile = Join-Path $Root "test-results\safe-shutdown-state.json"
$AsgSettingsFile = Join-Path $Root "test-results\asg-settings-before-shutdown.json"

$Asgs = @(
    "oms-pod2-dev-sm-asg",
    "oms-pod2-dev-api-asg",
    "oms-pod2-dev-cnt-asg",
    "oms-pod2-dev-svc-asg",
    "oms-pod2-dev-toronado-asg"
)

$SuspendForShutdown = @("Launch", "ReplaceUnhealthy", "HealthCheck")

function Get-Pod2DevInstanceIds {
    $baselineFile = Join-Path $Root "baseline\captured-at.json"
    if (Test-Path $baselineFile) {
        $baseline = Get-Content $baselineFile -Raw | ConvertFrom-Json
        if ($baseline.instance_ids -and $baseline.instance_ids.Count -gt 0) {
            return @($baseline.instance_ids)
        }
    }
    $ids = aws ec2 describe-instances `
        --region $Region `
        --filters "Name=tag:Name,Values=oms-pod2-dev-*" `
        --query "Reservations[].Instances[].InstanceId" `
        --output text
    if ($LASTEXITCODE -ne 0) { throw "Failed to discover pod2-dev instances" }
    return @($ids -split "\s+" | Where-Object { $_ })
}

function Get-AsgSnapshot {
    param([string[]]$Names)
    $snap = @()
    foreach ($name in $Names) {
        $json = aws autoscaling describe-auto-scaling-groups `
            --auto-scaling-group-names $name `
            --region $Region `
            --output json | ConvertFrom-Json
        $g = $json.AutoScalingGroups[0]
        $suspended = @($g.SuspendedProcesses | ForEach-Object { $_.ProcessName })
        $snap += [PSCustomObject]@{
            name               = $g.AutoScalingGroupName
            min_size           = $g.MinSize
            max_size           = $g.MaxSize
            desired_capacity   = $g.DesiredCapacity
            suspended_before   = $suspended
            instances          = @($g.Instances | ForEach-Object { $_.InstanceId })
        }
    }
    return $snap
}

$env:AWS_DEFAULT_REGION = $Region

Write-Host "=== Safe shutdown: oms-pod2-dev (DCOMS-29691) ===" -ForegroundColor Cyan
Write-Host "Region: $Region"
aws sts get-caller-identity --output table

$instanceIds = Get-Pod2DevInstanceIds
Write-Host ""
Write-Host "Instances to STOP ($($instanceIds.Count)):"
foreach ($id in $instanceIds) {
    $info = aws ec2 describe-instances --instance-ids $id --region $Region `
        --query "Reservations[0].Instances[0].{Name:Tags[?Key=='Name']|[0].Value,State:State.Name}" --output json | ConvertFrom-Json
    Write-Host "  $id  $($info.Name)  [$($info.State)]"
}

if (-not $SkipAsgSuspend) {
    Write-Host ""
    Write-Host "Capturing ASG state before suspend..."
    $asgBefore = Get-AsgSnapshot -Names $Asgs

    if ($PSCmdlet.ShouldProcess("pod2-dev ASGs", "Suspend $($SuspendForShutdown -join ', ')")) {
        foreach ($name in $Asgs) {
            Write-Host "  Suspending on $name : $($SuspendForShutdown -join ', ')"
            aws autoscaling suspend-processes `
                --region $Region `
                --auto-scaling-group-name $name `
                --scaling-processes $SuspendForShutdown | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "suspend-processes failed for $name" }
        }
    }
} else {
    $asgBefore = Get-AsgSnapshot -Names $Asgs
}

$state = [PSCustomObject]@{
    action              = "safe-stop"
    captured_at_utc     = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    region              = $Region
    instance_ids        = $instanceIds
    asg_suspend_applied = $SuspendForShutdown
    asg_before          = $asgBefore
    asg_restore_file    = (Resolve-Path $AsgSettingsFile -ErrorAction SilentlyContinue).Path
}
$state | ConvertTo-Json -Depth 6 | Set-Content -Path $StateFile -Encoding UTF8
Write-Host ""
Write-Host "Wrote state: $StateFile"

if ($PSCmdlet.ShouldProcess($instanceIds -join ", ", "Stop EC2 instances")) {
    Write-Host ""
    Write-Host "Stopping instances..."
    aws ec2 stop-instances --region $Region --instance-ids $instanceIds | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "stop-instances failed" }
}

Write-Host ""
Write-Host "Waiting for instances to reach 'stopped'..."
$deadline = (Get-Date).AddMinutes(10)
do {
    $states = aws ec2 describe-instances --region $Region --instance-ids $instanceIds `
        --query "Reservations[].Instances[].{Id:InstanceId,State:State.Name}" --output json | ConvertFrom-Json
    $pending = @($states | Where-Object { $_.State -ne "stopped" })
    if ($pending.Count -eq 0) { break }
    Write-Host "  Still stopping: $($pending.Id -join ', ') ($($pending.State -join ', '))"
    if ((Get-Date) -gt $deadline) { throw "Timeout waiting for instances to stop" }
    Start-Sleep -Seconds 15
} while ($true)

Write-Host ""
Write-Host "Done. All instances stopped. Same instance IDs preserved." -ForegroundColor Green
Write-Host "Start with: .\start-pod2-dev-safe.ps1"
Write-Host "ALB targets will be unhealthy while stopped (expected)."
