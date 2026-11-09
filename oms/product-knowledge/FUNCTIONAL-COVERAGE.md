# Functional coverage — behavior & flows (not file lists)

**Companion to:** [COVERAGE.md](./COVERAGE.md) (inventories + pages).  
**Goal:** Every **operator and developer action** maps to a documented flow.

---

## Checklist

| # | Functional area | Guide | Status |
|---|-----------------|-------|--------|
| F1 | Cross-repo flows (BJM, Batch, SM) | [27](./27-functional-cross-repo-flows.md) | ✅ |
| F2 | `oms` monorepo — all families + 133 folders | [28](./28-functional-oms-monorepo.md), [inventories/oms-functional-by-folder.md](./inventories/oms-functional-by-folder.md) | ✅ |
| F3 | Site Manager / ShopLogic / BJM UI | [06](./06-site-manager-shoplogic.md) + F2 | ✅ |
| F4 | Task engine, Toronado, ODX legacy | [08](./08-task-engine-feeds.md) + F2 | ✅ |
| F5 | Five Batch jobs (business + technical) | [29](./29-functional-batch-jobs.md), [01](./01-batch.md) | ✅ |
| F6 | Scheduler catalog + API usage | [30](./30-functional-scheduler-platform.md), [18](./18-scheduler-api.md) | ✅ |
| F7 | Terraform apply + runtime contracts | [31](./31-functional-infrastructure-platform.md), [02](./02-terraform.md) | ✅ |
| F8 | Step Functions / workflows | [17](./17-workflows-and-step-functions.md) + F1 | ✅ |
| F9 | Facades, ECS, auth | [09](./09-facades-core-edge.md) | ✅ |
| F10 | Platform (VPC, RDS, MQ, SSM) | [10](./10-platform-data-delivery.md) + F7 | ✅ |
| F11 | QA / environments | [03](./03-qa-environments.md), [11](./11-environments-matrix.md) | ✅ |
| F12 | Ops runbooks | [16](./16-operations-runbooks.md) | ✅ |
| F13 | 15 architecture domains map | [05](./05-oms-estate-map.md) | ✅ |
| F14 | **Commerce UI + `DCEOM.WebApi` scenarios** | [33](./33-functional-commerce-and-apis.md) | ✅ |
| F15 | **Order services deep scan (ASMx, facade, domain, Confluence)** | [34](./34-functional-order-services-deep-scan.md) | ✅ |

**Functional scope:** **15/15** rows above have a primary guide.

---

## Per-repo functional depth

| Repo | Functional guide | Approx. depth |
|------|------------------|---------------|
| `oms` | [28](./28-functional-oms-monorepo.md) | **100%** folders; **~85%** key user journeys |
| `oms-aws-service-manager-batch` | [29](./29-functional-batch-jobs.md) | **100%** of 5 jobs |
| `oms-aws-job-scheduler` | [30](./30-functional-scheduler-platform.md) | **100%** API surface + lifecycle |
| `oms-infrastructure` | [31](./31-functional-infrastructure-platform.md) | **100%** roots + A→D + ECS roles |

---

## Start here

| If you need… | Open |
|--------------|------|
| End-to-end Batch Job Manager | [27](./27-functional-cross-repo-flows.md) |
| “What does this folder do?” | [inventories/oms-functional-by-folder.md](./inventories/oms-functional-by-folder.md) |
| Deploy new Batch job | [31](./31-functional-infrastructure-platform.md) → [29](./29-functional-batch-jobs.md) |
