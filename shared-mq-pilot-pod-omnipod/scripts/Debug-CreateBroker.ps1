$ErrorActionPreference = 'Continue'
$Root = 'C:\PROD\ConnectorSuite\shared-mq-pilot-pod-omnipod'
$env:AWS_SHARED_CREDENTIALS_FILE = Join-Path $Root '.aws-temp-credentials'
$env:AWS_PROFILE = 'temp-mq-admin'
$env:AWS_DEFAULT_REGION = 'us-east-1'

$users = '[{"Username":"admin","Password":"TempAdminPass123456789","Groups":["admin"]}]'
$log = Join-Path $Root 'baselines\create-broker-debug.log'

$cmd = @(
    'aws','mq','create-broker',
    '--broker-name','oms-shared-dev-mq-broker',
    '--engine-type','RabbitMQ',
    '--engine-version','3.13.7',
    '--host-instance-type','mq.t3.micro',
    '--deployment-mode','SINGLE_INSTANCE',
    '--publicly-accessible',
    '--subnet-ids','subnet-0221e0c7482c56acf',
    '--security-groups','sg-06fadc62da43ea204',
    '--users',$users,
    '--auto-minor-version-upgrade',
    '--profile','temp-mq-admin',
    '--region','us-east-1'
)

"Command: $($cmd -join ' ')" | Set-Content $log
& $cmd[0] $cmd[1..($cmd.Length-1)] *>> $log 2>&1
"Exit: $LASTEXITCODE" | Add-Content $log
