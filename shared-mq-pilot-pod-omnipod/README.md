# Shared Amazon MQ pilot - pod/dev + omnipod/qa

Working area for consolidating **pod/dev** and **omnipod/qa** onto one shared RabbitMQ broker (`oms-shared-dev-mq-broker`) using **separate virtual hosts**, with full rollback to standalone brokers.

## Scope

| In scope | Out of scope |
|----------|----------------|
| `pod/dev`, `omnipod/qa` | Other 17 MQ brokers |
| SSM Parameter Store updates | Terraform / Harness changes |
| RabbitMQ vhost topology on shared broker | Resizing shared broker (stays `mq.t3.micro`) |
| ECS force-new-deployment | Deleting standalone brokers |

## Folder structure

```
shared-mq-pilot-pod-omnipod/
  README.md
  .gitignore                         # Excludes baseline JSON with decrypted passwords
  baselines/
    captured-at.json                 # Snapshot metadata
    ssm-mq-baseline-20260905.json    # FULL rollback (local only, contains secrets)
    ssm-mq-baseline-REDACTED.json      # Safe to share / commit
    shared-mq-target-state.json        # Post-cutover target SSM + vhosts
    ecs-mq-services-baseline.json      # ECS services to redeploy
    amazon-mq-brokers-list.json        # All account brokers at capture time
  scripts/
    Export-MqSsmBaseline.ps1           # Re-export SSM before changes
    Restore-MqSsmBaseline.ps1          # Rollback SSM from baseline file
    Validate-MqPilot.ps1               # Quick post-cutover checks
  runbooks/
    pilot-runbook.md                   # Step-by-step cutover
    rollback-recovery.md               # Emergency rollback
```

## Quick start

### Before any change

```powershell
cd C:\PROD\ConnectorSuite\shared-mq-pilot-pod-omnipod\scripts
.\Export-MqSsmBaseline.ps1
```

### Rollback

```powershell
.\Restore-MqSsmBaseline.ps1 -BaselineFile ..\baselines\ssm-mq-baseline-20260905.json -Environment pod/dev
# Then force new deployment on pod/dev ECS services (see runbook)
```

### Validate after cutover

```powershell
.\Validate-MqPilot.ps1
```

## Shared broker

| Property | Value |
|----------|--------|
| Name | `oms-shared-dev-mq-broker` |
| Endpoint | `b-5d413804-aec7-4af1-9a26-1de2f913f107.mq.us-east-1.on.aws` |
| Instance | `mq.t3.micro` (not resized for this pilot) |
| VPC | `vpc-0d5b8d7062341f295` (same as both pilot envs) |

## Security note

`baselines/ssm-mq-baseline-*.json` contains **decrypted SSM passwords**. It is listed in `.gitignore`. Do not commit or share that file. Use `ssm-mq-baseline-REDACTED.json` for documentation.

## Related analysis

Broker usage inventory and orphan analysis were performed in Cursor session (2026-09-04). Key finding: 13 brokers active, 4 orphan/idle candidates for future cleanup.
