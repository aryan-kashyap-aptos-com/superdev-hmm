#Requires -Version 5.1
<#
.SYNOPSIS
  Restore pod2-dev ASG capacity after off-hours shutdown (DCOMS-29691).
  Settings captured in test-results/asg-settings-before-shutdown.json
#>
$ErrorActionPreference = "Stop"
$settings = Get-Content (Join-Path $PSScriptRoot "..\test-results\asg-settings-before-shutdown.json") | ConvertFrom-Json

Write-Host "Restoring ASG capacity..."
foreach ($asg in $settings.auto_scaling_groups) {
    Write-Host "  $($asg.name) -> min=$($asg.min_size) max=$($asg.max_size) desired=$($asg.desired_capacity)"
    aws autoscaling update-auto-scaling-group `
        --auto-scaling-group-name $asg.name `
        --min-size $asg.min_size `
        --max-size $asg.max_size `
        --desired-capacity $asg.desired_capacity
    if ($asg.suspended_processes.Count -gt 0) {
        $procArgs = $asg.suspended_processes | ForEach-Object { @("--scaling-processes", $_) }
        & aws autoscaling suspend-processes --auto-scaling-group-name $asg.name @procArgs
    }
}

Write-Host "Starting standalone EC2 (bastion + migration host)..."
foreach ($ec2 in $settings.standalone_ec2) {
    Write-Host "  $($ec2.name) ($($ec2.instance_id))"
    aws ec2 start-instances --instance-ids $ec2.instance_id | Out-Null
}

Write-Host "Done. Wait for instances to boot, then verify ALB health checks."
