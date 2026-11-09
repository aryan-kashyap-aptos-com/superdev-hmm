# `oms-infrastructure` — complete reference

**Repo:** `RepoSuite/oms-infrastructure`  
**Coverage:** **100% Terraform file inventory** — **974/974** `.tf` files listed in [inventories/infrastructure-all-tf.txt](./inventories/infrastructure-all-tf.txt), grouped by **62 roots** in [inventories/infrastructure-tf-by-root.md](./inventories/infrastructure-tf-by-root.md).  
**Functional guide:** [31-functional-infrastructure-platform.md](./31-functional-infrastructure-platform.md).  
**Narrative:** [02-terraform.md](./02-terraform.md), stack table [15-infrastructure-stack-index.md](./15-infrastructure-stack-index.md).

---

## Counts

| Metric | Value |
|--------|------:|
| Terraform **roots** (`1-versions.tf` or Snowflake `00-*` layout) | **62** |
| `.tf` files (excl. `.terraform/`) | **974** |
| Foundation SSM parameters cataloged | **83** → [19-ssm-parameter-catalog.md](./19-ssm-parameter-catalog.md) |
| Harness pipeline YAML (in repo) | **4** → [20-harness-pipelines.md](./20-harness-pipelines.md) |
| Legacy `08-core` + `06-database-operation` `.tf` | in inventory under dedicated sections |

---

## Layer model

| Layer | Folder prefix | Role |
|-------|---------------|------|
| **01-infrastructure** | `01-infrastructure/` | KMS, SSM, VPC, RDS, MQ, peering, TGW, endpoints |
| **02-platform** | `02-platform/` | ECS cluster, S3 static, Batch platform A/C, Lambda layers |
| **03-application** | `03-application/` | ECS services, Batch B/D, Lambda, SFN, API GW, Snowflake |

**Batch Service Manager pipeline (memorize):**

```text
A: 02-platform/03-aws-batch/02-aws-batch-servicemanager-platform
C: 02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db
B: 03-application/03-aws-batch-job/02-servicemanager-scheduled-job  (per jobname)
D: 03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db
SFN: 03-application/06-aws-stepfunction
Scheduler ECS: 03-application/01-aws-ecs-service/22-servicemanagerscheduler
```

---

## All 62 Terraform roots

```text
01-infrastructure/00-aws-kms
01-infrastructure/01-parameterstore
01-infrastructure/02-vpc-infrastructure
01-infrastructure/03-rds-database-infrastructure/01-rds-database-master
01-infrastructure/03-rds-database-infrastructure/02-rds-database-subdivision
01-infrastructure/04-awsmq-broker-infrastructure
01-infrastructure/05-vpc-peering/01-15-existing-core
01-infrastructure/05-vpc-peering/02-15-15
01-infrastructure/05-vpc-peering/02-15-new-core
01-infrastructure/05-vpc-peering/03-harness-new-core
01-infrastructure/05-vpc-peering/04-15-harness
01-infrastructure/05-vpc-peering/05-new-core-existing-core
01-infrastructure/07-beanstalk
01-infrastructure/08-core/projects/eom-terraform-master/parameterstore
01-infrastructure/09-usergroup
01-infrastructure/10-transitgateway
01-infrastructure/11-vpc-endpoints
02-platform/01-ecs-cluster
02-platform/02-s3-staticweb
02-platform/03-aws-batch/01-aws-batch-sql-job
02-platform/03-aws-batch/02-aws-batch-servicemanager-platform
02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db
02-platform/04-aws-lambda-layer
03-application/01-aws-ecs-service/01-currencyexchange
03-application/01-aws-ecs-service/02-efs-fileexplorer
03-application/01-aws-ecs-service/03-keycloak
03-application/01-aws-ecs-service/04-minisoft
03-application/01-aws-ecs-service/05-extensibility
03-application/01-aws-ecs-service/06-taskscheduler
03-application/01-aws-ecs-service/07-omsfeed
03-application/01-aws-ecs-service/08-omsinventoryfeed
03-application/01-aws-ecs-service/09-taskprocessor
03-application/01-aws-ecs-service/10-orderfacade
03-application/01-aws-ecs-service/11-inventoryfacade
03-application/01-aws-ecs-service/15-configrulemanager
03-application/01-aws-ecs-service/16-coreapi
03-application/01-aws-ecs-service/17-coreservice
03-application/01-aws-ecs-service/18-corepaymentapi
03-application/01-aws-ecs-service/19-corekekservice
03-application/01-aws-ecs-service/20-omstaxationfacade
03-application/01-aws-ecs-service/21-omstaxation
03-application/01-aws-ecs-service/22-servicemanagerscheduler
03-application/02-aws-lambda
03-application/03-aws-batch-job/01-sql-job
03-application/03-aws-batch-job/02-servicemanager-scheduled-job
03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db
03-application/04-oms-providers/common/aws-api-gateway
03-application/04-oms-providers/common/aws-step-function
03-application/04-oms-providers/common/lambda-layers
03-application/04-oms-providers/common/parameter-store-vars
03-application/04-oms-providers/lambda
03-application/05-aws-cognito
03-application/06-aws-stepfunction
03-application/07-aws-sqs
03-application/08-aws-event-bridge-pipes
03-application/09-aws-eventbus
03-application/10-aws-api-gateway
03-application/10-aws-dlq
03-application/11-aws-parameterstore
03-application/12-core-route53
03-application/13-snowflake/01-dms-setup
03-application/13-snowflake/02-snowflake-setup
```

Canonical copy: [inventories/infrastructure-terraform-roots.txt](./inventories/infrastructure-terraform-roots.txt).

---

## Paths outside numbered roots (still 100% inventoried)

| Bucket | Purpose |
|--------|---------|
| `01-infrastructure/06-database-operation` | Bastion RDS init SQL/scripts (no `1-versions.tf`) |
| `01-infrastructure/08-core` | Legacy `eom-terraform-master` + shared modules (~356 `.tf`) |
| `01-infrastructure/08-core/harness-pipeline-source/` | `oms15-inf.yaml`, `oms15-ECS.yaml`, `oms15-lambda.yaml`, `oms15-core.yaml` |
| `scripts/` | e.g. cost allocation tag helper |

Every `.tf` path appears exactly once under [inventories/infrastructure-tf-by-root.md](./inventories/infrastructure-tf-by-root.md).

---

## Numbering convention (per stack folder)

Typical Harness stack file order:

| Prefix | Typical content |
|--------|-----------------|
| `0-terraform-remote-state-datasource.tf` | Remote state |
| `1-versions.tf` | Providers + TF version |
| `2-generic-variables.tf` | `state_bucket`, `space`, `environment` |
| `3-local-values.tf` | SSM prefix, tags, naming |
| `4-*` | Data sources, extra variables |
| `5-*` | Service resources (ECS task, Batch JD, …) |
| `6-*` | API Gateway / Route53 adjuncts |
| `7-*` | DNS registration |
| `8-*` | EventBridge / integration checks |

---

## Remote state key pattern

```text
<s3 bucket>/<owners>/<space>/<environment>/<category>/terraform.tfstate
```

Examples:

- VPC: `…/infrastructure/vpc/terraform.tfstate`
- ECS service: `…/applications/ecs-service/<name>/terraform.tfstate`
- Batch job B: `…/applications/batch-job/<jobname>/terraform.tfstate`

Harness templates: `01-infrastructure/08-core/harness-pipeline-source/*.yaml`.

---

## Related

- [04-deep-repo-scan.md](./04-deep-repo-scan.md) — Batch ↔ infra wiring  
- [17-workflows-and-step-functions.md](./17-workflows-and-step-functions.md)  
- Skill: `superdev-hmm/.cursor/skills/oms-infrastructure/reference.md`
