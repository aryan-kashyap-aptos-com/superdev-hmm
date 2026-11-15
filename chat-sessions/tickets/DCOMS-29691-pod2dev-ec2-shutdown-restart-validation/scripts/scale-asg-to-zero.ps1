#Requires -Version 5.1
<#
.SYNOPSIS
  Scale all pod2-dev ASGs to 0 for off-hours shutdown (DCOMS-29691).
#>
$ErrorActionPreference = "Stop"
$asgs = @(
    "oms-pod2-dev-sm-asg",
    "oms-pod2-dev-api-asg",
    "oms-pod2-dev-cnt-asg",
    "oms-pod2-dev-svc-asg",
    "oms-pod2-dev-toronado-asg"
)

foreach ($name in $asgs) {
    Write-Host "Scaling $name to 0..."
    aws autoscaling update-auto-scaling-group `
        --auto-scaling-group-name $name `
        --min-size 0 `
        --max-size 0 `
        --desired-capacity 0
}

Write-Host "Done. ASG instances will terminate; standalone EC2 already stopped separately."
