#Requires -Version 5.1
<#
.SYNOPSIS
  Safe startup for oms-pod2-dev after stop-pod2-dev-safe.ps1 (same instance IDs, no pipelines).

.EXAMPLE
  .\start-pod2-dev-safe.ps1
  .\start-pod2-dev-safe.ps1 -WaitMinutes 15
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Region = "us-east-1",
    [int]$WaitMinutes = 10
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$StateFile = Join-Path $Root "test-results\safe-shutdown-state.json"
$AsgSettingsFile = Join-Path $Root "test-results\asg-settings-before-shutdown.json"

$env:AWS_DEFAULT_REGION = $Region

Write-Host "=== Safe startup: oms-pod2-dev (DCOMS-29691) ===" -ForegroundColor Cyan

if (-not (Test-Path $StateFile)) {
    throw "Missing $StateFile - run .\stop-pod2-dev-safe.ps1 first, or pass instance IDs manually."
}

$state = Get-Content $StateFile -Raw | ConvertFrom-Json
$instanceIds = @($state.instance_ids)
if ($instanceIds.Count -eq 0) { throw "No instance_ids in safe-shutdown-state.json" }

Write-Host "Shutdown was: $($state.captured_at_utc)"
Write-Host "Instances to START ($($instanceIds.Count)): $($instanceIds -join ', ')"

if ($PSCmdlet.ShouldProcess($instanceIds -join ", ", "Start EC2 instances")) {
    aws ec2 start-instances --region $Region --instance-ids $instanceIds | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "start-instances failed" }
}

Write-Host ""
Write-Host "Waiting for 'running' (up to $WaitMinutes min)..."
$deadline = (Get-Date).AddMinutes($WaitMinutes)
do {
    $states = aws ec2 describe-instances --region $Region --instance-ids $instanceIds `
        --query "Reservations[].Instances[].{Id:InstanceId,Name:Tags[?Key=='Name']|[0].Value,State:State.Name}" --output json | ConvertFrom-Json
    $notRunning = @($states | Where-Object { $_.State -ne "running" })
    foreach ($s in $states) {
        Write-Host "  $($s.Id) $($s.Name) [$($s.State)]"
    }
    if ($notRunning.Count -eq 0) { break }
    if ((Get-Date) -gt $deadline) {
        Write-Warning "Timeout - some instances not running yet. Continue manually."
        break
    }
    Start-Sleep -Seconds 20
} while ($true)

if (-not (Test-Path $AsgSettingsFile)) {
    Write-Warning "Missing $AsgSettingsFile - skipping ASG process restore."
} elseif ($PSCmdlet.ShouldProcess("pod2-dev ASGs", "Restore normal suspended processes")) {
    Write-Host ""
    Write-Host "Restoring ASG suspended-processes (normal pod2-dev state)..."
    $settings = Get-Content $AsgSettingsFile -Raw | ConvertFrom-Json

    foreach ($asg in $settings.auto_scaling_groups) {
        Write-Host "  $($asg.name)"
        aws autoscaling resume-processes --region $Region --auto-scaling-group-name $asg.name | Out-Null
        if ($asg.suspended_processes.Count -gt 0) {
            $procArgs = @()
            foreach ($p in $asg.suspended_processes) {
                $procArgs += "--scaling-processes"
                $procArgs += $p
            }
            & aws autoscaling suspend-processes --region $Region --auto-scaling-group-name $asg.name @procArgs
            if ($LASTEXITCODE -ne 0) { throw "suspend-processes failed for $($asg.name)" }
            Write-Host "    suspended: $($asg.suspended_processes -join ', ')"
        } else {
            Write-Host "    suspended: (none)"
        }
    }
}

Write-Host ""
Write-Host "Done. Verify SM login (no App-Deploy / DFS needed if stop-only was used)." -ForegroundColor Green
Write-Host "  https://oms-pod2-dev-sm.dev.eom.aptos.io/backadmin/login.aspx"
Write-Host ""
Write-Host "Optional health check:"
Write-Host "  cd C:\PROD\ConnectorSuite\oms_ec2_connector"
Write-Host '  python oms_ec2.py --env .env.pod2dev exec sitemanager "Get-Service OMS-*"'
