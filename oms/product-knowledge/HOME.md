# OMS product knowledge — home (read like a Confluence space)

This is the **single written home** for Aptos OMS on AWS on your machine. It is **not** auto-synced to Confluence; copy sections into your team space or link to this repo on the **OMS** git branch when publishing internally.

---

## Where is everything written?

| Location | What lives there |
|----------|------------------|
| **`superdev-hmm/oms/product-knowledge/`** | **All guides below** — the source of truth for this workspace |
| **`superdev-hmm/oms/README.md`** | Short index + RepoSuite paths |
| **`superdev-hmm/.cursor/skills/oms-*`** | Cursor agent entry points (point back to product-knowledge) |
| **`RepoSuite/oms`** | Legacy **application** monorepo (ShopLogic, JobManager, DCEOM, …) |
| **`RepoSuite/oms-infrastructure`** | **Terraform / Harness** — AWS resources |
| **`RepoSuite/oms-aws-service-manager-batch`** | **AWS Batch** worker containers (.NET 8) |

**Rule for newcomers:** Read **this home page** → pick your **role path** → open only the docs you need. You do **not** need to read 974 Terraform files on day one.

---

## Full table of contents

| # | Page | Who it is for |
|---|------|----------------|
| **HOME** | (this file) | Everyone — start here |
| [00-onboarding.md](./00-onboarding.md) | Brand-new to OMS | 20-minute mental model |
| [01-batch.md](./01-batch.md) | Batch developers / SRE | Five AWS Batch jobs |
| [02-terraform.md](./02-terraform.md) | Platform / DevOps | Layers, A→C→B→D, SSM |
| [03-qa-environments.md](./03-qa-environments.md) | QA, explorers | Site Manager, browser, tests |
| [04-deep-repo-scan.md](./04-deep-repo-scan.md) | Staff engineers | Batch + infra second pass |
| [05-oms-estate-map.md](./05-oms-estate-map.md) | Architects | 15 domains, coverage % |
| [06-site-manager-shoplogic.md](./06-site-manager-shoplogic.md) | Admin UI, APIs | Site Manager, ShopLogic, minisoft |
| [07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md) | Batch migration | Job Manager UI + scheduler API |
| [08-task-engine-feeds.md](./08-task-engine-feeds.md) | Ops, integrations | Tasks, feeds, export classes |
| [09-facades-core-edge.md](./09-facades-core-edge.md) | API consumers | Facades, core ECS, auth, edge |
| [10-platform-data-delivery.md](./10-platform-data-delivery.md) | Platform | VPC, RDS, MQ, Harness, Snowflake |
| 11 | [11-environments-matrix.md](./11-environments-matrix.md) | Everyone | URLs, SSM, Harness ECS stages |
| 12 | [12-monorepo-catalog.md](./12-monorepo-catalog.md) | Developers | 133 `oms` folders grouped |
| 13 | [13-deployables-catalog.md](./13-deployables-catalog.md) | DevOps | ECR, pipelines, five-repo stack |
| 14 | [14-glossary-extended.md](./14-glossary-extended.md) | New hires | Extended acronyms |
| 15 | [15-infrastructure-stack-index.md](./15-infrastructure-stack-index.md) | Platform | All **62** Terraform roots |
| 16 | [16-operations-runbooks.md](./16-operations-runbooks.md) | Ops, QA | BJM sanity checks, ODX monitor, SQL |
| 17 | [17-workflows-and-step-functions.md](./17-workflows-and-step-functions.md) | Batch/workflows | SFN, Lambda catalog, multi-step |
| 18 | [18-scheduler-api.md](./18-scheduler-api.md) | Scheduler devs | `oms-aws-job-scheduler` API + EF |
| 19 | [19-ssm-parameter-catalog.md](./19-ssm-parameter-catalog.md) | Platform | All 83 foundation SSM params |
| 20 | [20-harness-pipelines.md](./20-harness-pipelines.md) | DevOps | 4 Harness YAML files |
| 21 | [21-monorepo-folder-index.md](./21-monorepo-folder-index.md) | Everyone | All 133 `oms` top-level folders |
| 22 | [22-batch-repo-complete-reference.md](./22-batch-repo-complete-reference.md) | Batch devs | **100%** batch repo file index |
| 23 | [23-job-scheduler-complete-reference.md](./23-job-scheduler-complete-reference.md) | Scheduler devs | **100%** scheduler repo index |
| 24 | [24-infrastructure-complete-reference.md](./24-infrastructure-complete-reference.md) | Platform | **100%** `974` `.tf` paths |
| 26 | [26-oms-monorepo-complete-reference.md](./26-oms-monorepo-complete-reference.md) | App devs | **100%** `oms` repo (**13,553** files) |
| **Functional** | **[FUNCTIONAL-COVERAGE.md](./FUNCTIONAL-COVERAGE.md)** | Everyone | **Behavior & flows** checklist |
| 27 | [27-functional-cross-repo-flows.md](./27-functional-cross-repo-flows.md) | All devs | BJM → scheduler → Batch end-to-end |
| 28 | [28-functional-oms-monorepo.md](./28-functional-oms-monorepo.md) | App devs | What each `oms` family **does** |
| 29 | [29-functional-batch-jobs.md](./29-functional-batch-jobs.md) | Batch devs | All 5 jobs — business + execution |
| 30 | [30-functional-scheduler-platform.md](./30-functional-scheduler-platform.md) | Scheduler | Catalog, lifecycle, EventBridge |
| 31 | [31-functional-infrastructure-platform.md](./31-functional-infrastructure-platform.md) | Platform | Apply order, ECS/Batch roles |
| 33 | [33-functional-commerce-and-apis.md](./33-functional-commerce-and-apis.md) | Commerce/QA | All Commerce pages + `/api` scenarios |
| 34 | [34-functional-order-services-deep-scan.md](./34-functional-order-services-deep-scan.md) | Integrations | OrderService.asmx, facade, domain services, Confluence |
| **—** | **[COVERAGE.md](./COVERAGE.md)** | Leads | File inventory + links to functional |

**RepoSuite runbooks (full text):** `oms-aws-service-manager-batch/docs/batch-job-manager-deployment-runbook.md`, `oms/docs/odx-feed-pipeline-monitor-runbook.md`.

---

## Repositories (five code + one doc space)

```text
RepoSuite/oms                          Site Manager UI, JobManager, SQL
RepoSuite/oms-aws-job-scheduler        Scheduler API (ECS) — clone if missing locally
RepoSuite/oms-aws-service-manager-batch Batch worker images
RepoSuite/oms-infrastructure           Terraform / Harness
superdev-hmm/oms/product-knowledge/    ← docs you are reading
```

Detail: [13-deployables-catalog.md](./13-deployables-catalog.md).

---

## Role-based reading paths

### I am brand new to OMS

1. [00-onboarding.md](./00-onboarding.md)  
2. [06-site-manager-shoplogic.md](./06-site-manager-shoplogic.md) — what operators see  
3. [03-qa-environments.md](./03-qa-environments.md) — if you will click around in a browser  

### I work on AWS Batch migration

1. [00-onboarding.md](./00-onboarding.md)  
2. [01-batch.md](./01-batch.md) → [02-terraform.md](./02-terraform.md)  
3. [07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md)  
4. [04-deep-repo-scan.md](./04-deep-repo-scan.md)  

### I am platform / Terraform

1. [02-terraform.md](./02-terraform.md)  
2. [10-platform-data-delivery.md](./10-platform-data-delivery.md)  
3. [05-oms-estate-map.md](./05-oms-estate-map.md)  
4. Harness: `oms-infrastructure/01-infrastructure/08-core/harness-pipeline-source/`  

### I support production (on-call)

1. [00-onboarding.md](./00-onboarding.md) — glossary  
2. [01-batch.md](./01-batch.md) — exit codes  
3. [08-task-engine-feeds.md](./08-task-engine-feeds.md) — feeds/tasks  
4. [09-facades-core-edge.md](./09-facades-core-edge.md) — which ECS service does what  

### I need the whole map

1. [05-oms-estate-map.md](./05-oms-estate-map.md)  
2. Then `06`–`14` for the domains you own  
3. [13-deployables-catalog.md](./13-deployables-catalog.md) for ECR/pipelines  

---

## SSM naming pattern (used everywhere)

Prefix: `/{owners}/{space}/{environment}/…`

Built in Terraform as `parameterstoreprefix` (see `01-infrastructure/01-parameterstore/3-local-values.tf`). Examples:

| Prefix fragment | Typical use |
|-----------------|-------------|
| `…/minisoft/endpoint` | Site Manager public URL |
| `…/sm/…` | Site Manager app config |
| `…/servicemanagerscheduler/…` | Batch scheduler API |
| `…/batch/platform/{name}/metadata` | Batch stage A platform |
| `…/{jobname}/batch/metadata` | Batch stage B job |

Spelling note: Terraform variable **`business_divsion`** is intentional in code (typo preserved).

---

## Documentation coverage

See **[COVERAGE.md](./COVERAGE.md)** for the full checklist.

| Measure | % |
|---------|---|
| **Defined product-knowledge scope** | **100%** (26 checklist rows) |
| **All RepoSuite code repos** | **100%** file inventories → `22`–`24`, `26` |
| **Terraform stacks (62)** | **100%** indexed |
| **Foundation SSM (83)** | **100%** cataloged |
| **`oms` top-level folders (133)** | **100%** indexed |
| **Newcomer orient (practical)** | **~94%** |
| **Every source line in all repos** | *out of scope* |

Remaining gaps: live URL matrix per customer, facade **application** repo names off-ECR, ISL side repos.

---

## Publishing to Confluence (optional)

1. Export or copy markdown section-by-section.  
2. Keep **secrets and passwords** out — link to [03-qa-environments.md](./03-qa-environments.md) private patterns instead.  
3. Ask the team if an official space already exists; avoid duplicating conflicting URL lists.

---

## Cursor agents

Skill **`oms-product-knowledge`** → read [00-onboarding.md](./00-onboarding.md) and this HOME page first.
