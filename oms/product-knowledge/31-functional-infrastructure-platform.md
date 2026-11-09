# Functional guide — infrastructure platform

**Repo:** `oms-infrastructure`  
**Path inventory:** [24-infrastructure-complete-reference.md](./24-infrastructure-complete-reference.md) (**62** roots, **974** `.tf`).  
**Narrative:** [02-terraform.md](./02-terraform.md), [10-platform-data-delivery.md](./10-platform-data-delivery.md).

---

## What “apply” means functionally

Each Terraform root is a **contract** with AWS (and sometimes Postgres via bastion). Applying creates or updates **real resources** consumed by ECS tasks, Batch jobs, and operators.

| Layer | Functional outcome after apply |
|-------|-------------------------------|
| **01-infrastructure** | Tenants can **exist** on AWS: network, secrets names, database, MQ, DNS prerequisites |
| **02-platform** | Shared **ECS cluster**, Batch **parking lot**, Lambda layers |
| **03-application** | **Runnable services**: minisoft, facades, scheduler, per-job Batch JD, API GW, SFN |

---

## Greenfield sequence (functional)

```text
1. oms15-inf (KMS → parameterstore → VPC → RDS → MQ)
2. RDS init / SQL baselines (06-database-operation — bastion)
3. oms15-ECS or per-service CD (Keycloak → minisoft → feeds → facades…)
4. Batch A → C (platform CE/JQ + Postgres catalog rows)
5. servicemanagerscheduler ECS + API GW route + SSM URL
6. Step Functions stack (06-aws-stepfunction)
7. Per job: Batch B → D (image must exist in ECR first)
8. SM SQL + toggle modernization + BJM smoke
```

Harness files: [20-harness-pipelines.md](./20-harness-pipelines.md).

---

## Batch A → C → B → D (functional)

| Stage | Operator-visible effect |
|-------|-------------------------|
| **A** | New environments can **submit** Batch jobs to a shared queue on Fargate |
| **C** | Scheduler UI **lists** the same CE/JQ names AWS has |
| **B** | A specific job appears in AWS console with correct **image, command, env, logs** |
| **D** | Scheduler UI can **pick** that job definition when building schedules |

**B depends on A:** job definition data-sources read platform SSM from stage A.  
**D depends on B:** catalog SQL reads job metadata written by B.

Job definition command must pass **SubmitJob JSON** into container ([29-functional-batch-jobs.md](./29-functional-batch-jobs.md)).

---

## ECS services (functional roles)

| Stack folder | Runtime role |
|--------------|----------------|
| `04-minisoft` | **Site Manager** — human admin UI |
| `06-taskscheduler` | Enqueues/schedules legacy tasks |
| `09-taskprocessor` | Executes tasks from queue |
| `07-omsfeed` / `08-omsinventoryfeed` | Feed workers (ECS; migrating to Batch for SM jobs) |
| `10-orderfacade` / `11-inventoryfacade` | Partner **HTTP APIs** |
| `16-coreapi` / `17-coreservice` | Core commerce APIs |
| `03-keycloak` | **Identity** issuer for facades + scheduler JWT |
| `22-servicemanagerscheduler` | **Batch catalog API** |
| `10-aws-api-gateway` | Edge routing to internal ALBs |

Image sources: [09-facades-core-edge.md](./09-facades-core-edge.md), [13-deployables-catalog.md](./13-deployables-catalog.md).

---

## SSM as runtime contract

Foundation parameters ([19-ssm-parameter-catalog.md](./19-ssm-parameter-catalog.md)) expose:

- Public URLs (`sitemanager_endpoint`, facade CNAMEs)  
- DB host fragments, feature flags  
- Batch platform/job metadata JSON  

**Apps read at startup** — changing SSM without redeploying may still require task restart to pick up new values (depends on app caching).

---

## Step Functions & Lambda (functional)

| Piece | Role |
|-------|------|
| `06-aws-stepfunction` | Orchestrates **multi-step** Batch with `submitJob.sync` |
| Catalog Lambda | Loads workflow steps from Postgres → ASL input |
| EventBridge rule | Starts SFN on schedule from tfvars `workflow_schedules` |

Worker containers may receive `WORKFLOW_ID`, `STEP_KEY`, `RUN_ID` env ([17](./17-workflows-and-step-functions.md)).

---

## Snowflake / analytics (optional roots)

| Root | Function |
|------|----------|
| `13-snowflake/01-dms-setup` | DMS replication plumbing toward lake |
| `13-snowflake/02-snowflake-setup` | Snowflake tables, pipes, merge tasks |

Not required for core OMS order path; estate-specific.

---

## Legacy `08-core`

Hundreds of `.tf` files under **`eom-terraform-master`** — pre-container AWS patterns (ASG, NLB). **`oms15-core.yaml`** still targets subsets. New estates favor **`01-infrastructure` + `03-application`** numbered stacks.

---

## Failure modes (functional)

| Symptom | Likely cause |
|---------|----------------|
| BJM 403 | Modernization off in **OMS DB**, not infra |
| Scheduler 502 | ECS task unhealthy, wrong JWT issuer, DB `SearchPath` |
| Batch success, old behavior | JD points at stale **image digest** |
| Step never runs | EventBridge disabled on scheduler **or** SFN IAM |
| Terraform plan fails remote state | Wrong `space`/`environment` or peering not applied |

---

## Related

- [27-functional-cross-repo-flows.md](./27-functional-cross-repo-flows.md)  
- [15-infrastructure-stack-index.md](./15-infrastructure-stack-index.md)  
- [16-operations-runbooks.md](./16-operations-runbooks.md)
