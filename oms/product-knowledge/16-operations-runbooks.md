# Operations runbooks (distilled for newcomers)

**Audience:** QA, support, devs standing up or debugging feeds and Batch Job Manager.  
**Full source docs live in RepoSuite** — this page is the index + essentials.

---

## Runbook index

| Topic | Canonical file (RepoSuite) | Product knowledge |
|-------|---------------------------|-------------------|
| **Batch Job Manager deploy & traps** | `oms-aws-service-manager-batch/docs/batch-job-manager-deployment-runbook.md` | [07](./07-batch-scheduler-api-ui.md), [13](./13-deployables-catalog.md) |
| **ODX feed pipeline monitor** | `oms/docs/odx-feed-pipeline-monitor-runbook.md` | Below + [08](./08-task-engine-feeds.md) |
| **Batch worker exit codes** | `oms-aws-service-manager-batch/docs/ARCHITECTURE.md` | [01-batch.md](./01-batch.md) |
| **Inventory/feed regression logs** | `oms-aws-service-manager-batch/docs/batch/REGRESSION-TESTS-OBSERVABILITY.md` | [01-batch.md](./01-batch.md) |

---

## Batch Job Manager — five-minute sanity check

From deployment runbook (adjust task/JD names for your `space`/`environment`):

```bash
# Scheduler wired to EventBridge?
aws ecs describe-task-definition --task-definition <prefix>-servicemanagerscheduler-td \
  --region us-east-1 \
  --query "taskDefinition.containerDefinitions[0].environment[?starts_with(name,'EventBridgeScheduler')]" \
  --output table --no-cli-pager

# Active job definition points at real ECR image?
aws batch describe-job-definitions --job-definition-name <prefix>-inventory-feed-jd \
  --status ACTIVE --region us-east-1 \
  --query "reverse(sort_by(jobDefinitions,&revision))[0].[revision,containerProperties.image]" \
  --output text --no-cli-pager

# UI schedules exist in EventBridge?
aws scheduler list-schedules --region us-east-1 \
  --query "Schedules[?contains(Name,'<prefix>')].[Name,State]" --output table --no-cli-pager
```

**Two-account trap:** images often publish in **`767398067331`**; workloads run in tenant account (e.g. **`268173716021`**). Query ECR with `--registry-id 767398067331` when QA account looks empty.

**Publish trap:** `oms release pipeline` may **skip** ECR publish unless second run uses **Build Type = Git Tag**.

---

## Batch Job Manager — env bootstrap order (short)

1. Baseline EF migration history (scheduler DB) — once per env.  
2. SSM `…/servicemanagerscheduler/endpoint` = full **`https://`** URL (via pipeline).  
3. Step Function stack **before** scheduler ECS.  
4. Scheduler ECS with `EventBridgeScheduler__*` enabled.  
5. Publish batch image → apply job definition stage B.  
6. Catalog SQL fix-up if required.  
7. UI: create job + schedule; verify EventBridge + Batch run.

---

## Proxy / URL traps (Site Manager → scheduler)

| Symptom | Cause |
|---------|--------|
| UI calls fail but API works on `execute-api` URL | Custom domain / Route53 mapping wrong |
| Changed `APIGatewayBatchSchedulerURL`, no effect | **15-minute cache** in `InfrastructureSettingRepository` — recycle app pool or wait |
| Empty Publish in pipeline | Branch build without **Git Tag** publish step |

Use API Gateway `get-apis` / `get-domain-name` from runbook § diagnostics.

---

## ODX Feed Pipeline Monitor (legacy queue visibility)

**UI:** Site Manager → **Content → Tasks → ODX Monitor** (`/backadmin/OdxFeedMonitor.aspx`).

**What it is:** Read-only view of **OMS → RabbitMQ → ODX** — tables `odxtasklogging`, `odxfeederror`, `omsfeedexport`, `omsfeedsqueuedorder`. Does **not** replay or fix queues.

| Screen area | Meaning |
|-------------|---------|
| Summary tiles | Counts by task name × state |
| Stuck in queue | Orders in `omsfeedsqueuedorder` > **4 hours** |
| Search | By order ID or **supplier ID** (inventory) |
| Detail timeline | Queued → Started → Done; export stages when `omsfeedexport` exists |

**API:** `/api/OdxFeedMonitor` (Site Manager session).  
**When migrating to Batch:** inventory/export may bypass this path — use CloudWatch + S3 + [01-batch.md](./01-batch.md) for new jobs.

---

## SQL scripts — Batch Job Manager (`oms` repo)

Folder: `SQLChangeScripts/2026.5/`

| Script | Role |
|--------|------|
| `Insert_BatchJobManager_to_ResourcesAndRolesVsResources.sql` | Nav + RBAC for admin page |
| `Insert_APIGatewayBatchSchedulerURL_InfrastructureSetting.sql` | DB setting for proxy base URL |
| `BatchJobManager_Create_oms_batch_scheduled_job.sql` | Schema objects |
| `BatchJobManager_Create_oms_batch_scheduled_job_step.sql` | Step table |
| `BatchJobManager_Alter_oms_batch_*` | Job definition type, schedule bounds |
| `DCOMS-29419-Create_Read_Path_Indexes_ODX_Task_Logging.sql` | ODX monitor performance |

---

## Inventory feed test (from runbook §8)

1. **New path:** omit `settings.JobStepId` — expect success + warning log; no `lastsynced` update.  
2. **Regression:** run **with** valid `jobStepId` — confirm `jobstep.lastsynced` still updates.  
3. Check `oms_batch.job_run` and S3 output.

---

## When to escalate

| Situation | Team / action |
|-----------|----------------|
| Stuck ODX queue, no `odxfeederror` | ODX consumer health / NetOps |
| Batch exit code 4 loop | Transient — check CloudWatch; not config exit 5/8 |
| Scheduler 401 | Keycloak issuer mismatch |
| Terraform catalog FK errors | Run platform catalog stage C before job stage D |

---

## Related

- [03-qa-environments.md](./03-qa-environments.md)  
- [17-workflows-and-step-functions.md](./17-workflows-and-step-functions.md)  
