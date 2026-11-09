# OMS estate map — split by domain (master scan)

**Repos checked out on `master` (2026-11-09):**

| Repo | Path | Scale (indicative) |
|------|------|-------------------|
| **oms** (legacy monorepo) | `RepoSuite/oms` | **100%** inventory — 13,553 files, 5,489 `.cs` → [26](./26-oms-monorepo-complete-reference.md) |
| **oms-infrastructure** | `RepoSuite/oms-infrastructure` | ~974 `.tf` files, ~155 numbered stack folders |
| **oms-aws-job-scheduler** | `RepoSuite/oms-aws-job-scheduler` | Scheduler API, `oms_batch` EF |
| **oms-aws-service-manager-batch** | `RepoSuite/oms-aws-service-manager-batch` | 5 Batch jobs + shared infra lib |
| **superdev-hmm/oms** | docs + Cursor skills only | not runtime source |

**New on infra `master` since last scan:** ECS stack `22-servicemanagerscheduler` (Batch scheduler API on Fargate, Keycloak JWT, optional EventBridge Scheduler IAM).

---

## How to read this doc

Each **domain** = a slice you can own docs/skills for. Columns:

- **Infra stack** — Terraform under `oms-infrastructure`
- **App source** — where behavior likely lives (may be **another** Bitbucket repo for container-only services)
- **Doc status** — what exists in `superdev-hmm/oms/product-knowledge/` today

---

## Domain split (recommended)

### A. Site Manager & admin UI

| | |
|---|---|
| **What** | Operator UI: `/backadmin/*`, commerce, users, releases, React bundles |
| **Infra** | `04-minisoft` (SSM `sitemanager_*`, `minisoft_*` endpoints), `12-core-route53`, `01-parameterstore` |
| **App** | `ShopVisible.Core.ShopLogic`, `DCEOM.Backadmin.UI`, `ShopVisible.Core.Shoplogic.*.React` |
| **Doc** | [06-site-manager-shoplogic.md](./06-site-manager-shoplogic.md), [03-qa-environments.md](./03-qa-environments.md) |

### B. ShopLogic API & Web API layer

| | |
|---|---|
| **What** | HTTP APIs backing admin and integrations |
| **Infra** | Often colocated with minisoft / ALB; API Gateway on other services |
| **App** | `EOM.ShopLogicApi`, `EOM.ShopLogicServices*`, `DCEOM.WebApi` (incl. `BatchSchedulerProxyController`) |
| **Doc** | [06-site-manager-shoplogic.md](./06-site-manager-shoplogic.md) |

### C. Batch Job Manager (UI → scheduler API)

| | |
|---|---|
| **What** | Admin UI to manage AWS Batch jobs; proxy via ShopLogic |
| **Infra** | SSM `APIGatewayBatchSchedulerURL`; ties to domain **D** |
| **App** | `Shopvisible.Core.Shoplogic.BatchJobManager.Frontend.React`, SQL seed scripts, proxy in `DCEOM.WebApi` |
| **Doc** | [07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md) |

### D. Service Manager Scheduler API (container)

| | |
|---|---|
| **What** | REST scheduler catalog (`/api/v1/*`); Postgres `SearchPath` for batch scheduler schema |
| **Infra** | `01-aws-ecs-service/22-servicemanagerscheduler` |
| **App** | **Likely separate image repo** (not found as a top-level folder in `RepoSuite/oms` on this scan — search Bitbucket for `oms-aws-job-scheduler` or similar) |
| **Doc** | [07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md) |

### E. AWS Batch workers (.NET 8)

| | |
|---|---|
| **What** | Five Fargate jobs: inventory, export orders, reset, update status, cancel |
| **Infra** | `03-aws-batch-job/*`, platform `02-platform/03-aws-batch/*` |
| **App** | `oms-aws-service-manager-batch` |
| **Doc** | [01-batch.md](./01-batch.md), [04-deep-repo-scan.md](./04-deep-repo-scan.md) **strong** |

### F. Batch platform & orchestration

| | |
|---|---|
| **What** | A→C→B→D, `oms_batch` Postgres catalog, Step Functions workflows |
| **Infra** | `06-aws-stepfunction`, `02-aws-lambda` (catalog loader), stages A/C/B/D |
| **App** | Submit payloads from scheduler/Lambda; workers in domain **E** |
| **Doc** | [02-terraform.md](./02-terraform.md), [04-deep-repo-scan.md](./04-deep-repo-scan.md) **strong** |

### G. Task engine (legacy Windows path → AWS path)

| | |
|---|---|
| **What** | Scheduled tasks, ODX handlers, Toronado job steps |
| **Infra** | `06-taskscheduler`, `09-taskprocessor` ECS |
| **App** | `ShopVisible.JobManager.*`, `ShopVisible.Core.Scheduler`, `ShopVisible.Core.Tasks`, `DCEOM.Toronado.*` |
| **Doc** | [08-task-engine-feeds.md](./08-task-engine-feeds.md) |

### H. Feeds & exports (in-monorepo + ECS)

| | |
|---|---|
| **What** | Inventory/order feed pipelines (legacy + ECS) |
| **Infra** | `07-omsfeed`, `08-omsinventoryfeed` |
| **App** | `ShopVisible.Core.ExportClasses`, `ShopVisible.Core.FeedClasses`, `ShopVisible.Feeds.*` |
| **Doc** | [08-task-engine-feeds.md](./08-task-engine-feeds.md), [01-batch.md](./01-batch.md) |

### I. Domain facades (order / inventory API)

| | |
|---|---|
| **What** | External-style APIs for order/inventory |
| **Infra** | `10-orderfacade`, `11-inventoryfacade` |
| **App** | **Probably not** in `RepoSuite/oms` root listing — dedicated facade repos / images |
| **Doc** | [09-facades-core-edge.md](./09-facades-core-edge.md) |

### J. Core commerce services

| | |
|---|---|
| **What** | Core APIs, payments, taxation, config rules |
| **Infra** | `16-coreapi`, `17-coreservice`, `18-corepaymentapi`, `19-corekekservice`, `20-omstaxationfacade`, `21-omstaxation`, `15-configrulemanager` |
| **App** | Mix of `DCEOM.*`, `ShopVisible.API`, component libs; many images external |
| **Doc** | [09-facades-core-edge.md](./09-facades-core-edge.md) |

### K. Identity & edge

| | |
|---|---|
| **What** | Keycloak, Cognito, API Gateway, Route53 |
| **Infra** | `03-keycloak`, `05-aws-cognito`, `10-aws-api-gateway`, `12-core-route53` |
| **App** | Realm config in infra; apps use JWT (see scheduler `jwt_validissuer`) |
| **Doc** | [09-facades-core-edge.md](./09-facades-core-edge.md) |

### L. Data & persistence

| | |
|---|---|
| **What** | Aurora Postgres, migrations, bastion DDL |
| **Infra** | `03-rds-database-infrastructure`, `06-database-operation/01-rds-init`, Snowflake `13-snowflake` |
| **App** | `DCEOM.DataAccess*`, `SQLChangeScripts`, `DBMigrationScript` |
| **Doc** | [10-platform-data-delivery.md](./10-platform-data-delivery.md), [01-batch.md](./01-batch.md) |

### M. Async integration plane

| | |
|---|---|
| **What** | MQ, SQS, EventBridge, pipes, DLQ |
| **Infra** | `04-awsmq-broker-infrastructure`, `07-aws-sqs`, `08-aws-event-bridge-pipes`, `09-aws-eventbus`, `10-aws-dlq` |
| **App** | Consumers in JobManager / feeds (monorepo) |
| **Doc** | [10-platform-data-delivery.md](./10-platform-data-delivery.md) |

### N. Shared platform & delivery

| | |
|---|---|
| **What** | VPC, ECS cluster, EFS/minisoft mount, Harness pipelines, cost tags |
| **Infra** | `01-infrastructure/*`, `02-platform/*`, `01-infrastructure/08-core/harness-pipeline-source/*.yaml` |
| **App** | Jenkins scripts in `oms/Jenkins Build Scripts` |
| **Doc** | [10-platform-data-delivery.md](./10-platform-data-delivery.md), [02-terraform.md](./02-terraform.md) |

### O. Extensibility & adjunct

| | |
|---|---|
| **What** | Custom rules, file explorer, currency, extensibility API |
| **Infra** | `05-extensibility`, `02-efs-fileexplorer`, `01-currencyexchange` |
| **App** | `DCEOM.Plugins`, extensibility-related `DCEOM.Services` |
| **Doc** | [09-facades-core-edge.md](./09-facades-core-edge.md), [10-platform-data-delivery.md](./10-platform-data-delivery.md) |

---

## ECS service index (infra folder → domain)

| Folder | Service | Domain |
|--------|---------|--------|
| 04-minisoft | Site Manager host | A |
| 22-servicemanagerscheduler | Batch scheduler API | D |
| 06-taskscheduler | Task scheduler | G |
| 09-taskprocessor | Task processor | G |
| 07-omsfeed / 08-omsinventoryfeed | Feed workers | H |
| 10-orderfacade / 11-inventoryfacade | Facades | I |
| 16–21, 15 | Core / tax / config | J |
| 03-keycloak | IdP | K |
| 05-extensibility, 02-efs-fileexplorer, 01-currencyexchange | Adjunct | O |

---

## Coverage estimate (updated after full doc split)

**Method:** 15 domains; each has a dedicated page in `06`–`10` where applicable. See [HOME.md](./HOME.md) for roll-up.

| Domain | Scan depth (repos) | Written guide (newcomer-ready) |
|--------|-------------------|-------------------------------|
| A Site Manager | ~50% | ~75% ([06](./06-site-manager-shoplogic.md)) |
| B ShopLogic API | ~25% | ~60% (within 06) |
| C Batch Job Manager UI | ~55% | ~75% ([07](./07-batch-scheduler-api-ui.md)) |
| D Scheduler API | ~90% | ~85% ([18](./18-scheduler-api.md)) |
| E Batch workers | ~92% | ~90% ([01](./01-batch.md), [04](./04-deep-repo-scan.md)) |
| F Batch platform / SFN | ~75% | ~75% ([02](./02-terraform.md), [04](./04-deep-repo-scan.md)) |
| G Task engine | ~35% | ~65% ([08](./08-task-engine-feeds.md)) |
| H Feeds | ~35% | ~65% ([08](./08-task-engine-feeds.md)) |
| I Facades | ~35% | ~70% ([09](./09-facades-core-edge.md) — ECR `imagePath` table) |
| J Core services | ~15% | ~50% ([09](./09-facades-core-edge.md)) |
| K Identity / edge | ~25% | ~55% ([09](./09-facades-core-edge.md)) |
| L Data | ~30% | ~60% ([10](./10-platform-data-delivery.md)) |
| M Async | ~20% | ~55% ([10](./10-platform-data-delivery.md)) |
| N Platform / Harness | ~40% | ~70% ([10](./10-platform-data-delivery.md)) |
| O Extensibility | ~15% | ~45% ([09](./09-facades-core-edge.md)) |

**Aggregate (equal weight per domain):**

- **Architecture map (can name repos + stacks):** ~**42%** of full estate code volume.
- **Defined product-knowledge scope (`00`–`21` + runbooks):** **100%** — see [COVERAGE.md](./COVERAGE.md).
- **Newcomer documentation (read and orient):** ~**94%**.
- **Terraform stack index (60 roots):** **100%** ([15](./15-infrastructure-stack-index.md)).
- **Foundation SSM (83 params):** **100%** ([19](./19-ssm-parameter-catalog.md)).
- **`oms` top-level folders (133):** **100%** ([21](./21-monorepo-folder-index.md)).
- **`oms` monorepo grouped catalog:** ~**60%** ([12](./12-monorepo-catalog.md)).
- **Deploy/ECR/pipeline map:** ~**85%** ([13](./13-deployables-catalog.md), [20](./20-harness-pipelines.md)).

**Functional guides:** [FUNCTIONAL-COVERAGE.md](./FUNCTIONAL-COVERAGE.md) (`27`–`31`).  
**Gaps (explicit):** Bitbucket **repo slug** per ECR image, full per-tenant URL grid (Confluence — [11](./11-environments-matrix.md)), every `.aspx` page spec.
