# Terraform reference (detailed)

**100% `.tf` inventory:** `oms/product-knowledge/24-infrastructure-complete-reference.md` and `inventories/infrastructure-tf-by-root.md` (**974** files, **62** roots).  
Canonical narrative: `oms/product-knowledge/02-terraform.md`.

## Stage resource ownership

| Stage | Creates in AWS / DB |
|-------|---------------------|
| **A** | `aws_batch_compute_environment`, `aws_batch_job_queue`, Batch service IAM role, platform SSM |
| **C** | Postgres `oms_batch` CE + JQ rows via bastion SSH (`null_resource`) |
| **B** | `aws_batch_job_definition`, task role, log group, job SSM, optional connection SecureString |
| **D** | Postgres `job_definition` catalog row via bastion |

Stage **B** **reads** CE/JQ from **A** (data sources + platform SSM), execution role from ECS cluster remote state.

## Common tfvars

| Variable | Role |
|----------|------|
| `state_bucket` | Remote state bucket |
| `business_divsion` | → SSM `owners` |
| `space`, `environment` | Tenant/env |
| `multitenant`, `master_space`, `master_environment` | Shared VPC/bastion state |
| `batch_shared_name` | Default `servicemanager-scheduled` |
| `jobname` | e.g. `inventory-feed`, `cancel-items` |
| `batch_job_definition` | ECR, Fargate size, command, env, retry, timeout |

Catalog **C/D:** `private_key` or `private_key_path` for bastion (`TF_VAR_private_key` in Harness).

## Remote state examples

| Dependency | Key pattern |
|------------|-------------|
| VPC | `{space}/{env}/infrastructure/vpc/terraform.tfstate` |
| Bastion (C/D) | `…/infrastructure/dboperation/rdsinitpredb/terraform.tfstate` |
| ECS cluster (B) | Used for execution role ARN |

## Batch job application folder map

| Infra folder | App job |
|--------------|---------|
| B tfvars `inventory-feed` | `Jobs/InventoryFeed` |
| B tfvars `cancel-items` | `Jobs/CancelItems` |
| (per `jobname`) | Matching `Jobs/*` + ECR repo name |

## ECS service list

`03-application/01-aws-ecs-service/`:  
01 currencyexchange, 02 efs-fileexplorer, 03 keycloak, 04 minisoft, 05 extensibility, 06 taskscheduler, 07 omsfeed, 08 omsinventoryfeed, 09 taskprocessor, 10 orderfacade, 11 inventoryfacade, 15 configrulemanager, 16 coreapi, 17 coreservice, 18 corepaymentapi, 19 corekekservice, 20 omstaxationfacade, 21 omstaxation.

## Harness

Pipeline YAML: `01-infrastructure/08-core/harness-pipeline-source/oms15-inf.yaml` (and ECS/lambda variants). Backend key template: `<space>/<environment>/…/terraform.tfstate`.

## Step Functions

`06-aws-stepfunction` — may consume `servicemanager_batch_job_state_key` from stage B for IAM ARNs. Workflow docs under `02-servicemanager-scheduled-job/docs/`.

## Cost tags script

`scripts/apply-cost-allocation-tags.py` at repo root.
