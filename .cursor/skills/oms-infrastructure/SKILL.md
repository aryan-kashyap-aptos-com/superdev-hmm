---
name: oms-infrastructure
description: >-
  OMS Terraform monorepo (RepoSuite/oms-infrastructure): VPC/RDS/ECS, Service
  Manager Batch stages A→C→B→D, SSM batch metadata, Harness backends, state
  keys, ECR job definitions. Read reference.md for full product knowledge.
---

# OMS infrastructure (Terraform)

**Local path:** `/Users/akashyap/RepoSuite/oms-infrastructure`

## When to use this skill

- **Apply order**, state keys, or **which folder** to edit (platform vs per-job)
- **SSM paths** for batch platform vs job metadata
- Wiring **ECR image**, `Ref::` command, env vars to **oms-aws-service-manager-batch**
- **ECS service** stack under `01-aws-ecs-service`
- **Harness** / `secrets.tfvars` / `dev.conf` patterns
- **Multitenant** remote state (`master_space`)

## Service Manager Batch (memorize)

```text
A: 02-platform/03-aws-batch/02-aws-batch-servicemanager-platform
C: 02-platform/03-aws-batch/03-aws-batch-servicemanager-catalog-platform-db
B: 03-application/03-aws-batch-job/02-servicemanager-scheduled-job
D: 03-application/03-aws-batch-job/03-servicemanager-batch-catalog-job-db
```

Apply: **A → C → B → D** per jobname (A+C once per `batch_shared_name`).

## SSM (under `/{owners}/{space}/{env}`)

- Platform: `batch/platform/{batch_shared_name}/metadata` (**A**)
- Job: `{jobname}/batch/metadata` (**B**)
- Optional DB: `{jobname}/dbConnStr/connectionstring` (**B**)

`owners` = tfvar **`business_divsion`** (spelling in code).

## Traps

1. Stage **C** is in **02-platform**, not `03-application/04-…`.
2. README folder numbers `03-`/`05-` ≠ on-disk `02-`/`03-` for B/D.
3. Never commit `secrets.tfvars` or `*.conf` backends.
4. **`evaluateOnExit`** must match batch repo exit codes — read `oms-aws-service-manager-batch` skill first.

## Workflow

```bash
cd RepoSuite/oms-infrastructure/<stack>
terraform init -backend-config="dev.conf" -var-file="secrets.tfvars"
terraform plan -var-file="secrets.tfvars"
```

## Full product knowledge

Read **`reference.md`** here, or:  
`superdev-hmm/oms/product-knowledge/02-terraform.md` (branch **OMS**).

## Application handoff

Container behavior, submit JSON, exit codes: skill **oms-aws-service-manager-batch**.
