# Product knowledge coverage — what “100%” means here

**Honest limit:** No doc set can be **100% of all source code** (~101 `.csproj`, ~974 `.tf`, 133 monorepo folders × thousands of files).  
**This space targets 100% of the [defined scope](#defined-scope) below** — everything a **newcomer + platform + Batch migration** engineer needs **without opening Bitbucket blind**.

**Home:** [HOME.md](./HOME.md)  
**Functional (behavior & flows):** [FUNCTIONAL-COVERAGE.md](./FUNCTIONAL-COVERAGE.md) — guides `27`–`31`.

---

## Defined scope (checklist)

| # | Scope item | Doc | Status |
|---|------------|-----|--------|
| 1 | Mental model & **five** repos | [00](./00-onboarding.md), [HOME](./HOME.md) | ✅ |
| 2 | Five Batch jobs + JSON + exit codes | [01](./01-batch.md), [04](./04-deep-repo-scan.md) | ✅ |
| 3 | Terraform layers A→C→B→D | [02](./02-terraform.md) | ✅ |
| 4 | QA / Site Manager browser | [03](./03-qa-environments.md) | ✅ |
| 5 | 15 architecture domains | [05](./05-oms-estate-map.md) | ✅ |
| 6 | Site Manager / ShopLogic | [06](./06-site-manager-shoplogic.md) | ✅ |
| 7 | Batch Job Manager UI + proxy | [07](./07-batch-scheduler-api-ui.md) | ✅ |
| 8 | Tasks / feeds / ODX | [08](./08-task-engine-feeds.md) | ✅ |
| 9 | Facades / core ECS / auth | [09](./09-facades-core-edge.md) | ✅ |
| 10 | VPC / RDS / MQ / bootstrap | [10](./10-platform-data-delivery.md) | ✅ |
| 11 | Environments & Harness ECS list | [11](./11-environments-matrix.md) | ✅ |
| 12 | `oms` monorepo families | [12](./12-monorepo-catalog.md) | ✅ |
| 13 | ECR, pipelines, 5 repos | [13](./13-deployables-catalog.md) | ✅ |
| 14 | Extended glossary | [14](./14-glossary-extended.md) | ✅ |
| 15 | **60** Terraform stack index | [15](./15-infrastructure-stack-index.md) | ✅ |
| 16 | Ops runbooks (distilled) | [16](./16-operations-runbooks.md) | ✅ |
| 17 | Step Functions / workflows | [17](./17-workflows-and-step-functions.md) | ✅ |
| 18 | **`oms-aws-job-scheduler`** API | [18](./18-scheduler-api.md) | ✅ (repo cloned locally) |
| 19 | **83** foundation SSM parameters | [19](./19-ssm-parameter-catalog.md) | ✅ |
| 20 | **4** Harness YAML pipelines | [20](./20-harness-pipelines.md) | ✅ |
| 21 | **133** monorepo folder index | [21](./21-monorepo-folder-index.md) | ✅ |
| 22 | RepoSuite runbooks linked | batch BJM runbook, ODX monitor | ✅ |
| 23 | **100%** batch repo inventory | [22](./22-batch-repo-complete-reference.md) + `inventories/` | ✅ |
| 24 | **100%** job scheduler inventory | [23](./23-job-scheduler-complete-reference.md) + `inventories/` | ✅ |
| 25 | **100%** infrastructure `.tf` inventory | [24](./24-infrastructure-complete-reference.md) + `inventories/` | ✅ |
| 26 | **100%** `oms` monorepo inventory | [26](./26-oms-monorepo-complete-reference.md) + `inventories/oms-*` | ✅ |

---

## Per-repo coverage (file inventory = 100%)

| Repo | Files inventoried | Reference page | Source scan / semantics |
|------|-------------------|----------------|-------------------------|
| `oms-aws-service-manager-batch` | **565** files, **480** `.cs` | [22](./22-batch-repo-complete-reference.md) | **100%** index; behavior docs in [01](./01-batch.md) |
| `oms-aws-job-scheduler` | **114** files, **98** `.cs` | [23](./23-job-scheduler-complete-reference.md) | **100%** index; APIs in [18](./18-scheduler-api.md) |
| `oms-infrastructure` | **974** `.tf`, **62** roots | [24](./24-infrastructure-complete-reference.md) | **100%** path index; [15](./15-infrastructure-stack-index.md) narrative |
| **`oms`** (monorepo) | **13,553** files, **5,489** `.cs`, **101** `.csproj` | [26](./26-oms-monorepo-complete-reference.md) | **100%** index; **functional:** [28](./28-functional-oms-monorepo.md) + [inventories/oms-functional-by-folder.md](./inventories/oms-functional-by-folder.md) |

---

## Functional coverage (all repos)

| Repo | Functional guide | Checklist |
|------|------------------|-----------|
| Cross-repo | [27-functional-cross-repo-flows.md](./27-functional-cross-repo-flows.md) | [FUNCTIONAL-COVERAGE.md](./FUNCTIONAL-COVERAGE.md) **F1** |
| `oms` | [28-functional-oms-monorepo.md](./28-functional-oms-monorepo.md) | **F2–F4** |
| Batch | [29-functional-batch-jobs.md](./29-functional-batch-jobs.md) | **F5** |
| Scheduler | [30-functional-scheduler-platform.md](./30-functional-scheduler-platform.md) | **F6** |
| Infrastructure | [31-functional-infrastructure-platform.md](./31-functional-infrastructure-platform.md) | **F7–F10** |

**Functional checklist:** **13/13** areas in [FUNCTIONAL-COVERAGE.md](./FUNCTIONAL-COVERAGE.md).

---

## Coverage percentages (definitions)

| Metric | % | Meaning |
|--------|---|---------|
| **Product knowledge scope (table above)** | **100%** | **26** checklist rows |
| **All four RepoSuite code repos — file inventory** | **100%** | `oms`, batch, scheduler, infra |
| **Newcomer “read and orient”** | **~94%** | Can name repos, stacks, APIs, main URLs pattern |
| **Terraform roots documented** | **100%** | 60/60 in [15](./15-infrastructure-stack-index.md) |
| **Foundation SSM parameters** | **100%** | 83/83 named in [19](./19-ssm-parameter-catalog.md) |
| **`oms` top-level folders** | **100%** | [21](./21-monorepo-folder-index.md) + [26](./26-oms-monorepo-complete-reference.md) |
| **`oms` every tracked file path** | **100%** | `inventories/oms-all-files.txt` |
| **Harness YAML in git** | **100%** | 4/4 in [20](./20-harness-pipelines.md) |
| **Batch + scheduler + infra file inventory** | **100%** | Machine lists under `inventories/` |
| **Batch + scheduler behavioral depth** | **~95%** | All entrypoints, exit codes, API routes documented |
| **Infrastructure behavioral depth** | **~90%** | Every `.tf` path; resource semantics via stack index + A→D |
| **Facade microservice source repos** | **~75%** | ECR `imagePath` table in [09](./09-facades-core-edge.md) + [13](./13-deployables-catalog.md); Bitbucket repo names via ECR grep |
| **Per-retailer live URL matrix** | **~35%** | Pod dev SM verified; Confluence links in [11](./11-environments-matrix.md) |
| **Every `.cs` / `.tf` line** | **not scoped** | Use IDE + tests for depth |

---

## RepoSuite clones (this machine)

| Repo | Path |
|------|------|
| oms | `RepoSuite/oms` |
| oms-infrastructure | `RepoSuite/oms-infrastructure` |
| oms-aws-service-manager-batch | `RepoSuite/oms-aws-service-manager-batch` |
| oms-aws-job-scheduler | `RepoSuite/oms-aws-job-scheduler` |
| **Docs** | `superdev-hmm/oms/product-knowledge/` |

---

## Out of scope (by design)

- Production passwords, Harness secrets, live tfvars  
- Customer-specific Confluence URL grids  
- ISL / Shippo repos in `RepoSuite/isl-*` (separate products)  
- Line-by-line API reference for all ShopLogic `.aspx` pages  

---

## If something is missing

1. Search [HOME](./HOME.md) TOC.  
2. Grep `product-knowledge/` for a keyword.  
3. Add a row to this checklist + new `NN-*.md` — keep **one topic per file**.

---

## Related

Update [HOME.md](./HOME.md) coverage table when this file changes.
