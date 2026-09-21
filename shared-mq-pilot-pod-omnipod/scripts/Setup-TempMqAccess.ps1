<#
.SYNOPSIS
  Ensure SSM bastion exists, validate MQ topology, print console access options.
#>
[CmdletBinding()]
param(
    [string]$ProfileName = 'temp-mq-admin',
    [string]$Region = 'us-east-1',
    [string]$BastionName = 'oms-shared-mq-bastion'
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$CredsFile = Join-Path $Root '.aws-temp-credentials'
$OutFile = Join-Path $Root 'baselines\temp-mq-provision-output.json'

if (-not (Test-Path $CredsFile)) { throw "Missing $CredsFile" }
if (-not (Test-Path $OutFile)) { throw "Missing $OutFile - run Provision-TempSharedMq.ps1 first" }

$env:AWS_SHARED_CREDENTIALS_FILE = $CredsFile
$env:AWS_PROFILE = $ProfileName
$env:AWS_DEFAULT_REGION = $Region

$cfg = Get-Content $OutFile -Raw | ConvertFrom-Json
$mqHost = $cfg.endpoint
$consoleUrl = $cfg.consoleUrl
$adminUser = $cfg.adminUser
$adminPass = $cfg.adminPassword
$vpcId = $cfg.vpcId
$subnetId = $cfg.subnetId

function Invoke-Aws {
    param([string[]]$AwsArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $raw = & aws --profile $ProfileName --region $Region @AwsArgs 2>&1 }
    finally { $ErrorActionPreference = $prev }
    if ($LASTEXITCODE -ne 0) {
        throw (($raw | ForEach-Object { if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { "$_" } }) -join "`n")
    }
    if ($raw -is [array]) { return ($raw | ForEach-Object { "$_" }) -join "`n" }
    return [string]$raw
}

function Wait-SsmOnline {
    param([string]$InstanceId)
    $deadline = (Get-Date).AddMinutes(10)
    do {
        $info = Invoke-Aws @('ssm', 'describe-instance-information', '--filters', "Key=InstanceIds,Values=$InstanceId", '--output', 'json') | ConvertFrom-Json
        if ($info.InstanceInformationList.Count -gt 0 -and $info.InstanceInformationList[0].PingStatus -eq 'Online') {
            Write-Host "  SSM Online: $InstanceId"
            return
        }
        Write-Host "  Waiting for SSM agent..."
        Start-Sleep -Seconds 15
    } while ((Get-Date) -lt $deadline)
    throw "SSM did not come online for $InstanceId"
}

function Invoke-SsmShell {
    param([string]$InstanceId, [string]$Script, [string]$Comment)
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Script))
    $commands = @("echo $b64 | base64 -d | bash")
    $payload = ($commands | ConvertTo-Json -Compress)
    $cmdId = Invoke-Aws @(
        'ssm', 'send-command',
        '--instance-ids', $InstanceId,
        '--document-name', 'AWS-RunShellScript',
        '--comment', $Comment,
        '--parameters', "commands=$payload",
        '--query', 'Command.CommandId', '--output', 'text'
    )
    $deadline = (Get-Date).AddMinutes(3)
    do {
        Start-Sleep -Seconds 3
        $inv = Invoke-Aws @('ssm', 'get-command-invocation', '--command-id', $cmdId, '--instance-id', $InstanceId, '--output', 'json') | ConvertFrom-Json
    } while ($inv.Status -in @('Pending', 'InProgress', 'Delayed') -and (Get-Date) -lt $deadline)
    if ($inv.Status -ne 'Success') {
        throw "SSM failed: $($inv.StandardErrorContent)"
    }
    return $inv.StandardOutputContent
}

Write-Host "=== Step 1: Bastion (SSM) ===" -ForegroundColor Green
$existing = Invoke-Aws @(
    'ec2', 'describe-instances',
    '--filters', "Name=tag:Name,Values=$BastionName", 'Name=instance-state-name,Values=running,pending',
    '--query', 'Reservations[0].Instances[0].InstanceId', '--output', 'text'
)
if ($existing -and $existing -ne 'None') {
    $bastionId = $existing.Trim()
    Write-Host "Reusing bastion: $bastionId"
}
else {
    $defaultSg = Invoke-Aws @('ec2', 'describe-security-groups', '--filters', "Name=vpc-id,Values=$vpcId", 'Name=group-name,Values=default', '--query', 'SecurityGroups[0].GroupId', '--output', 'text')
    $ami = Invoke-Aws @('ssm', 'get-parameters', '--names', '/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64', '--query', 'Parameters[0].Value', '--output', 'text')
    Write-Host "Launching bastion ($ami) in $subnetId..."
    $bastionId = Invoke-Aws @(
        'ec2', 'run-instances',
        '--image-id', $ami.Trim(),
        '--instance-type', 't3.micro',
        '--subnet-id', $subnetId,
        '--iam-instance-profile', 'Name=EC2-SSM-Profile',
        '--security-group-ids', $defaultSg.Trim(),
        '--tag-specifications', 'ResourceType=instance,Tags=[{Key=Name,Value=oms-shared-mq-bastion}]',
        '--query', 'Instances[0].InstanceId', '--output', 'text'
    )
    Write-Host "Created bastion: $bastionId"
}

Wait-SsmOnline -InstanceId $bastionId

Write-Host "`n=== Step 2: Validate topology from bastion ===" -ForegroundColor Green
$vhostChecks = ($cfg.vhosts | ForEach-Object { $_.vhost }) -join ' '
$validateScript = @"
set -euo pipefail
BASE='https://$mqHost/api'
U='$adminUser'
P='$adminPass'
check_vhost() {
  local VH="`$1"
  curl -fsS -u "`${U}:`${P}" "`${BASE}/queues/`${VH}" | grep -q export_requested && echo "OK queues `$VH" || { echo "FAIL `$VH"; exit 1; }
  curl -fsS -u "`${U}:`${P}" "`${BASE}/exchanges/`${VH}/main_exchange" | grep -q main_exchange && echo "OK exchange `$VH"
}
for v in $vhostChecks; do check_vhost "`$v"; done
curl -fsS -u "`${U}:`${P}" "`${BASE}/overview" | head -c 120
echo
echo VALIDATION_OK
"@
$valOut = Invoke-SsmShell -InstanceId $bastionId -Script $validateScript -Comment 'validate temp shared mq'
Write-Host $valOut

Write-Host "`n=== Step 3: Access options ===" -ForegroundColor Green
$awsConsole = "https://$Region.console.aws.amazon.com/amazon-mq/home?region=$Region#/brokers/details?id=$($cfg.brokerId)"
Write-Host @"

1) AWS Console (often works on corporate VPN):
   $awsConsole
   Click 'RabbitMQ web console' on the broker page.

2) SSM port forward (if direct MQ URL is blocked):
   .\Open-TempMqConsole.ps1
   Then open: https://localhost:8443
   Login: $adminUser / (password in temp-mq-provision-output.json)
   Accept the certificate warning (cert is for $mqHost, not localhost).

3) Direct URL (if your network allows):
   $consoleUrl

Bastion instance: $bastionId
"@

$cfg | Add-Member -NotePropertyName bastionInstanceId -NotePropertyValue $bastionId -Force
$cfg | Add-Member -NotePropertyName awsConsoleBrokerUrl -NotePropertyValue $awsConsole -Force
$cfg | Add-Member -NotePropertyName localPortForwardUrl -NotePropertyValue 'https://localhost:8443' -Force
$cfg | ConvertTo-Json -Depth 6 | Set-Content $OutFile -Encoding UTF8
Write-Host "Updated $OutFile"
