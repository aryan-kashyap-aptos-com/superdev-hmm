# Harness pipelines (in-repo YAML)

**Audience:** DevOps tracing “which pipeline deploys what?”  
**Path:** `oms-infrastructure/01-infrastructure/08-core/harness-pipeline-source/`

Four pipeline definitions are committed (names vary per Harness project import):

| File | Pipeline id (example) | Scope |
|------|----------------------|--------|
| `oms15-inf.yaml` | infrastructure stages | Foundation Terraform |
| `oms15-ECS.yaml` | `hox15-clops-ecs` | ECS cluster + 9 services |
| `oms15-lambda.yaml` | lambda stages | `02-aws-lambda` variants |
| `oms15-core.yaml` | legacy EOM | `projects/eom-terraform-master/*` |

**Repo connector:** `hoxbitbucket` → `oms-infrastructure.git` + `folderPath` per stage.

**Common variables:** `aws_region`, `business_divsion`, `space`, `environment`, `bucket_state_location`, `commit`.

---

## `oms15-inf.yaml` stages (Terraform roots)

| Stage | folderPath |
|-------|------------|
| AWSKMSPlan/Apply | `01-infrastructure/00-aws-kms` |
| ParameterStorePlan/Apply | `01-infrastructure/01-parameterstore` |
| VPCPlan/Apply | `01-infrastructure/02-vpc-infrastructure` |
| RDSDatabasePlan/Apply | `01-infrastructure/03-rds-database-infrastructure` |
| AWSMQBrokerPlan/Apply | `01-infrastructure/04-awsmq-broker-infrastructure` |

State keys inline in YAML, e.g. `…/infrastructure/aws-kms/terraform.tfstate`.

---

## `oms15-ECS.yaml` stages

| Deploy stage | Terraform folder | ecs_service_name (example) |
|--------------|------------------|----------------------------|
| (platform) | `02-platform/01-ecs-cluster` | cluster |
| keycloak_deploy | `03-application/01-aws-ecs-service/03-keycloak` | keycloak |
| minisoft_deploy | `04-minisoft` | minisoft |
| extensibility_deploy | `05-extensibility` | extensibility |
| taskscheduler_deploy | `06-taskscheduler` | taskscheduler |
| omsfeed_deploy | `07-omsfeed` | omsfeed |
| omsinventoryfeed_deploy | `08-omsinventoryfeed` | omsinventoryfeed |
| taskprocessor_deploy | `09-taskprocessor` | taskprocessor |
| orderfacade_deploy | `10-orderfacade` | orderfacade |
| inventoryfacade_deploy | `11-inventoryfacade` | inventoryfacade |

**Not in this file:** `15`–`22` (coreapi, taxation, **servicemanagerscheduler**) — separate CD pipelines (see batch runbook: `OMS-DEV-AWS-ECS-SERVICE-CD`, `OMSDEVAWSECSSERVICESHAREDCD`).

Example Harness variables: `minisoft_cname`, `order_facade_cname`, `inventory_facade_cname`, `taskscheduler_cname`, `keycloak_repo`.

---

## `oms15-lambda.yaml` stages

| Deploy stage | Purpose (folder still `03-application/02-aws-lambda`) |
|--------------|--------------------------------------------------------|
| clientsync_deploy | Client sync function |
| clearerrlogtable_deploy | Error log maintenance |
| ordercomplstatus_deploy | Order completion status |
| torooverduealert_deploy | Toronado overdue alert |

Each stage: TerraformPlan + TerraformApply against `02-aws-lambda` with different inline tfvars (function identity).

Also references `02-platform/04-aws-lambda-layer` in earlier platform stage (read YAML for layer publish).

---

## `oms15-core.yaml` (legacy)

Stages under `01-infrastructure/08-core/projects/eom-terraform-master/`:

- tf_state_s3, tf_state_dynamodb, iam, vpc, dhcp, groups, s3_logs, sqlserver, content, services, services_alb, apiserver_lc/asg, **sitemanager_lc/asg**, app, sftp, …

Use when estate still has **EC2/ASG Site Manager** footprint — parallel to modern **ECS minisoft** path.

---

## Batch / Step Functions pipelines (not in these four files)

Documented in **`oms-aws-service-manager-batch/docs/batch-job-manager-deployment-runbook.md`**:

| Pipeline name (example) | Deploys |
|---------------------------|---------|
| `oms release pipeline` | ECR images (oms, batch, scheduler) |
| `OMS-DEV-SERVICE-MANAGER-BATCH-CD` | Step Function + Batch JD stages |
| `OMS-DEV-AWS-ECS-SERVICE-CD` | servicemanagerscheduler |
| `OMSDEVAWSECSSERVICESHAREDCD` | Scheduler image tag |

---

## Related

- [11-environments-matrix.md](./11-environments-matrix.md)  
- [13-deployables-catalog.md](./13-deployables-catalog.md)  
- [15-infrastructure-stack-index.md](./15-infrastructure-stack-index.md)  
