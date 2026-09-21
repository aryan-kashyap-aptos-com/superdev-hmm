# Broker inventory summary (capture 2026-09-05)

Account: `268173716021` | Region: `us-east-1` | Total brokers: **19**

## Pilot scope

| Environment | Standalone broker (rollback) | ECS cluster | VPC |
|-------------|------------------------------|-------------|-----|
| pod/dev | `oms-pod-dev-mq-broker` (m7g.medium) | `oms-pod-dev-ecs-cluster` | vpc-0d5b8d7062341f295 |
| omnipod/qa | `oms-omnipod-qa-mq-broker` (m7g.medium) | `oms-omnipod-qa-ecs-cluster` | vpc-0d5b8d7062341f295 |

## Shared target (no resize)

| Property | Value |
|----------|--------|
| Broker | `oms-shared-dev-mq-broker` |
| Type | `mq.t3.micro` (unchanged) |
| Endpoint | `b-5d413804-aec7-4af1-9a26-1de2f913f107.mq.us-east-1.on.aws` |
| VPC | vpc-0d5b8d7062341f295 |

## Usage snapshot (from prior analysis)

| Category | Count |
|----------|-------|
| Active with ECS MQ services running | ~13 |
| CloudWatch activity last 14d | 15 |
| Zero activity (delete candidates later) | 4 (perf-qa orphan, shared-dev, appsec-dast, aoregression202530) |

## Not in this pilot

- pod2/dev (different VPC - needs peering)
- All other namespaces

Full broker list: `amazon-mq-brokers-list.json`
