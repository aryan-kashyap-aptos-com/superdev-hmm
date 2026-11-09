---
name: oms-infrastructure
description: >-
  RepoSuite oms-infrastructure — Terraform for OMS AWS (VPC, RDS, ECS, Batch
  platform, scheduled jobs, API Gateway, SQS, Cognito). Use for Harness apply
  order, state keys, SSM batch metadata, and linking to batch app repo.
---

# oms-infrastructure

**Path:** `/Users/akashyap/RepoSuite/oms-infrastructure`

Terraform monorepo organized by **layer**, then **AWS product**, then **stack folder** (each with its own backend state).

## Top-level layers

| Layer | Purpose |
|-------|---------|
| **01-infrastructure** | Foundation: VPC, RDS subdivisions, Amazon MQ, Elastic Beanstalk, peering, transit gateway, VPC endpoints, user groups, … |
| **02-platform** | Shared platform — notably **03-aws-batch** (compute environments, job queues, Service Manager catalog bootstrap). |
| **03-application** | Workloads: **ECS services** (`01-aws-ecs-service/*`), **Batch per-job** (`03-aws-batch-job/*`), Lambda, Cognito, Step Functions, SQS, EventBridge, API Gateway, Parameter Store, Route53, Snowflake/DMS, … |

## AWS Batch — Service Manager migration

Four-stage pipeline (Windows scheduled services → Batch):

```text
A: 02-platform/03-aws-batch/02-aws-batch-servicemanager-platform
   Shared CE + JQ + SSM platform metadata (once per batch_shared_name)

C: 02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db
   Postgres catalog rows for CE + JQ

B: 03-application/03-aws-batch-job/03-servicemanager-scheduled-job
   Job definition per jobname

D: 03-application/03-aws-batch-job/05-servicemanager-batch-catalog-job-db
   Postgres job_definition row per job
```

**Apply order:** **A → C → B → D** (per `jobname` for B and D).

Legacy SQL batch queue: `02-platform/03-aws-batch/01-aws-batch-sql-job` (superseded by Service Manager platform pattern).

### SSM contracts

- Platform: `/{owners}/{space}/{env}/batch/platform/{batch_shared_name}/metadata`
- Job: `/{owners}/{space}/{env}/{jobname}/batch/metadata`

### State key patterns (examples)

| Stack | Pattern |
|-------|---------|
| Service Manager platform | `…/servicemanager-batch-platform/{batch_shared_name}/terraform.tfstate` |
| Catalog platform DB | `…/servicemanager-batch-catalog-platform/{batch_shared_name}/terraform.tfstate` |
| Scheduled job | `…/servicemanager-scheduled-job/{jobname}/terraform.tfstate` |
| Catalog job DB | `…/servicemanager-batch-catalog-job/{jobname}/terraform.tfstate` |

DDL helper (optional, once per env): `02-platform/03-aws-batch/scripts/aws_batch_scheduler_model.sql`.

## Link to application repo

Container images and entrypoints come from **oms-aws-service-manager-batch**. This repo owns:

- Job definition (CPU, memory, command `Ref::`, environment for SSM DB vars)
- `retryStrategy`, `timeout`, `evaluateOnExit` aligned with app exit codes
- `logConfiguration` → CloudWatch log groups

When changing retry rules, read exit code tables in batch `docs/ARCHITECTURE.md` first.

## ECS application services (03-application/01-aws-ecs-service)

Named folders include (non-exhaustive): `orderfacade`, `inventoryfacade`, `omsfeed`, `omsinventoryfeed`, `taskprocessor`, `taskscheduler`, `coreservice`, `omstaxation`, `configrulemanager`, … — each is its own Terraform root with Harness-style layout.

## Typical Terraform workflow

Per stack directory:

```bash
terraform init -backend-config="<env>.conf" -var-file="secrets.tfvars"
terraform validate
terraform plan -var-file="secrets.tfvars"
terraform apply -var-file="secrets.tfvars"
```

Use `terraform fmt` before commit. Secrets stay in `secrets.tfvars` (not in git).

## Related docs in repo

- `03-application/03-aws-batch-job/README.md` — migration overview
- `03-application/03-aws-batch-job/02-servicemanager-scheduled-job/docs/*` — Step Functions, deployment, external steps
- `02-platform/03-aws-batch/README.md` — platform stacks table

## Agent guidance

- Prefer **smallest stack** that owns the resource (don’t edit VPC when fixing one job definition).
- Respect **apply order** for new Batch jobs: platform before job definition before catalog DB rows.
- Cross-repo PRs: image tag / job definition revision in infra + code change in batch repo should ship together.
