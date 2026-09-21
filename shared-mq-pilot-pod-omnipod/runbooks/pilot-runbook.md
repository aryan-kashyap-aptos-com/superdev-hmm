# Pilot runbook - shared AMQ (pod/dev + omnipod/qa)

## Preconditions

- [ ] Baseline exported: `scripts/Export-MqSsmBaseline.ps1`
- [ ] Standalone brokers still **RUNNING** (`oms-pod-dev-mq-broker`, `oms-omnipod-qa-mq-broker`)
- [ ] Shared broker **RUNNING** (`oms-shared-dev-mq-broker`, `mq.t3.micro` - no resize)
- [ ] Change window agreed for ECS restarts

## Phase 1 - RabbitMQ UI (shared broker)

Console: `https://b-5d413804-aec7-4af1-9a26-1de2f913f107.mq.us-east-1.on.aws`

### Per vhost (`pod-dev`, then `omnipod-qa`)

1. Create virtual host
2. Create app user (`pod-dev-app` / `omnipod-qa-app`) and save passwords securely
3. Grant permissions on that vhost only (configure/read/write `.*`)
4. On that vhost, create exchange `main_exchange` (direct, durable)
5. Create queues (durable, `x-max-length=8196`):
   - `export_requested`
   - `inventory_requested`
   - `taskprocessing_requested`
   - `taskprocessing_status`
   - `eom_atp_service_queue`
   - `eom_inventory_service_queue`
6. Bind each queue to `main_exchange` with routing key = queue name

## Phase 2 - Cutover pod/dev

### SSM (`/oms/pod/dev/aws-mq-broker/`)

| Parameter | Value |
|-----------|--------|
| endpoint | `b-5d413804-aec7-4af1-9a26-1de2f913f107.mq.us-east-1.on.aws` |
| virtualhost | `pod-dev` |
| applicationusername | `pod-dev-app` |
| applicationpassword | *(from RabbitMQ UI)* |

Do not change: port, scheme, sslenabled, sslprotocols.

### ECS cluster `oms-pod-dev-ecs-cluster`

Force new deployment:

- `oms-pod-dev-omsfeed-service`
- `oms-pod-dev-omsinventoryfeed-service`
- `oms-pod-dev-taskprocessor-service`
- `oms-pod-dev-taskscheduler-service`
- `oms-pod-dev-inventoryfacade-service`

### Validate pod/dev

- [ ] Connections on vhost `pod-dev` in RabbitMQ UI
- [ ] Feed / scheduler / taskprocessor smoke test
- [ ] No traffic on wrong vhost
- [ ] `scripts/Validate-MqPilot.ps1 -Environment pod/dev`

**Wait 24-48h before omnipod/qa** unless urgent.

## Phase 3 - Cutover omnipod/qa

### SSM (`/oms/omnipod/qa/aws-mq-broker/`)

| Parameter | Value |
|-----------|--------|
| endpoint | `b-5d413804-aec7-4af1-9a26-1de2f913f107.mq.us-east-1.on.aws` |
| virtualhost | `omnipod-qa` |
| applicationusername | `omnipod-qa-app` |
| applicationpassword | *(from RabbitMQ UI)* |

### ECS cluster `oms-omnipod-qa-ecs-cluster`

Force new deployment:

- `oms-omnipod-qa-omsfeed-service`
- `oms-omnipod-qa-omsinventoryfeed-service`
- `oms-omnipod-qa-taskprocessor-service`
- `oms-omnipod-qa-taskscheduler-service`
- `oms-omnipod-qa-inventoryfacade-service`

### Validate omnipod/qa

Same checks on vhost `omnipod-qa`.

## Post-cutover monitoring

CloudWatch → `AWS/AmazonMQ` → `oms-shared-dev-mq-broker`:

- `SystemCpuUtilization`
- `RabbitMQMemUsed` / `RabbitMQMemLimit`
- `ConnectionCount`
- `PublishRate`

## Rollback

See `rollback-recovery.md`.
