# Rollback and recovery - shared AMQ pilot

Use this when cutover fails or you need to return to standalone brokers.

## When to rollback

- ECS tasks fail health checks after SSM change
- RabbitMQ connection errors in ODX / scheduler logs
- Cross-env message leakage (wrong vhost)
- Shared `mq.t3.micro` under memory/CPU pressure

## Fast rollback (per environment)

### 1. Restore SSM from baseline

```powershell
cd C:\PROD\ConnectorSuite\shared-mq-pilot-pod-omnipod\scripts

# One environment
.\Restore-MqSsmBaseline.ps1 -BaselineFile ..\baselines\ssm-mq-baseline-20260905.json -Environment pod/dev

# Or both
.\Restore-MqSsmBaseline.ps1 -BaselineFile ..\baselines\ssm-mq-baseline-20260905.json -Environment all
```

### 2. Force new ECS deployment

**pod/dev** (`oms-pod-dev-ecs-cluster`):

- oms-pod-dev-omsfeed-service
- oms-pod-dev-omsinventoryfeed-service
- oms-pod-dev-taskprocessor-service
- oms-pod-dev-taskscheduler-service
- oms-pod-dev-inventoryfacade-service

**omnipod/qa** (`oms-omnipod-qa-ecs-cluster`):

- oms-omnipod-qa-omsfeed-service
- oms-omnipod-qa-omsinventoryfeed-service
- oms-omnipod-qa-taskprocessor-service
- oms-omnipod-qa-taskscheduler-service
- oms-omnipod-qa-inventoryfacade-service

### 3. Verify standalone broker

| Env | Standalone broker | Expected endpoint host |
|-----|-------------------|------------------------|
| pod/dev | oms-pod-dev-mq-broker | `b-e93a05aa-377d-441c-8e35-5b862ff6b9cd.mq.us-east-1.on.aws` |
| omnipod/qa | oms-omnipod-qa-mq-broker | `b-aa4f9294-525c-4c56-bdec-16dc30e652ee.mq.us-east-1.on.aws` |

```powershell
.\Validate-MqPilot.ps1 -ExpectStandalone
```

## Manual SSM rollback (if script unavailable)

### pod/dev

```
/oms/pod/dev/aws-mq-broker/endpoint             = b-e93a05aa-377d-441c-8e35-5b862ff6b9cd.mq.us-east-1.on.aws
/oms/pod/dev/aws-mq-broker/virtualhost            = /
/oms/pod/dev/aws-mq-broker/applicationusername      = admin
/oms/pod/dev/aws-mq-broker/applicationpassword      = (from ssm-mq-baseline-20260905.json)
```

### omnipod/qa

```
/oms/omnipod/qa/aws-mq-broker/endpoint            = b-aa4f9294-525c-4c56-bdec-16dc30e652ee.mq.us-east-1.on.aws
/oms/omnipod/qa/aws-mq-broker/virtualhost           = /
/oms/omnipod/qa/aws-mq-broker/applicationusername   = admin
/oms/omnipod/qa/aws-mq-broker/applicationpassword   = (from ssm-mq-baseline-20260905.json)
```

## What rollback does NOT require

- Deleting shared broker
- Terraform apply
- VPC changes
- Application redeploy (binary) - only ECS service restart

## After rollback

- Standalone brokers were never deleted - apps reconnect automatically
- Shared broker vhosts can remain (harmless) or be removed later
- Re-export baseline if you changed passwords: `Export-MqSsmBaseline.ps1`

## Re-attempt cutover

1. Fix root cause (topology, credentials, capacity)
2. Fresh `Export-MqSsmBaseline.ps1`
3. Follow `pilot-runbook.md` again one env at a time
