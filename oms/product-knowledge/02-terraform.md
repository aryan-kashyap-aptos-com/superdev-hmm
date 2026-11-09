# Product knowledge — OMS infrastructure (`oms-infrastructure`)

> **New to OMS?** Read [00-onboarding.md](./00-onboarding.md) first.

**Repo:** `RepoSuite/oms-infrastructure`  
**100% `.tf` inventory:** [24-infrastructure-complete-reference.md](./24-infrastructure-complete-reference.md) (**974** files, **62** roots).  
**Role:** **Infrastructure as code** — networks, databases, APIs on ECS, and the AWS Batch “plumbing” (queues, job templates, IAM, logs). Does **not** contain the .NET business logic that runs inside containers.

**Pair with:** [01-batch.md](./01-batch.md) for what those containers actually *do*.

### In plain English

Think of this repo as **blueprints for AWS**. Each subfolder is one blueprint stack (its own Terraform state). Harness (or you locally) runs `terraform apply` to create or update real resources. When someone says “deploy inventory feed to dev,” that usually means **apply stage B** with the right image tag **and** the batch repo has already published that image to ECR.

---

## Layer model

Three layers — **foundation → shared platform → specific apps**:

| Layer | Analogy | Examples |
|-------|---------|----------|
| **01-infrastructure** | Land, power, water | VPC, RDS PostgreSQL, message broker, bastion host for DB scripts |
| **02-platform** | Shared building | ECS cluster, **shared Batch queue**, scheduler DB sync for queues |
| **03-application** | Tenants & equipment | Each microservice (order API), **each Batch job definition**, Lambdas |

```text
01-infrastructure/     VPC, RDS, MQ, peering, bastion, KMS, …
02-platform/           ECS cluster, AWS Batch platform (stages A + C), …
03-application/        ECS facades, per-job Batch (stages B + D), API GW, …
```

**Convention:** `{layer}/{product}/{numbered-stack}/` — each folder is its own Terraform root (`terraform init -backend-config=…`).

---

## Service Manager Batch — pipeline A → C → B → D

**Plain English:** Adding a new scheduled job to AWS Batch is a **four-step Terraform rollout**, not one button.

| Stage | One-line explanation |
|-------|----------------------|
| **A** | Create the **shared parking lot** — Batch compute + queue for many jobs |
| **C** | Tell the **OMS scheduler database** “this queue exists” (Postgres rows) |
| **B** | Register **this job’s recipe** — Docker image, CPU, command, env, logs, retries |
| **D** | Tell the **scheduler database** “this job definition exists” |

**Apply order:** **A → C → B → D**. Do A+C once per environment “platform”; do B+D **once per job** (e.g. `inventory-feed`, `cancel-items`).

> **Folder naming trap:** READMEs sometimes say `03-servicemanager-scheduled-job` / `05-catalog-job-db`. On disk use **`02-servicemanager-scheduled-job`** and **`03-servicemanager-batch-catalog-job-db`**. Stage **C** is under **`02-platform`**, not `03-application/04-…`.

| Stage | Path | Creates |
|-------|------|---------|
| **A** | `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform` | Fargate **compute environment**, **job queue**, Batch **service IAM role**, **SSM platform metadata** |
| **C** | `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db` | SSH to migration bastion → **Postgres** `oms_batch` rows for CE + JQ (no AWS Batch API resources) |
| **B** | `03-application/03-aws-batch-job/02-servicemanager-scheduled-job` | **Job definition**, **task role**, **log group**, **SSM job metadata**, optional DB connection SecureString |
| **D** | `03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db` | Bastion → **Postgres `job_definition`** row from stage B metadata |

**Legacy (superseded for SM jobs):**

- Platform: `02-platform/03-aws-batch/01-aws-batch-sql-job`
- Per job: `03-application/03-aws-batch-job/01-sql-job`

**DDL (optional, once per env):** `02-platform/03-aws-batch/scripts/aws_batch_scheduler_model.sql`

---

## SSM contracts

**Plain English:** **SSM Parameter Store** is where AWS keeps **configuration the containers need at runtime** (often including *where to find* the database connection string). Terraform **writes** metadata parameters when you apply A and B; the .NET job **reads** them using env vars like `ssm_connectionstring`.

Prefix: `/{owners}/{space}/{environment}` — `owners` comes from variable **`business_divsion`** (spelling is intentional in code).

| Path | Written by | Contents |
|------|------------|----------|
| `…/batch/platform/{batch_shared_name}/metadata` | **A** | CE/JQ ARNs, names, schema version, service role |
| `…/{jobname}/batch/metadata` | **B** | JD ARN/revision, image, CPU/mem, command, env, queue, roles |
| `…/{jobname}/dbConnStr/connectionstring` | **B** (optional) | Full DB connection SecureString |
| `…/aws-db-pgsql/…` | RDS stacks | Read by B for connection fragments |

Stage **D** reads job metadata JSON and upserts catalog SQL (`03-servicemanager-batch-catalog-job-db/docs/catalog-db-sync.md`).

App containers consume:

- `ssm_connectionstring` → parameter **name** pointing at connection material
- `connectionstringParams` → suffix
- See batch doc for in-process merge to `ConnectionStrings:Database`

---

## State keys (examples)

Bucket typically `oms-deployment-state` (via `state_bucket` var). Keys prefix `{space}/{environment}/…`.

| Stack | Suffix pattern |
|-------|----------------|
| Platform A | `…/servicemanager-batch-platform/{batch_shared_name}/terraform.tfstate` |
| Catalog platform C | `…/servicemanager-batch-catalog-platform/{batch_shared_name}/terraform.tfstate` |
| Scheduled job B | `…/application/aws-batch/servicemanager-scheduled-job/{jobname}/terraform.tfstate` |
| Catalog job D | `…/application/aws-batch/servicemanager-batch-catalog-job-db/{jobname}/terraform.tfstate` |

**Multitenant:** VPC/bastion remote state may use `master_space` / `master_environment` while app resources use `space` / `environment`.

---

## Terraform workflow (per stack)

```bash
cd RepoSuite/oms-infrastructure/<stack-path>
terraform init -backend-config="dev.conf" -var-file="secrets.tfvars"
terraform validate
terraform plan -var-file="secrets.tfvars"
terraform apply -var-file="secrets.tfvars"
```

| File | Notes |
|------|--------|
| `*.conf` | Backend bucket/key — **gitignored**, local or Harness |
| `secrets.tfvars` | **gitignored** — secrets |
| `config.tfvars.example` | Committed structure, non-secret defaults |

**Harness:** Samples in `01-infrastructure/08-core/harness-pipeline-source/` (`oms15-inf.yaml`, etc.). Catalog stages C/D need **`TF_VAR_private_key`** (PEM for bastion SSH).

---

## Stage B ↔ application repo

`batch_job_definition` in tfvars wires the running container:

| Tfvars field | App repo |
|--------------|----------|
| `ecr_repository` | Image built from `Jobs/<Job>/Dockerfile` |
| `container_image_tag` | Release tag — ship with code |
| `runner_command` | e.g. `dotnet`, `/app/OmsAwsBatch.InventoryFeed.Job.dll` |
| `container_command_override` | `["Ref::inventoryFeedJobJson"]` or `Ref::jobParamter` |
| Environment block | `ssm_connectionstring`, `BATCH_JOB_KEY`, job-specific `__` keys |
| `retry_strategy` / timeouts | Must align with `*ExitCode` + `BatchExitRetryClassifier` |

**Example ECR repos (from examples):**

- `oms-aws-service-manager-batch-inventory-feed`
- `oms-aws-service-manager-batch-cancel-items`

**Example registry:** `767398067331.dkr.ecr.us-east-1.amazonaws.com`

Inventory example command pattern: `dotnet /app/InventoryFeed.dll`, `BATCH_JOB_KEY=inventory-feed`.

---

## `03-application/03-aws-batch-job` folders

| Folder | Role |
|--------|------|
| `01-sql-job` | Legacy SQL Batch job stack |
| `02-servicemanager-scheduled-job` | **Stage B** |
| `03-servicemanager-batch-catalog-job-db` | **Stage D** |
| `04-servicemanager-batch-catalog-platform-db` | Placeholder (keypair only) — **not** stage C |

---

## `01-infrastructure` highlights

| Area | Folders |
|------|---------|
| Network | `02-vpc-infrastructure`, `05-vpc-peering/*`, `11-vpc-endpoints` |
| Data | `03-rds-database-infrastructure` (master + subdivision), `06-database-operation/01-rds-init` (bastion for C/D) |
| Messaging | `04-awsmq-broker-infrastructure` |
| Shared legacy | `08-core` (Harness pipeline source, DMS, monitoring) |
| Security | `00-aws-kms`, `09-usergroup` |

---

## `02-platform` highlights

| Area | Folders |
|------|---------|
| ECS | `01-ecs-cluster` — cluster, execution role, discovery |
| Batch | `03-aws-batch` — sql-job, **servicemanager platform**, **catalog platform db** |
| Web | `02-s3-staticweb` |
| Lambda | `04-aws-lambda-layer` |

---

## ECS microservices (`03-application/01-aws-ecs-service`)

Independent Terraform root per numbered folder, including:

`currencyexchange`, `efs-fileexplorer`, `keycloak`, `minisoft`, `extensibility`, `taskscheduler`, `omsfeed`, `omsinventoryfeed`, `taskprocessor`, `orderfacade`, `inventoryfacade`, `configrulemanager`, `coreapi`, `coreservice`, `corepaymentapi`, `corekekservice`, `omstaxationfacade`, `omstaxation`, …

These are **long-running services**, not Batch jobs. Batch inventory/export jobs may still read the same OMS database as facades.

---

## Other `03-application` stacks

| Folder | Purpose |
|--------|---------|
| `06-aws-stepfunction` | Workflows; can reference stage B state for `batch_job_role_arn` |
| `04-oms-providers` | Shared modules (API GW, Step Functions, parameter store vars) |
| `05-aws-cognito` | Auth; SES identity outputs may feed Batch Cancel job |
| `07-aws-sqs`, `08-aws-event-bridge-pipes`, `09-aws-eventbus` | Async integration |
| `10-aws-api-gateway`, `11-aws-parameterstore`, `12-core-route53` | Edge & config |
| `13-snowflake` | DMS / Snowflake setup |

---

## Step Functions & multi-step Batch

Docs under `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/docs/`:

- `workflow-stepfunctions.md`
- `workflow-stack-split.md`
- `workflow-external-step-jobs.md`
- `servicemanager-batch-deployment.md`

`workflow_runtime_profiles` maps profile keys to **per-step ECR repos** (same registry/tag conventions as single-job B).

---

## Root `scripts/`

`apply-cost-allocation-tags.py` — injects cost tags (`owners`/`Owner`, `space`/`Space`, `environment`/`Environment`) into `.tf` `common_tags` merges (skips `08-core`).

---

## Agent checklist — new Batch job

1. Implement job in **oms-aws-service-manager-batch** (exit codes, README, example JSON).
2. Build/push **ECR** image.
3. Apply **A** (if new `batch_shared_name`) → **C** → **B** with new `jobname` → **D**.
4. Wire scheduler / Step Functions to queue ARN + JD name from SSM metadata.
5. Verify CloudWatch log group and `evaluateOnExit` against batch exit table.

---

## Agent gotchas

1. Match **`business_divsion`** spelling in tfvars.
2. Do not use `03-application/04-servicemanager-batch-catalog-platform-db` for stage C.
3. Backend + `secrets.tfvars` are never committed.
4. Ship **infra tag + app image** together when behavior changes.
5. Cross-repo PRs: Terraform job definition + .NET exit code changes must land coordinated.
