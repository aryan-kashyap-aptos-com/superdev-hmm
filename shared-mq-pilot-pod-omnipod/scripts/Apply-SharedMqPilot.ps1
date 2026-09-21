<#
.SYNOPSIS
  Create shared MQ vhost topology, update SSM, and redeploy ECS for pilot environments.
.PARAMETER Environment
  pod/dev, omnipod/qa, or all (default: all - pod/dev first)
.PARAMETER WhatIf
  Show actions without applying SSM/ECS changes (still creates topology unless -SkipTopology)
#>
[CmdletBinding()]
param(
    [ValidateSet('pod/dev', 'omnipod/qa', 'all')]
    [string]$Environment = 'all',

    [switch]$WhatIf,
    [switch]$SkipTopology,
    [switch]$SkipEcsRedeploy
)

$ErrorActionPreference = 'Stop'
$SharedHost = 'b-5d413804-aec7-4af1-9a26-1de2f913f107.mq.us-east-1.on.aws'
$SharedConsole = "https://$SharedHost"
$BastionInstanceId = 'i-09d67cca2bb3a28e8'  # oms-shared-dev-BastionHost
$AwsRegion = 'us-east-1'
$Queues = @(
    'export_requested', 'inventory_requested', 'taskprocessing_requested',
    'taskprocessing_status', 'eom_atp_service_queue', 'eom_inventory_service_queue'
)

$envConfig = @{
    'pod/dev' = @{
        vhost = 'pod-dev'
        user  = 'pod-dev-app'
        ssmPrefix = '/oms/pod/dev/aws-mq-broker'
        ecsCluster = 'oms-pod-dev-ecs-cluster'
        ecsServices = @(
            'oms-pod-dev-omsfeed-service', 'oms-pod-dev-omsinventoryfeed-service',
            'oms-pod-dev-taskprocessor-service', 'oms-pod-dev-taskscheduler-service',
            'oms-pod-dev-inventoryfacade-service'
        )
    }
    'omnipod/qa' = @{
        vhost = 'omnipod-qa'
        user  = 'omnipod-qa-app'
        ssmPrefix = '/oms/omnipod/qa/aws-mq-broker'
        ecsCluster = 'oms-omnipod-qa-ecs-cluster'
        ecsServices = @(
            'oms-omnipod-qa-omsfeed-service', 'oms-omnipod-qa-omsinventoryfeed-service',
            'oms-omnipod-qa-taskprocessor-service', 'oms-omnipod-qa-taskscheduler-service',
            'oms-omnipod-qa-inventoryfacade-service'
        )
    }
}

function Invoke-SsmShellScript {
    param(
        [string[]]$Commands,
        [string]$Comment
    )
    $payload = ($Commands | ConvertTo-Json -Compress)
    $cmdId = aws ssm send-command `
        --instance-ids $BastionInstanceId `
        --document-name 'AWS-RunShellScript' `
        --comment $Comment `
        --parameters "commands=$payload" `
        --region $AwsRegion `
        --query 'Command.CommandId' --output text

    $deadline = (Get-Date).AddMinutes(3)
    do {
        Start-Sleep -Seconds 3
        $inv = aws ssm get-command-invocation `
            --command-id $cmdId `
            --instance-id $BastionInstanceId `
            --region $AwsRegion `
            --output json | ConvertFrom-Json
    } while ($inv.Status -in @('Pending', 'InProgress', 'Delayed') -and (Get-Date) -lt $deadline)

    if ($inv.Status -ne 'Success') {
        $detail = if ($inv.StandardErrorContent) { $inv.StandardErrorContent } else { $inv.StatusDetails }
        throw "SSM command failed ($($inv.Status)): $detail"
    }
    return $inv.StandardOutputContent
}

function Initialize-VhostTopology {
    param([hashtable]$Cfg, [string]$AppPassword)

    $queueList = ($Queues | ForEach-Object { "'$_'" }) -join ' '
    $vhost = $Cfg.vhost
    $user = $Cfg.user
    $appPassEsc = $AppPassword -replace "'", "'\\''"

    $bash = @"
set -euo pipefail
BASE='https://$SharedHost/api'
ADMIN_USER=`$(aws ssm get-parameter --name '/oms/shared/dev/aws-mq-broker/adminusername' --region $AwsRegion --query 'Parameter.Value' --output text)
ADMIN_PASS=`$(aws ssm get-parameter --name '/oms/shared/dev/aws-mq-broker/adminpassword' --with-decryption --region $AwsRegion --query 'Parameter.Value' --output text)
VH='$vhost'
USER='$user'
APP_PASS='$appPassEsc'
QUEUES=($queueList)

rmq() {
  local method="`$1" path="`$2" body="`${3:-}"
  if [ -n "`$body" ]; then
    curl -fsS -u "`${ADMIN_USER}:`${ADMIN_PASS}" -X "`$method" -H 'Content-Type: application/json' -d "`$body" "`${BASE}`${path}" >/dev/null
  else
    curl -fsS -u "`${ADMIN_USER}:`${ADMIN_PASS}" -X "`$method" "`${BASE}`${path}" >/dev/null
  fi
}

echo "Creating vhost `$VH..."
rmq PUT "/vhosts/`$VH" '{}'
echo "Creating user `$USER..."
rmq PUT "/users/`$USER" "{\"password\":\"`$APP_PASS\",\"tags\":\"\"}"
echo "Setting permissions..."
rmq PUT "/permissions/`$VH/`$USER" '{"configure":".*","write":".*","read":".*"}'
echo "Creating exchange main_exchange..."
rmq PUT "/exchanges/`$VH/main_exchange" '{"type":"direct","durable":true,"auto_delete":false,"arguments":{}}'
for q in "`${QUEUES[@]}"; do
  echo "Queue + bind: `$q"
  rmq PUT "/queues/`$VH/`$q" '{"durable":true,"auto_delete":false,"arguments":{"x-max-length":8196}}'
  rmq POST "/bindings/`$VH/e/main_exchange/q/`$q" "{\"routing_key\":\"`$q\",\"arguments\":{}}"
done
echo "Topology complete for `$VH"
"@

    Write-Host "  RabbitMQ topology via SSM bastion ($BastionInstanceId)..." -ForegroundColor Cyan
    $out = Invoke-SsmShellScript -Commands @($bash) -Comment "shared-mq-pilot topology $vhost"
    $out -split "`n" | ForEach-Object { if ($_.Trim()) { Write-Host "    $_" } }
}

function Set-PilotSsm {
    param([hashtable]$Cfg, [string]$AppPassword)
    $prefix = $Cfg.ssmPrefix
    $updates = @{
        endpoint            = $SharedHost
        virtualhost         = $Cfg.vhost
        applicationusername = $Cfg.user
        applicationpassword = $AppPassword
        'webconsole-endpoint' = $SharedConsole
    }
    foreach ($k in $updates.Keys) {
        $name = "$prefix/$k"
        $val = $updates[$k]
        if ($WhatIf) {
            Write-Host "  [WhatIf] SSM $name"
            continue
        }
        $type = if ($k -match 'password') { 'SecureString' } else { 'String' }
        aws ssm put-parameter --name $name --value $val --type $type --overwrite | Out-Null
        Write-Host "  SSM updated: $name"
    }
}

function Invoke-EcsRedeploy {
    param([hashtable]$Cfg)
    foreach ($svc in $Cfg.ecsServices) {
        if ($WhatIf) {
            Write-Host "  [WhatIf] ECS redeploy $($Cfg.ecsCluster) / $svc"
            continue
        }
        Write-Host "  ECS force deploy: $svc"
        aws ecs update-service --cluster $Cfg.ecsCluster --service $svc --force-new-deployment --query 'service.serviceName' --output text | Out-Null
    }
}

# --- main ---
$targets = if ($Environment -eq 'all') { @('pod/dev', 'omnipod/qa') } else { @($Environment) }

$credFile = Join-Path $PSScriptRoot '..\baselines\pilot-app-credentials.json'
$appCreds = @{}
if (Test-Path $credFile) {
    $appCreds = Get-Content $credFile -Raw | ConvertFrom-Json -AsHashtable
}

foreach ($envKey in $targets) {
    Write-Host "`n========== $envKey ==========" -ForegroundColor Green
    $cfg = $envConfig[$envKey]

    if (-not $appCreds.ContainsKey($cfg.user)) {
        $appCreds[$cfg.user] = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 24 | ForEach-Object { [char]$_ })
    }
    $appPass = $appCreds[$cfg.user]

    if (-not $SkipTopology) {
        Write-Host "RabbitMQ topology..."
        Initialize-VhostTopology -Cfg $cfg -AppPassword $appPass
    }

    Write-Host "SSM parameters..."
    Set-PilotSsm -Cfg $cfg -AppPassword $appPass

    if (-not $SkipEcsRedeploy) {
        Write-Host "ECS redeploy..."
        Invoke-EcsRedeploy -Cfg $cfg
    }
}

if (-not $WhatIf) {
    $appCreds | ConvertTo-Json | Set-Content $credFile -Encoding UTF8
    Write-Host "`nApp credentials saved to baselines/pilot-app-credentials.json (gitignored)"
}

Write-Host "`nDone. Run Validate-MqPilot.ps1 to check status."
