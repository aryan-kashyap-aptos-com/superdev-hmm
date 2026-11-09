# OMS branch — Cursor skills & product knowledge

This branch holds **project skills** and pointers for Order Management System (OMS) work on Aptos Retail AWS estates.

## Local repo paths (RepoSuite)

| Repo | Path |
|------|------|
| Legacy OMS application (monorepo) | `/Users/akashyap/RepoSuite/oms` |
| Batch scheduler API | `/Users/akashyap/RepoSuite/oms-aws-job-scheduler` |
| Batch job code (.NET 8) | `/Users/akashyap/RepoSuite/oms-aws-service-manager-batch` |
| Terraform / Harness infra | `/Users/akashyap/RepoSuite/oms-infrastructure` |

## Product knowledge (Confluence-style space)

**Home page:** [product-knowledge/HOME.md](./product-knowledge/HOME.md) — table of contents, where docs are written, role paths, coverage %.

All guides live under **`superdev-hmm/oms/product-knowledge/`** (not in Bitbucket OMS repos). Copy sections to Confluence when your team publishes.

| # | Document | Contents |
|---|----------|----------|
| **HOME** | [HOME.md](./product-knowledge/HOME.md) | **Start here** — index, five repos, newcomer paths |
| **0** | [00-onboarding.md](./product-knowledge/00-onboarding.md) | 20-min mental model, glossary, diagram |
| 1 | [01-batch.md](./product-knowledge/01-batch.md) | Batch jobs, JSON payloads, exit codes, Docker (with plain-English intros) |
| 2 | [02-terraform.md](./product-knowledge/02-terraform.md) | Terraform layers, A→C→B→D, SSM/state, ECR wiring (with analogies) |
| 3 | [03-qa-environments.md](./product-knowledge/03-qa-environments.md) | **QA** — Site Manager / backadmin, pod URLs, browser login, many services per env |
| 4 | [04-deep-repo-scan.md](./product-knowledge/04-deep-repo-scan.md) | **Deep scan** — per-job flows, Step Functions, catalog DB, infra traps, gaps |
| 5 | [05-oms-estate-map.md](./product-knowledge/05-oms-estate-map.md) | **Estate map** — 15 domains, ECS index, coverage % |
| 6 | [06-site-manager-shoplogic.md](./product-knowledge/06-site-manager-shoplogic.md) | Site Manager, backadmin, ShopLogic, minisoft |
| 7 | [07-batch-scheduler-api-ui.md](./product-knowledge/07-batch-scheduler-api-ui.md) | Batch Job Manager UI + scheduler API |
| 8 | [08-task-engine-feeds.md](./product-knowledge/08-task-engine-feeds.md) | Tasks, feeds, JobManager, migration map |
| 9 | [09-facades-core-edge.md](./product-knowledge/09-facades-core-edge.md) | Facades, core ECS, Keycloak, edge |
| 10 | [10-platform-data-delivery.md](./product-knowledge/10-platform-data-delivery.md) | VPC, RDS, MQ, Harness, Snowflake |
| 11 | [11-environments-matrix.md](./product-knowledge/11-environments-matrix.md) | Environments, URLs, SSM, Harness |
| 12 | [12-monorepo-catalog.md](./product-knowledge/12-monorepo-catalog.md) | `oms` repo — all folders grouped |
| 13 | [13-deployables-catalog.md](./product-knowledge/13-deployables-catalog.md) | ECR, pipelines, four-repo map |
| 14 | [14-glossary-extended.md](./product-knowledge/14-glossary-extended.md) | Extended glossary |
| 15 | [15-infrastructure-stack-index.md](./product-knowledge/15-infrastructure-stack-index.md) | All 60 Terraform stacks |
| 16 | [16-operations-runbooks.md](./product-knowledge/16-operations-runbooks.md) | Ops: BJM, ODX monitor, SQL |
| 17 | [17-workflows-and-step-functions.md](./product-knowledge/17-workflows-and-step-functions.md) | Step Functions + workflows |
| 18–21 | [18](./product-knowledge/18-scheduler-api.md) … [21](./product-knowledge/21-monorepo-folder-index.md) | Scheduler API, SSM, Harness, folder index |
| 22–24 | [22](./product-knowledge/22-batch-repo-complete-reference.md) … [24](./product-knowledge/24-infrastructure-complete-reference.md) | **100%** inventories (batch, scheduler, infra) |
| 26 | [26-oms-monorepo-complete-reference.md](./product-knowledge/26-oms-monorepo-complete-reference.md) | **100%** `oms` monorepo inventory |
| Functional | [FUNCTIONAL-COVERAGE.md](./product-knowledge/FUNCTIONAL-COVERAGE.md) | Behavior guides `27`–`31` |
| — | [COVERAGE.md](./product-knowledge/COVERAGE.md) | **100% scope** checklist |

## Project skills (Cursor agents)

| Skill | When to use |
|-------|-------------|
| [oms-product-knowledge](../.cursor/skills/oms-product-knowledge/SKILL.md) | Start here — links to full docs |
| [oms-aws-service-manager-batch](../.cursor/skills/oms-aws-service-manager-batch/SKILL.md) | Batch app; see `reference.md` in same folder |
| [oms-infrastructure](../.cursor/skills/oms-infrastructure/SKILL.md) | Terraform; see `reference.md` in same folder |

## Cursor skills inventory

Bundled manifest: [cursor-skills-inventory.json](./cursor-skills-inventory.json) (personal skills under `~/.cursor/skills-cursor/`).

Atlassian plugins (when enabled): `~/.cursor/plugins/cache/cursor-public/atlassian/.../skills/` — Jira, Confluence, sprint dashboard, etc.
