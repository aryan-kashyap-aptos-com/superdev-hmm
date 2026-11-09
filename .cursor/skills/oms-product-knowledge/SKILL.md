---
name: oms-product-knowledge
description: >-
  OMS on AWS — how batch jobs (oms-aws-service-manager-batch) and Terraform
  (oms-infrastructure) fit together. Use for DCOMS/Batch migrations, Harness
  apply order, exit codes, SSM DB bootstrap, or Service Manager scheduled jobs.
---

# OMS product knowledge (umbrella)

## Repositories

| Repo | Role |
|------|------|
| **oms-aws-service-manager-batch** | .NET 8 **application** code for AWS Batch: inventory feed, export order items, reset reroute, update item status, cancel items. Job definitions / CE / queues live in infra. |
| **oms-infrastructure** | **Terraform** for VPC, RDS, ECS microservices, Batch platform, Step Functions, SQS, API Gateway, Parameter Store, etc. |

Local paths (this machine): `RepoSuite/oms-aws-service-manager-batch`, `RepoSuite/oms-infrastructure`.

## End-to-end: Service Manager → AWS Batch

Legacy Windows Service scheduled .NET jobs are moving to containers on AWS Batch.

```text
Application code (oms-aws-service-manager-batch)
    → Docker image → ECR (deploy pipeline)
Infrastructure (oms-infrastructure)
    → job definition, CE, JQ, retry/evaluateOnExit, CloudWatch logs
    → Toronado / catalog Postgres rows (stages C, D)
Trigger
    → SubmitJob JSON (Ref:: parameter) and/or Step Functions (scheduled job stack)
```

**Apply order (Batch migration, per job):** **A → C → B → D**

| Stage | Stack |
|-------|--------|
| A | `02-platform/03-aws-batch/02-aws-batch-servicemanager-platform` |
| C | `02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db` |
| B | `03-application/03-aws-batch-job/03-servicemanager-scheduled-job` |
| D | `03-application/03-aws-batch-job/05-servicemanager-batch-catalog-job-db` |

## Contract between repos

- **Exit codes** are defined in batch repo (`OmsAwsBatch.Infrastructure.Diagnostics.*ExitCode`). Infra **`evaluateOnExit`** must stay aligned — see batch `docs/ARCHITECTURE.md`.
- **DB connection:** jobs use **`SsmDatabaseConnectionBootstrap`** → `ConnectionStrings:Database` from `ssm_connectionstring` + `connectionstringParams`. Batch **job role** needs `ssm:GetParameter` (+ KMS if applicable).
- **Submit payload:** Batch job definition uses `Ref::<paramName>`; inner JSON carries `configXml`, `jobStepId`, filters/settings per job. Examples under batch `docs/batch/*.example.json`.
- **No RabbitMQ** in the new inventory feed path; export order items likewise in-process (DCOMS-29257 pattern).

## Infra layout (high level)

```text
oms-infrastructure/
  01-infrastructure/   # VPC, RDS, MQ, Beanstalk, peering, …
  02-platform/         # Shared Batch CE/JQ, Service Manager platform
  03-application/      # ECS services, per-job Batch, Lambda, Cognito, SQS, …
```

## Deeper skills

- Batch jobs, build, tests, observability → **oms-aws-service-manager-batch** skill.
- Terraform paths, SSM metadata keys, state keys → **oms-infrastructure** skill.

## Commands cheat sheet

```bash
# Batch app repo
cd RepoSuite/oms-aws-service-manager-batch
dotnet build OmsAwsBatchJobs.sln
dotnet test OmsAwsBatchJobs.sln --filter "TestCategory!=RequiresDocker&TestCategory!=RequiresOmsDatabase"

# Infra (typical; use env-specific backend + secrets)
cd RepoSuite/oms-infrastructure/<stack-folder>
terraform init -backend-config="dev.conf" -var-file="secrets.tfvars"
terraform plan -var-file="secrets.tfvars"
```

When changing retry behavior or alarms, always cross-check **exit code tables** in batch docs against the job definition Terraform.
