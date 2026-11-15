#Requires -Version 5.1
<#
.SYNOPSIS
  Collect oms-pod2-dev baseline and backup details via AWS CLI for DCOMS-29691.

.PARAMETER OutputDir
  Directory for JSON output. Defaults to ../baseline relative to this script.

.PARAMETER IncludeTargetHealth
  Also fetch ELB target group health status.
#>
param(
    [string]$OutputDir = (Join-Path $PSScriptRoot "..\baseline"),
    [switch]$IncludeTargetHealth
)

$ErrorActionPreference = "Stop"
$Region = "us-east-1"
$ClusterId = "oms-pod2-dev-aurora"
$Route53ZoneId = "Z03009582CVKQO0JAKTL1"

# Discover current pod2-dev instances (post-ASG-restore safe — no hardcoded IDs)
$InstanceIds = @(
    aws ec2 describe-instances `
        --region $Region `
        --filters "Name=tag:Name,Values=oms-pod2-dev-*" `
        --query "Reservations[].Instances[].InstanceId" `
        --output text
) -split "\s+" | Where-Object { $_ }

if ($InstanceIds.Count -eq 0) {
    throw "No oms-pod2-dev-* instances found in $Region"
}
Write-Host "Instances ($($InstanceIds.Count)): $($InstanceIds -join ', ')"

function Save-AwsJson {
    param([string]$FileName, [scriptblock]$Command)
    $path = Join-Path $OutputDir $FileName
    Write-Host "Fetching $FileName ..."
    $result = & $Command
    if ($LASTEXITCODE -ne 0) { throw "AWS CLI failed for $FileName" }
    $result | Set-Content -Path $path -Encoding UTF8
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$env:AWS_DEFAULT_REGION = $Region

Write-Host "AWS identity:"
aws sts get-caller-identity

Save-AwsJson "ec2-instances-full.json" {
    aws ec2 describe-instances --instance-ids $InstanceIds --output json
}

Save-AwsJson "ec2-instances-summary.json" {
    aws ec2 describe-instances --instance-ids $InstanceIds --query "Reservations[].Instances[].{InstanceId:InstanceId,Name:Tags[?Key=='Name']|[0].Value,State:State.Name,Type:InstanceType,PrivateIp:PrivateIpAddress,PublicIp:PublicIpAddress,AZ:Placement.AvailabilityZone,SubnetId:SubnetId,VpcId:VpcId,ImageId:ImageId,KeyName:KeyName,LaunchTime:LaunchTime,IamInstanceProfile:IamInstanceProfile.Arn}" --output json
}

Save-AwsJson "ebs-volumes.json" {
    $volFilter = "Name=attachment.instance-id,Values=$($InstanceIds -join ',')"
    aws ec2 describe-volumes --filters $volFilter --query "Volumes[].{VolumeId:VolumeId,InstanceId:Attachments[0].InstanceId,Device:Attachments[0].Device,Size:Size,Type:VolumeType,Encrypted:Encrypted,State:State,Iops:Iops,SnapshotId:SnapshotId,DeleteOnTermination:Attachments[0].DeleteOnTermination,AZ:AvailabilityZone,Tags:Tags}" --output json
}

Save-AwsJson "ebs-volumes-orphaned.json" {
    aws ec2 describe-volumes --filters "Name=status,Values=available" --query "Volumes[].{VolumeId:VolumeId,Size:Size,State:State,SnapshotId:SnapshotId,AZ:AvailabilityZone,Tags:Tags}" --output json
}

Save-AwsJson "asg-settings.json" {
    $asgNames = @(
        "oms-pod2-dev-sm-asg",
        "oms-pod2-dev-api-asg",
        "oms-pod2-dev-cnt-asg",
        "oms-pod2-dev-svc-asg",
        "oms-pod2-dev-toronado-asg"
    )
    $groups = foreach ($n in $asgNames) {
        aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names $n --output json | ConvertFrom-Json
    }
    $groups | ConvertTo-Json -Depth 20
}

Save-AwsJson "rds-cluster.json" {
    aws rds describe-db-clusters --db-cluster-identifier $ClusterId --output json
}

Save-AwsJson "rds-cluster-snapshots.json" {
    aws rds describe-db-cluster-snapshots --db-cluster-identifier $ClusterId --query "DBClusterSnapshots[].{Id:DBClusterSnapshotIdentifier,Type:SnapshotType,Status:Status,Created:SnapshotCreateTime,Engine:Engine,AllocatedStorage:AllocatedStorage,Encrypted:StorageEncrypted}" --output json
}

Save-AwsJson "rds-automated-backups.json" {
    aws rds describe-db-cluster-automated-backups --db-cluster-identifier $ClusterId --output json
}

Save-AwsJson "elastic-ips.json" {
    aws ec2 describe-addresses --filters "Name=tag:Space,Values=pod2" --output json
}

Save-AwsJson "load-balancers.json" {
    aws elbv2 describe-load-balancers --query "LoadBalancers[?contains(LoadBalancerName, 'pod2')].{Name:LoadBalancerName,ARN:LoadBalancerArn,DNS:DNSName,Scheme:Scheme,Type:Type,State:State.Code}" --output json
}

Save-AwsJson "target-groups.json" {
    aws elbv2 describe-target-groups --query "TargetGroups[?contains(TargetGroupName, 'pod2')].{Name:TargetGroupName,ARN:TargetGroupArn,Port:Port,Protocol:Protocol,TargetType:TargetType,HealthCheckPath:HealthCheckPath}" --output json
}

Save-AwsJson "aws-backup-vaults.json" {
    aws backup list-backup-vaults --output json
}

Save-AwsJson "route53-oms-pod2-dev-local.json" {
    aws route53 list-resource-record-sets --hosted-zone-id $Route53ZoneId --output json
}

# AMIs used by pod2-dev instances
$imageIds = (aws ec2 describe-instances --instance-ids $InstanceIds --query "Reservations[].Instances[].ImageId" --output text) -split "\s+"
$uniqueImages = $imageIds | Select-Object -Unique
Save-AwsJson "amis.json" {
    aws ec2 describe-images --image-ids $uniqueImages --output json
}

if ($IncludeTargetHealth) {
    $tgArns = (aws elbv2 describe-target-groups --query "TargetGroups[?contains(TargetGroupName, 'pod2')].TargetGroupArn" --output text) -split "\s+"
    $healthResults = @()
    foreach ($arn in $tgArns) {
        $health = aws elbv2 describe-target-health --target-group-arn $arn --output json | ConvertFrom-Json
        $healthResults += [PSCustomObject]@{
            TargetGroupArn = $arn
            TargetHealthDescriptions = $health.TargetHealthDescriptions
        }
    }
    $healthResults | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $OutputDir "target-group-health.json") -Encoding UTF8
    Write-Host "Wrote target-group-health.json"
}

$capturedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
@{
    captured_at_utc = $capturedAt
    region          = $Region
    account         = (aws sts get-caller-identity --query Account --output text)
    instance_ids    = $InstanceIds
    note            = "Post-recovery baseline after terminate + App-Deploy + DFS (DCOMS-29691)"
} | ConvertTo-Json | Set-Content (Join-Path $OutputDir "captured-at.json") -Encoding UTF8

Write-Host ""
Write-Host "Baseline collection complete. Output: $OutputDir"
Write-Host "Captured: $capturedAt"
Write-Host "Review baseline/backup-summary.md for interpretation."
