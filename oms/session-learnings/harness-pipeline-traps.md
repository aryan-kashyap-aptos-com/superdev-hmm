# Harness and deploy pipeline traps

**Status:** verified  
**Evidence:** DCOMS-29691 App-Deploy inputs, product-knowledge [16](../product-knowledge/16-operations-runbooks.md) + [13](../product-knowledge/13-deployables-catalog.md), harness-related transcripts

## OMS-App-Deploy (Windows pods)

| Input | Gotcha |
|-------|--------|
| `environment_name` | **`pod2`** for pod2-dev registry - not `pod2-dev` |
| `webserver_setup_require` | Must be **`true`** after EC2 terminate / fresh IIS |
| `action` | Run **`plan`** first on unfamiliar recovery |

WinRM stages: content directory, SM setup, robocopy ShopLogic to `D:\content\...\sm`, JobManager deploy on Toronado.

## OMS-DFS-Namespace

| Input | Gotcha |
|-------|--------|
| `dfs_action` | Must be **`create_and_validate`** - typo `creata_and_validate` is invalid |
| When needed | After **new content server hostname** - SM UNC paths break without DFS retarget |

## Batch / ECR two-account

- Images often published in account **`767398067331`**
- Workloads run in tenant account (e.g. **`268173716021`**)
- Query ECR with `--registry-id 767398067331` when QA account list looks empty

## Publish trap

`oms release pipeline` may **skip** ECR publish unless a second run uses **Build Type = Git Tag**.

## Batch Job Manager bootstrap order (short)

From deployment runbook - order matters:

1. Baseline EF migration history (scheduler DB)
2. SSM `…/servicemanagerscheduler/endpoint` = full `https://` URL
3. Step Function stack **before** scheduler ECS
4. Scheduler ECS with `EventBridgeScheduler__*` enabled
5. Publish batch image → job definition stage B
6. UI job + schedule; verify EventBridge + Batch run

## Investigating pipeline failures

Several agent sessions were spent on Harness/terraform apply errors - always capture **sequence ID**, stage name, and whether failure is **WinRM**, **Terraform**, or **ECR pull** before re-running apply.
