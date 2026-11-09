# Extended glossary and acronyms

**Audience:** New hires decoding meetings and tickets.  
**Short glossary:** [00-onboarding.md](./00-onboarding.md).

---

## Products and code names

| Term | Meaning |
|------|---------|
| **EOM** | E-Commerce Order Management — component libraries (`EOM.*`, `Eom.Component.*` NuGet) |
| **DCEOM** | .NET wrapper layer around EOM (`DCEOM.*` projects) |
| **ShopVisible / ShopLogic** | Legacy brand for monorepo admin + services |
| **Site Manager (SM)** | Operator admin product; **`/backadmin`** URLs |
| **minisoft** | AWS **ECS service name** hosting Site Manager container |
| **Toronado** | Scheduler/config subsystem in OMS DB (`jobstep`, export XML) |
| **ODX** | Legacy integration/export dispatcher (queues being retired for Batch) |
| **Service Manager** | Windows-era scheduled task host → **AWS Batch** migration |
| **Batch Job Manager** | Admin UI for defining Batch schedules (React in `oms`) |
| **SIMFA** | Site-specific integration — ask team Confluence |
| **iZenda** | Embedded reporting in Site Manager |

---

## AWS and platform

| Term | Meaning |
|------|---------|
| **space** | Tenant slice in Terraform (`pod`, `hox-clops2`, …) |
| **environment** | Stage (`dev`, `qa`, `uat`, `prod`) |
| **owners / business_divsion** | Cost/SSM owner tag (spelling as in tfvars) |
| **Fargate** | Serverless ECS/Batch compute |
| **JD** | Batch **job definition** |
| **CE / JQ** | Batch **compute environment** / **job queue** |
| **SSM** | AWS Systems Manager Parameter Store |
| **Harness** | Continuous delivery running Terraform |
| **EFS** | Shared file system (minisoft mount `/minisoft`) |
| **Step Functions** | AWS workflow; may chain Batch `submitJob.sync` |
| **EventBridge Scheduler** | Cron → start Step Function or targets |

---

## Databases and schemas

| Term | Meaning |
|------|---------|
| **OMS DB** | Main PostgreSQL business database |
| **oms_batch** | Postgres schema/catalog for Batch scheduler (CE, JQ, JD rows) |
| **SearchPath** | Postgres schema search path on scheduler API connection |
| **Bastion** | Jump host for running catalog upsert SQL (stages C/D) |
| **RDS init** | SQL templates seeding site metadata including endpoint placeholders |

---

## Batch and JSON

| Term | Meaning |
|------|---------|
| **SubmitJob** | AWS API to run one Batch job with parameters |
| **Generic envelope** | JSON with `configType`, `operation`, `settings`, `filters` |
| **Ref::** | Batch substitution marker in job definition command |
| **taskId** | OMS scheduler GUID for export de-dup (**not** Batch job id) |
| **Exit code** | Process return value; infra should align retries (see [01-batch.md](./01-batch.md)) |
| **lastsynced** | Toronado `jobstep` timestamp updated on successful inventory feed |

---

## Pipelines (examples)

| Name | Role |
|------|------|
| `oms release pipeline` | Build/publish Docker images to ECR |
| `oms15-inf` | Foundation Terraform |
| `oms15-ECS` | Classic ECS service Terraform |
| `OMS-DEV-SERVICE-MANAGER-BATCH-CD` | Batch + Step Functions |

Full table: [13-deployables-catalog.md](./13-deployables-catalog.md).

---

## URLs and paths

| Path | Meaning |
|------|---------|
| `/backadmin/` | Site Manager ASP.NET root |
| `/backadmin/BatchJobManager.aspx` | Batch Job Manager host page |
| `/api/v1/*` | Scheduler API (via proxy from ShopLogic) |

Host patterns: [11-environments-matrix.md](./11-environments-matrix.md).
