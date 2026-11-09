---
name: oms-aws-service-manager-batch
description: >-
  OMS .NET 8 AWS Batch jobs (RepoSuite/oms-aws-service-manager-batch): Inventory
  Feed, Export Order Items, Reset/Update/Cancel TASK jobs, GenericJob submit
  JSON, SSM DB bootstrap, exit codes, Docker publish, EOM NuGet. Read reference.md
  for full product knowledge.
---

# OMS Batch application repo

**Local path:** `/Users/akashyap/RepoSuite/oms-aws-service-manager-batch`

## When to use this skill

- Implementing or debugging a **Batch container** (not Terraform CE/JQ/JD)
- **SubmitJob** inner JSON, `Ref::` parameters, argv vs env precedence
- **Exit codes** and `BatchExitRetryClassifier` (before changing `evaluateOnExit` in infra)
- **SSM** `ssm_connectionstring` + `connectionstringParams`
- **Docker** publish-then-COPY images; private **Eom.Component.*** feed
- Legacy **ODX / RabbitMQ** parity questions

## Five jobs (quick)

| Job | DLL | Batch param key | EOM? |
|-----|-----|-----------------|------|
| Inventory Feed | `OmsAwsBatch.InventoryFeed.Job.dll` | `inventoryFeedJobJson` | No |
| Export Order Items | `OmsAwsBatch.ExportOrderItems.Job.dll` | `exportOrderItemsJobJson` | Yes |
| Reset Items for Reroute | `OmsAwsBatch.ResetItemsForReroute.Job.dll` | `resetItemsForRerouteJobJson` | Yes |
| Update Item Status | `OmsAwsBatch.UpdateItemStatus.Job.dll` | `updateItemStatusJobJson` | Yes |
| Cancel Items | `OmsAwsBatch.CancelItems.Job.dll` | **`jobParamter`** | Yes + optional SES |

## Non-negotiables

1. **Infra owns** JD, retry, CloudWatch — **this repo owns** exit code integers and runner behavior (`docs/ARCHITECTURE.md`).
2. **Export Order Items:** `settings.taskId` = scheduler task GUID; exit **8** if S3 bucket missing (checked first).
3. **Cancel Items:** orchestrator typo `jobParamter` is intentional.
4. **No RabbitMQ** for inventory / export paths in this repo.

## Commands

```bash
cd RepoSuite/oms-aws-service-manager-batch
dotnet build OmsAwsBatchJobs.sln
dotnet test OmsAwsBatchJobs.sln --filter "TestCategory!=RequiresDocker&TestCategory!=RequiresOmsDatabase"
```

## Full product knowledge

Read **`reference.md`** in this skill folder, or repo copy:  
`superdev-hmm/oms/product-knowledge/01-batch.md` (on branch **OMS**).

## Terraform handoff

After code changes, update stage **B** (+ **D** if metadata changes): skill **oms-infrastructure**.
