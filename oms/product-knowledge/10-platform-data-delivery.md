# Platform foundation, data, messaging, and delivery

**Audience:** Platform engineers, DBAs, release managers.  
**Prerequisites:** [02-terraform.md](./02-terraform.md).

---

## What this layer is

Before any OMS **application** container runs, the estate needs:

- **Network** (VPC, peering, endpoints)  
- **Data** (Aurora PostgreSQL, optional Snowflake/DMS)  
- **Messaging** (Amazon MQ, SQS, EventBridge)  
- **Compute platform** (ECS cluster, EFS, Batch platform)  
- **Delivery** (Harness pipelines, per-stack Terraform state)

Everything under `oms-infrastructure/01-infrastructure` and `02-platform` is this layer. `03-application` stacks **consume** remote state from here.

---

## Layer diagram

```text
01-infrastructure     "Land" — VPC, RDS, MQ, KMS, bastion, parameter store seeds
        │
        ▼
02-platform           "Shared building" — ECS cluster, Batch CE/JQ, lambda layers, static web
        │
        ▼
03-application        "Tenants" — each ECS service, Batch job, Step Functions, Cognito, …
```

Convention: `{layer}/{product-area}/{numbered-stack}/` = one Terraform root with its own **backend state key**.

---

## `01-infrastructure` — detailed map

| Folder | Purpose |
|--------|---------|
| `00-aws-kms` | Encryption keys |
| `01-parameterstore` | **Central SSM** — endpoints, DB fragments, sitemanager/minisoft/facade prefixes ([HOME](./HOME.md)) |
| `02-vpc-infrastructure` | VPC, subnets, baseline security groups |
| `03-rds-database-infrastructure` | Aurora — master + subdivision stacks |
| `04-awsmq-broker-infrastructure` | Amazon MQ for legacy/async messaging |
| `05-vpc-peering/*` | Peering to core / Harness / 15 networks |
| `06-database-operation/01-rds-init` | **Bastion** — SSH for catalog SQL (Batch C/D) |
| `07-beanstalk` | Elastic Beanstalk (if used in estate) |
| `08-core` | Harness YAML sources, DMS, monitoring modules |
| `09-usergroup` | IAM user groups |
| `10-transitgateway` | TGW attachments |
| `11-vpc-endpoints` | Private AWS API access |

**Multitenant note:** Some remote state reads use `master_space` / `master_environment` while apps use `space` / `environment` ([02-terraform.md](./02-terraform.md)).

---

## `02-platform` — detailed map

| Folder | Purpose |
|--------|---------|
| `01-ecs-cluster` | Cluster, **execution role**, EFS (minisoft mount), discovery |
| `02-s3-staticweb` | Static web assets |
| `03-aws-batch` | Batch **platform** (stages A + C), legacy `01-aws-batch-sql-job` |
| `04-aws-lambda-layer` | Shared layers (e.g. psycopg2 for catalog Lambda) |

Batch Service Manager platform:

- **A:** `03-aws-batch/02-aws-batch-servicemanager-platform`  
- **C:** `03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db`  

---

## `03-application` — cross-cutting (not ECS one-offs)

| Folder | Purpose |
|--------|---------|
| `02-aws-lambda` | Functions including **workflow catalog loader** |
| `04-oms-providers` | Shared Terraform modules |
| `05-aws-cognito` | User pools |
| `06-aws-stepfunction` | Workflow orchestration ([04-deep-repo-scan](./04-deep-repo-scan.md)) |
| `07-aws-sqs` | Queues |
| `08-aws-event-bridge-pipes` | Pipes |
| `09-aws-eventbus` | Event buses |
| `10-aws-api-gateway` | API Gateway |
| `10-aws-dlq` | Dead-letter handling |
| `11-aws-parameterstore` | App-level params |
| `12-core-route53` | DNS |
| `13-snowflake` | DMS + Snowflake setup tasks |

---

## Data plane

| Concern | Where |
|---------|--------|
| **OMS business data** | Aurora Postgres — connection strings under `…/aws-db-pgsql/…` SSM |
| **Batch scheduler catalog** | Schema often `oms_batch` (variable `batch_scheduler_catalog_schema`) |
| **Batch scheduler API DB schema** | SSM `db_rds_servicemanagerscheduler_dbname` on scheduler task |
| **Migrations (app)** | `RepoSuite/oms/SQLChangeScripts/` |
| **Migrations (bastion)** | Batch catalog upsert via stage D |
| **Analytics** | `13-snowflake` — DMS replication path |

**Bootstrap pattern for Batch workers:** `ssm_connectionstring` + `connectionstringParams` → `ConnectionStrings:Database` in container ([01-batch.md](./01-batch.md)).

---

## Messaging plane

| Technology | Infra folder | Typical consumer |
|------------|--------------|------------------|
| Amazon MQ | `04-awsmq-broker-infrastructure` | Legacy feed/task paths |
| SQS | `07-aws-sqs` | Decoupled workers |
| EventBridge | Pipes, scheduler on Batch API | Cron → Step Functions |
| Event bus | `09-aws-eventbus` | Cross-service events |

During migration, **treat MQ as legacy** for inventory/export where Batch already owns the path ([08-task-engine-feeds.md](./08-task-engine-feeds.md)).

---

## Delivery — Harness and Terraform

**Typical local workflow** (one stack):

```bash
cd RepoSuite/oms-infrastructure/<stack-path>
terraform init -backend-config="dev.conf" -var-file="secrets.tfvars"
terraform plan -var-file="secrets.tfvars"
terraform apply -var-file="secrets.tfvars"
```

| File | Committed? |
|------|------------|
| `config.tfvars.example` | Yes — structure |
| `secrets.tfvars`, `*.conf` backends | **No** — local/Harness secrets |

**Harness ECS pipeline example:** `01-infrastructure/08-core/harness-pipeline-source/oms15-ECS.yaml` — parallel deploy stages for keycloak, minisoft, feeds, facades, task services.

**Batch pipeline:** documented under `03-aws-batch-job/README.md` (stages A–D naming traps in [02-terraform.md](./02-terraform.md)).

**Cost tags:** repo script `scripts/apply-cost-allocation-tags.py` injects `owners`, `space`, `environment` into Terraform tags.

---

## State keys (mental model)

Pattern: `{space}/{environment}/…/terraform.tfstate` in bucket `oms-deployment-state` (or `state_bucket` var).

Examples:

| Stack | Key suffix (illustrative) |
|-------|---------------------------|
| minisoft ECS | `applications/ecs-service/minisoft/terraform.tfstate` |
| Batch job B | `application/aws-batch/servicemanager-scheduled-job/{jobname}/terraform.tfstate` |
| Batch platform A | `…/servicemanager-batch-platform/{batch_shared_name}/terraform.tfstate` |

Never commit state files.

---

## Snowflake / DMS (`13-snowflake`)

| Subfolder | Role |
|-----------|------|
| `01-dms-setup` | Database Migration Service to replicate OMS data |
| `02-snowflake-setup` | Snowflake tasks (e.g. merge root task SQL on master) |

Analytical path — **not** in the hot path for Site Manager clicks.

---

## New environment bootstrap (checklist)

| Order | Action |
|-------|--------|
| 1 | VPC + RDS (`01-infrastructure`) |
| 2 | Parameter store base (`01-parameterstore`) |
| 3 | ECS cluster + EFS (`02-platform/01-ecs-cluster`) |
| 4 | Keycloak/Cognito as required |
| 5 | minisoft + facades (`03-application/01-aws-ecs-service`) |
| 6 | Batch platform A → C |
| 7 | Per-job B → D for each Batch worker |
| 8 | servicemanagerscheduler + Step Functions if using UI workflows |

---

## Pitfalls

1. **`business_divsion` typo** — must match across all stacks.  
2. **Bastion private_key** — required for catalog stages C/D via Harness `TF_VAR_private_key`.  
3. **Wrong stage folder** for Batch B/D — use `02-servicemanager-scheduled-job` and `03-servicemanager-batch-catalog-job-db`.  
4. **`.terraform/` in repo** — local provider caches; not documentation of live AWS.

---

## Next reading

- [02-terraform.md](./02-terraform.md)  
- [05-oms-estate-map.md](./05-oms-estate-map.md)  
- [HOME.md](./HOME.md)  
