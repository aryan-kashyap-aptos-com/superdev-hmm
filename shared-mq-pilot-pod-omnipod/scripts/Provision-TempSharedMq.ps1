<#
.SYNOPSIS
  Provision shared Amazon MQ (RabbitMQ) in temp AWS account with pilot topology.
#>
[CmdletBinding()]
param(
    [string]$ProfileName = 'temp-mq-admin',
    [string]$Region = 'us-east-1',
    [string]$BrokerName = 'oms-shared-dev-mq-broker',
    [string]$VpcId = '',
    [string]$SubnetId = ''
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$CredsFile = Join-Path $Root '.aws-temp-credentials'
$OutFile = Join-Path $Root 'baselines\temp-mq-provision-output.json'

$Queues = @(
    'export_requested', 'inventory_requested', 'taskprocessing_requested',
    'taskprocessing_status', 'eom_atp_service_queue', 'eom_inventory_service_queue'
)

$Vhosts = @(
    @{ Name = 'pod-dev'; User = 'pod-dev-app' }
    @{ Name = 'omnipod-qa'; User = 'omnipod-qa-app' }
)

function Invoke-Aws {
    param([string[]]$AwsArgs)
    $all = @('--profile', $ProfileName, '--region', $Region) + $AwsArgs
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $raw = & aws @all 2>&1
    }
    finally {
        $ErrorActionPreference = $prevEap
    }
    if ($LASTEXITCODE -ne 0) {
        $msg = ($raw | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.Exception.Message + ' ' + $_.ToString() }
            else { "$_" }
        }) -join "`n"
        throw "aws $($AwsArgs -join ' ') failed:`n$msg"
    }
    if ($raw -is [array]) { return ($raw | ForEach-Object { "$_" }) -join "`n" }
    return [string]$raw
}

function New-RandomPassword {
    param([int]$Length = 24)
    -join ((65..90) + (97..122) + (48..57) | Get-Random -Count $Length | ForEach-Object { [char]$_ })
}

function Wait-MqBroker {
    param([string]$BrokerId)
    $deadline = (Get-Date).AddMinutes(25)
    do {
        $state = Invoke-Aws @('mq', 'describe-broker', '--broker-id', $BrokerId, '--query', 'BrokerState', '--output', 'text')
        Write-Host "  Broker state: $state"
        if ($state -eq 'RUNNING') { return }
        if ($state -in @('DELETION_IN_PROGRESS', 'REBOOT_IN_PROGRESS')) {
            Start-Sleep -Seconds 15
            continue
        }
        Start-Sleep -Seconds 20
    } while ((Get-Date) -lt $deadline)
    throw "Broker did not reach RUNNING within timeout"
}

function Invoke-RmqApi {
    param(
        [string]$BaseUrl,
        [string]$Method,
        [string]$Path,
        [string]$AdminUser,
        [string]$AdminPass,
        [string]$Body = $null
    )
    $uri = "$BaseUrl/api$Path"
    $pair = '{0}:{1}' -f $AdminUser, $AdminPass
    $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
    $params = @{
        Uri     = $uri
        Method  = $Method
        Headers = @{ Authorization = "Basic $b64" }
    }
    if ($Body) {
        $params.ContentType = 'application/json'
        $params.Body = $Body
    }
    try {
        Invoke-RestMethod @params
    }
    catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code -eq 204) { return $null }
        throw "RabbitMQ API $Method $Path failed: $_"
    }
}

if (-not (Test-Path $CredsFile)) {
    throw "Missing credentials file: $CredsFile (create from temp account session)"
}

$env:AWS_SHARED_CREDENTIALS_FILE = $CredsFile
$env:AWS_PROFILE = $ProfileName

Write-Host "=== Step 1: Verify access ===" -ForegroundColor Green
$identity = Invoke-Aws @('sts', 'get-caller-identity', '--output', 'json') | ConvertFrom-Json
Write-Host "Account: $($identity.Account)  Arn: $($identity.Arn)"

Write-Host "`n=== Step 2: Network ===" -ForegroundColor Green
if (-not $VpcId) {
    $vpcs = Invoke-Aws @('ec2', 'describe-vpcs', '--query', 'Vpcs[*].[VpcId,CidrBlock,IsDefault]', '--output', 'json') | ConvertFrom-Json
    $pick = $vpcs | Where-Object { $_[2] -eq $true } | Select-Object -First 1
    if (-not $pick) { $pick = $vpcs[0] }
    $VpcId = $pick[0]
    Write-Host "Using VPC: $VpcId ($($pick[1]))"
}

if (-not $SubnetId) {
    $subnets = Invoke-Aws @(
        'ec2', 'describe-subnets',
        '--filters', "Name=vpc-id,Values=$VpcId",
        '--query', 'Subnets[*].[SubnetId,AvailabilityZone,MapPublicIpOnLaunch]',
        '--output', 'json'
    ) | ConvertFrom-Json
    $pickSub = $subnets | Where-Object { $_[2] -eq $true } | Select-Object -First 1
    if (-not $pickSub) { $pickSub = $subnets[0] }
    $SubnetId = $pickSub[0]
    Write-Host "Using subnet: $SubnetId ($($pickSub[1]))"
}

$vpcCidr = Invoke-Aws @('ec2', 'describe-vpcs', '--vpc-ids', $VpcId, '--query', 'Vpcs[0].CidrBlock', '--output', 'text')
$sgName = 'oms-shared-mq-sg'
$existingSg = Invoke-Aws @(
    'ec2', 'describe-security-groups',
    '--filters', "Name=group-name,Values=$sgName", "Name=vpc-id,Values=$VpcId",
    '--query', 'SecurityGroups[0].GroupId', '--output', 'text'
)
if ($existingSg -and $existingSg -ne 'None') {
    $sgId = $existingSg
    Write-Host "Reusing security group: $sgId"
}
else {
    Write-Host "Creating security group $sgName..."
    $sgId = Invoke-Aws @(
        'ec2', 'create-security-group',
        '--group-name', $sgName,
        '--description', 'Shared OMS RabbitMQ broker',
        '--vpc-id', $VpcId,
        '--query', 'GroupId', '--output', 'text'
    )
    Invoke-Aws @('ec2', 'authorize-security-group-ingress', '--group-id', $sgId, '--protocol', 'tcp', '--port', '5671', '--cidr', $vpcCidr) | Out-Null
    Invoke-Aws @('ec2', 'authorize-security-group-ingress', '--group-id', $sgId, '--protocol', 'tcp', '--port', '443', '--cidr', '0.0.0.0/0') | Out-Null
    Write-Host "Created SG: $sgId"
}

Write-Host "`n=== Step 3: Amazon MQ broker ===" -ForegroundColor Green
$existing = Invoke-Aws @('mq', 'list-brokers', '--query', "BrokerSummaries[?BrokerName=='$BrokerName'].[BrokerId,BrokerState]", '--output', 'json') | ConvertFrom-Json
$adminUser = 'admin'
$adminPass = New-RandomPassword -Length 20
$appPasswords = @{}

if ($existing -and $existing.Count -gt 0) {
    $brokerId = $existing[0][0]
    Write-Host "Broker already exists: $brokerId ($($existing[0][1]))"
    if (Test-Path $OutFile) {
        $prev = Get-Content $OutFile -Raw | ConvertFrom-Json
        $adminPass = $prev.adminPassword
        Write-Host "Using admin password from prior provision output"
    }
    else {
        throw "Broker exists but no $OutFile found. Delete broker or provide output file with adminPassword."
    }
}
else {
    $engineJson = Invoke-Aws @('mq', 'describe-broker-engine-types', '--engine-type', 'RabbitMQ', '--output', 'json') | ConvertFrom-Json
    $validVersions = @($engineJson.BrokerEngineTypes[0].EngineVersions | ForEach-Object { $_.EngineVersion })
    $engineVersion = ($validVersions | Where-Object { $_ -eq '3.13' } | Select-Object -First 1)
    if (-not $engineVersion) { $engineVersion = ($validVersions | Sort-Object { [version]$_ } | Select-Object -Last 1) }
    if (-not $engineVersion) { $engineVersion = '3.13' }
    Write-Host "Engine version: $engineVersion (valid: $($validVersions -join ', '))"
    $instanceType = 'mq.m7g.medium'
    Write-Host "Instance type: $instanceType"

    $usersFile = Join-Path $env:TEMP "mq-users-$BrokerName.json"
    $usersObj = @(
        @{
            Username = $adminUser
            Password = $adminPass
            Groups   = @('admin')
        }
    )
    [System.IO.File]::WriteAllText($usersFile, (ConvertTo-Json -InputObject $usersObj -Compress -Depth 5))
    $usersArg = "file://$($usersFile -replace '\\','/')"

    $brokerId = Invoke-Aws @(
        'mq', 'create-broker',
        '--broker-name', $BrokerName,
        '--engine-type', 'RabbitMQ',
        '--engine-version', $engineVersion,
        '--host-instance-type', $instanceType,
        '--deployment-mode', 'SINGLE_INSTANCE',
        '--publicly-accessible',
        '--subnet-ids', $SubnetId,
        '--users', $usersArg,
        '--auto-minor-version-upgrade',
        '--query', 'BrokerId', '--output', 'text'
    )
    Remove-Item $usersFile -Force -ErrorAction SilentlyContinue
    Write-Host "Created broker: $brokerId - waiting for RUNNING..."
    Wait-MqBroker -BrokerId $brokerId
}

$broker = Invoke-Aws @('mq', 'describe-broker', '--broker-id', $brokerId, '--output', 'json') | ConvertFrom-Json
$endpoint = ($broker.BrokerInstances[0].Endpoints | Where-Object { $_ -match 'amqps' } | Select-Object -First 1)
if (-not $endpoint) { $endpoint = $broker.BrokerInstances[0].Endpoints[0] }
$hostName = ($endpoint -replace '^amqps://', '' -replace ':5671$', '' -replace '/$', '')
$consoleUrl = "https://$hostName"
Write-Host "Broker endpoint: $hostName"
Write-Host "Console: $consoleUrl"

Write-Host "`n=== Step 4: RabbitMQ topology ===" -ForegroundColor Green
foreach ($vh in $Vhosts) {
    $appPass = New-RandomPassword
    $appPasswords[$vh.User] = $appPass
    $v = [Uri]::EscapeDataString($vh.Name)
    Write-Host "Vhost: $($vh.Name)"
    Invoke-RmqApi -BaseUrl $consoleUrl -Method PUT -Path "/vhosts/$v" -AdminUser $adminUser -AdminPass $adminPass -Body '{}' | Out-Null
    Invoke-RmqApi -BaseUrl $consoleUrl -Method PUT -Path "/users/$($vh.User)" -AdminUser $adminUser -AdminPass $adminPass -Body (@{ password = $appPass; tags = '' } | ConvertTo-Json -Compress) | Out-Null
    Invoke-RmqApi -BaseUrl $consoleUrl -Method PUT -Path "/permissions/$v/$($vh.User)" -AdminUser $adminUser -AdminPass $adminPass -Body (@{ configure = '.*'; write = '.*'; read = '.*' } | ConvertTo-Json -Compress) | Out-Null
    Invoke-RmqApi -BaseUrl $consoleUrl -Method PUT -Path "/exchanges/$v/main_exchange" -AdminUser $adminUser -AdminPass $adminPass -Body (@{ type = 'direct'; durable = $true; auto_delete = $false; arguments = @{} } | ConvertTo-Json -Compress) | Out-Null
    foreach ($q in $Queues) {
        Invoke-RmqApi -BaseUrl $consoleUrl -Method PUT -Path "/queues/$v/$q" -AdminUser $adminUser -AdminPass $adminPass -Body (@{ durable = $true; auto_delete = $false; arguments = @{ 'x-max-length' = 8196 } } | ConvertTo-Json -Compress) | Out-Null
        Invoke-RmqApi -BaseUrl $consoleUrl -Method POST -Path "/bindings/$v/e/main_exchange/q/$q" -AdminUser $adminUser -AdminPass $adminPass -Body (@{ routing_key = $q; arguments = @{} } | ConvertTo-Json -Compress) | Out-Null
    }
}

Write-Host "`n=== Step 5: SSM parameters ===" -ForegroundColor Green
$ssmPrefix = '/oms/shared/dev/aws-mq-broker'
$ssmParams = @{
    endpoint            = $hostName
    port                = '5671'
    scheme              = 'amqps'
    sslenabled          = 'true'
    sslprotocols        = 'None'
    virtualhost         = '/'
    adminusername       = $adminUser
    adminpassword       = $adminPass
    applicationusername = $adminUser
    applicationpassword = $adminPass
    'webconsole-endpoint' = $consoleUrl
}
foreach ($k in $ssmParams.Keys) {
    $type = if ($k -match 'password') { 'SecureString' } else { 'String' }
    Invoke-Aws @('ssm', 'put-parameter', '--name', "$ssmPrefix/$k", '--value', $ssmParams[$k], '--type', $type, '--overwrite') | Out-Null
    Write-Host "  SSM: $ssmPrefix/$k"
}

foreach ($vh in $Vhosts) {
    $spaceEnv = if ($vh.Name -eq 'pod-dev') { '/oms/pod/dev/aws-mq-broker' } else { '/oms/omnipod/qa/aws-mq-broker' }
    $updates = @{
        endpoint            = $hostName
        virtualhost         = $vh.Name
        applicationusername = $vh.User
        applicationpassword = $appPasswords[$vh.User]
        'webconsole-endpoint' = $consoleUrl
    }
    foreach ($k in $updates.Keys) {
        $type = if ($k -match 'password') { 'SecureString' } else { 'String' }
        Invoke-Aws @('ssm', 'put-parameter', '--name', "$spaceEnv/$k", '--value', $updates[$k], '--type', $type, '--overwrite') | Out-Null
        Write-Host "  SSM: $spaceEnv/$k"
    }
}

$output = @{
    accountId    = $identity.Account
    region       = $Region
    brokerId     = $brokerId
    brokerName   = $BrokerName
    endpoint     = $hostName
    consoleUrl   = $consoleUrl
    adminUser    = $adminUser
    adminPassword = $adminPass
    vpcId        = $VpcId
    subnetId     = $SubnetId
    securityGroup = $sgId
    vhosts       = $Vhosts | ForEach-Object {
        @{
            vhost = $_.Name
            user  = $_.User
            password = $appPasswords[$_.User]
            queues = $Queues
            exchange = 'main_exchange'
        }
    }
    ssmPrefixes = @($ssmPrefix, '/oms/pod/dev/aws-mq-broker', '/oms/omnipod/qa/aws-mq-broker')
    provisionedAt = (Get-Date).ToUniversalTime().ToString('o')
}
$output | ConvertTo-Json -Depth 6 | Set-Content $OutFile -Encoding UTF8

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Output saved: $OutFile"
Write-Host "Console: $consoleUrl"
Write-Host "Admin user: $adminUser"
