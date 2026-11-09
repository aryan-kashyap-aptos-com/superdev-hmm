# Terraform stack index (`oms-infrastructure`)

**Audience:** Platform engineers choosing which folder to `terraform apply`.  
**Count:** **62** Terraform roots — **60** with `1-versions.tf` + **2** Snowflake stacks (`13-snowflake/*`). **100%** `.tf` inventory: [24-infrastructure-complete-reference.md](./24-infrastructure-complete-reference.md).

Every stack = **own state file** (backend `*.conf` in Harness or local). Pattern: `terraform init -backend-config=…` then `apply -var-file=secrets.tfvars`.

---

## Layer 01 — infrastructure (foundation)

| Stack path | Purpose |
|------------|---------|
| `01-infrastructure/00-aws-kms` | CMKs for encryption |
| `01-infrastructure/01-parameterstore` | **Central SSM** — ~83 parameters (endpoints, DB hints, feature flags) |
| `01-infrastructure/02-vpc-infrastructure` | VPC, subnets, bastion EC2, security groups |
| `01-infrastructure/03-rds-database-infrastructure/01-rds-database-master` | Aurora master cluster |
| `01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision` | Aurora subdivision / proxy |
| `01-infrastructure/04-awsmq-broker-infrastructure` | Amazon MQ broker |
| `01-infrastructure/05-vpc-peering/*` (6 stacks) | Peering variants (Harness, core, 15-network) |
| `01-infrastructure/07-beanstalk` | Elastic Beanstalk (legacy/adjunct) |
| `01-infrastructure/08-core/projects/eom-terraform-master/parameterstore` | Legacy EOM parameter store |
| `01-infrastructure/09-usergroup` | IAM user groups |
| `01-infrastructure/10-transitgateway` | Transit Gateway |
| `01-infrastructure/11-vpc-endpoints` | Interface VPC endpoints |

**Also present (no `1-versions.tf` in scan):** `06-database-operation/01-rds-init` (bastion DB bootstrap scripts), `08-core` Harness YAML — see [10-platform-data-delivery.md](./10-platform-data-delivery.md).

**Harness `oms15-inf.yaml` applies (subset):** KMS → parameterstore → VPC → RDS → MQ.

---

## Layer 02 — platform (shared compute)

| Stack path | Purpose |
|------------|---------|
| `02-platform/01-ecs-cluster` | ECS cluster, **execution role**, EFS (minisoft AP) |
| `02-platform/02-s3-staticweb` | Static website bucket |
| `02-platform/03-aws-batch/01-aws-batch-sql-job` | Legacy shared SQL Batch platform |
| `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform` | **Batch stage A** — CE + JQ |
| `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db` | **Batch stage C** — Postgres CE/JQ rows |
| `02-platform/04-aws-lambda-layer` | Shared Lambda layers |

---

## Layer 03 — application — ECS (22 services)

| Folder | ECS service | Domain doc |
|--------|-------------|------------|
| `01-currencyexchange` | currencyexchange | [09](./09-facades-core-edge.md) |
| `02-efs-fileexplorer` | efs-fileexplorer | [09](./09-facades-core-edge.md) |
| `03-keycloak` | keycloak | [09](./09-facades-core-edge.md) |
| `04-minisoft` | minisoft | [06](./06-site-manager-shoplogic.md) |
| `05-extensibility` | extensibility | [09](./09-facades-core-edge.md) |
| `06-taskscheduler` | taskscheduler | [08](./08-task-engine-feeds.md) |
| `07-omsfeed` | omsfeed | [08](./08-task-engine-feeds.md) |
| `08-omsinventoryfeed` | omsinventoryfeed | [08](./08-task-engine-feeds.md) |
| `09-taskprocessor` | taskprocessor | [08](./08-task-engine-feeds.md) |
| `10-orderfacade` | orderfacade | [09](./09-facades-core-edge.md) |
| `11-inventoryfacade` | inventoryfacade | [09](./09-facades-core-edge.md) |
| `15-configrulemanager` | configrulemanager | [09](./09-facades-core-edge.md) |
| `16-coreapi` | coreapi | [09](./09-facades-core-edge.md) |
| `17-coreservice` | coreservice | [09](./09-facades-core-edge.md) |
| `18-corepaymentapi` | corepaymentapi | [09](./09-facades-core-edge.md) |
| `19-corekekservice` | corekekservice | [09](./09-facades-core-edge.md) |
| `20-omstaxationfacade` | omstaxationfacade | [09](./09-facades-core-edge.md) |
| `21-omstaxation` | omstaxation | [09](./09-facades-core-edge.md) |
| `22-servicemanagerscheduler` | servicemanagerscheduler | [07](./07-batch-scheduler-api-ui.md) |

**In `oms15-ECS.yaml` today:** keycloak, minisoft, extensibility, taskscheduler, omsfeed, omsinventoryfeed, taskprocessor, orderfacade, inventoryfacade + **ecs-cluster** platform. Stacks `15`–`22` may use other Harness pipelines.

---

## Layer 03 — application — Batch

| Stack path | Stage | Purpose |
|------------|-------|---------|
| `03-aws-batch-job/01-sql-job` | Legacy | Old SQL batch job |
| `03-aws-batch-job/02-servicemanager-scheduled-job` | **B** | Job definition per `jobname` |
| `03-aws-batch-job/03-servicemanager-batch-catalog-job-db` | **D** | Catalog upsert per `jobname` |
| `03-aws-batch-job/04-servicemanager-batch-catalog-platform-db` | Placeholder | Keypair only — **not** stage C |

---

## Layer 03 — application — integration & edge

| Stack path | Purpose |
|------------|---------|
| `02-aws-lambda` | Functions (catalog loader, etc.) |
| `04-oms-providers/common/*` | Shared modules (API GW, Step Fn, layers, params) |
| `04-oms-providers/lambda` | Provider lambda roots |
| `05-aws-cognito` | User pools |
| `06-aws-stepfunction` | Workflow orchestration + EventBridge schedules |
| `07-aws-sqs` | Queues |
| `08-aws-event-bridge-pipes` | EventBridge pipes |
| `09-aws-eventbus` | Event buses |
| `10-aws-api-gateway` | API Gateway |
| `10-aws-dlq` | DLQ handling |
| `11-aws-parameterstore` | App-level parameters |
| `12-core-route53` | DNS (reads SSM endpoints) |

**Snowflake:** `03-application/13-snowflake/` (DMS + setup SQL) — separate init pattern.

---

## Dependency order (simplified bootstrap)

```text
00-kms → 01-parameterstore → 02-vpc → 03-rds → (bastion init) 
  → 02-platform/01-ecs-cluster 
  → 03-keycloak / 04-minisoft / … ECS 
  → 02-batch platform A → C → job B → D per jobname 
  → 22-servicemanagerscheduler + 06-stepfunction (Batch Job Manager path)
```

Detail: [10-platform-data-delivery.md](./10-platform-data-delivery.md), [13-deployables-catalog.md](./13-deployables-catalog.md).

---

## How to find state keys

Each stack’s `config.tfvars.example` or Harness inline backend block shows the S3 key pattern, usually:

`{space}/{environment}/…/terraform.tfstate`

---

## Related

- [02-terraform.md](./02-terraform.md)  
- [11-environments-matrix.md](./11-environments-matrix.md)  
- [17-workflows-and-step-functions.md](./17-workflows-and-step-functions.md)  
