# Workflows, Step Functions, and multi-step Batch

**Audience:** Anyone asking why **EventBridge** starts **Step Functions** instead of Batch directly.  
**Prerequisites:** [01-batch.md](./01-batch.md), [07-batch-scheduler-api-ui.md](./07-batch-scheduler-api-ui.md).

---

## Two ways Batch gets triggered

| Path | Who submits Batch | Typical use |
|------|-------------------|-------------|
| **Scheduler UI / API** | EventBridge Scheduler → Step Functions → `submitJob.sync` | Scheduled Service Manager jobs with catalog in `oms_batch` |
| **Direct SubmitJob** | Lambda, manual CLI, old integrators | One-off or non-workflow jobs |
| **Step workflow (multi-step)** | Step Functions **Map** over catalog steps | Ordered steps, each a different image/profile |

The **scheduler API does not** call `batch:SubmitJob` for UI schedules — Step Functions does ([batch runbook](RepoSuite/oms-aws-service-manager-batch/docs/batch-job-manager-deployment-runbook.md)).

---

## Step Functions flow (Terraform)

**Stack:** `03-application/06-aws-stepfunction`  
**Module:** `modules/05-workflow-batch-orchestration/workflow_orchestration.asl.tftpl`

```text
EventBridge Scheduler  (cron from workflow_schedules in tfvars)
        │ StartExecution { "workflowId": "..." }
        ▼
Step Functions
        │ Lambda: LoadCatalog (Postgres workflow + steps)
        ▼
Choice / Map (MaxConcurrency: 1)
        │ each step: batch:submitJob.sync
        ▼
AWS Batch container
```

**IAM note:** State machine needs permission on rule `StepFunctionsGetEventsForBatchJobsRule` (see module `main.tf`).

---

## Catalog Lambda (`02-aws-lambda`)

- Reads **Postgres** tables (`workflow`, `workflow_step`, …).  
- Returns ordered **SubmitJob** payloads (PascalCase keys for ASL).  
- Uses Lambda request id for unique Batch job names.  
- **psycopg2** layer from `02-platform/04-aws-lambda-layer`.

Deploy: `oms15-lambda.yaml` → `03-application/02-aws-lambda`.

---

## Worker steps from *other* repositories

Doc: `03-aws-batch-job/02-servicemanager-scheduled-job/docs/workflow-external-step-jobs.md`

| Concept | Meaning |
|---------|---------|
| `runtime_profile_key` | Postgres column linking a step to a **profile** in Terraform |
| `workflow_runtime_profiles` | tfvars map: profile → **ECR repo**, command, `Ref::` params, CPU/mem |
| Container env | `WORKFLOW_ID`, `STEP_KEY`, `RUN_ID`, `ENVIRONMENT_DETAIL` injected by catalog Lambda |

Inventory / product import steps may live in **separate repos** — only job-specific logic; platform owns orchestration.

---

## Job definition name vs revision

Step Functions input uses **`JobDefinition.$": "$.JobDefinition"`** from catalog — **not** the stored `aws_job_definition_revision` column alone (catalog metadata).

Implication: after publishing a new image, update **catalog + active JD name** so executions pick up the right revision (runbook §5–10).

---

## Manual test execution

```json
{ "workflowId": "<scheduled job id or workflow key>" }
```

Start on state machine ARN from Terraform output. Cannot override job definition in input — catalog builds the payload.

---

## Relationship to Service Manager Batch jobs (five jobs)

The five jobs in **`oms-aws-service-manager-batch`** are **one step = one container**. They use:

- Stage **B** job definitions (`inventory-feed`, `cancel-items`, …)  
- Generic submit JSON ([01-batch.md](./01-batch.md))  
- Optional registration in `workflow_runtime_profiles` for multi-step workflows

---

## Deploy order (new environment)

1. Batch platform **A → C**  
2. Lambda catalog + layers  
3. **06-aws-stepfunction** (if `isWorkflowBatchOrchestrationDeployment`)  
4. **22-servicemanagerscheduler** with EventBridge enabled  
5. Per-job **B → D** and ECR images  

Full checklist: [16-operations-runbooks.md](./16-operations-runbooks.md).

---

## Related

- [04-deep-repo-scan.md](./04-deep-repo-scan.md)  
- [15-infrastructure-stack-index.md](./15-infrastructure-stack-index.md)  
