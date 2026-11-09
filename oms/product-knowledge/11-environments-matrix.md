# OMS environments — naming, URLs, and SSM

**Audience:** New QA, new developers, anyone asking “what host do I use?”  
**Prerequisites:** [HOME.md](./HOME.md), [06-site-manager-shoplogic.md](./06-site-manager-shoplogic.md)

---

## How environments are named in code

Three Terraform/Harness dimensions appear everywhere:

| Variable | Meaning | Example |
|----------|---------|---------|
| `business_divsion` | Owner tag (typo in code) | `oms` |
| `space` | Tenant / estate slice | `pod`, `indusknights`, `hox-clops2` |
| `environment` | Stage | `dev`, `qa`, `uat`, `prod` |

**AWS resource name prefix:** often `{owners}-{space}-{environment}-…` (e.g. `oms-pod-dev-inventory-feed-jd`).

**SSM prefix:** `/{owners}/{space}/{environment}/…` — see [HOME.md](./HOME.md).

---

## Confluence authority (live URL grids)

**Do not mirror full per-tenant tables in git** — they change when estates are added or consolidated. Use these pages as source of truth and link from runbooks:

| Page | Confluence | Use for |
|------|------------|---------|
| **OMS Developer Environments** | [DEV space — page 136326736](https://aptos.atlassian.net/wiki/spaces/DEV/pages/136326736/OMS+Developer+Environments) | Dev connectivity, corporate network requirement |
| **OMS Environments** | [DC space — page 139690636](https://aptos.atlassian.net/wiki/spaces/DC/pages/139690636/OMS+Environments) | NetOps / PS canonical environment list |
| **AO/OMS-QA Environments** | [AO space — page 147918624](https://aptos.atlassian.net/wiki/spaces/AO/pages/147918624/AO+OMS-QA+Environments) | AO + OMS QA matrix (points to Aptos ONE dev envs) |
| **Aptos ONE Consolidated QA Envs** | [SR space — page 852000769](https://aptos.atlassian.net/wiki/spaces/SR/pages/852000769/Aptos+ONE+Consolidated+QA+Envs) | Consolidation strategy |
| **Harness + new env** | [personal — OMS Environment Deployment Guide](https://aptos.atlassian.net/wiki/spaces/~712020eaa98996890f47078a7834ea0feaeae8/pages/303333377/OMS+Environment+Deployment+Guide) | Pipeline order for greenfield deploy |

This product-knowledge folder documents **patterns + one verified pod dev URL**; Confluence holds the **full matrix**.

---

## Hostname patterns (public URLs)

Patterns vary by estate; these are the ones seen in **this workspace’s** docs and samples:

```text
# Site Manager (common eom dev pattern)
https://oms-<tenant>-sm.<stage>.eom.aptos.io/backadmin/...

# Alternate marketing / legacy (Harness sample)
https://<something>.aptos.io

# Facades (Harness hox sample — your estate may differ)
https://order-facade-api-<estate>.aptos.io
https://inventory-facade-api-<estate>.aptos.io
```

**Pod dev Site Manager (verified for QA on this machine):**

| Surface | URL |
|---------|-----|
| Login | `https://oms-pod-dev-sm.dev.eom.aptos.io/backadmin/login.aspx` |
| Commerce hub | `…/backadmin/commerce.aspx` |

Credentials: [03-qa-environments.md](./03-qa-environments.md) — **never commit passwords**.

---

## Where the canonical URL is stored (not in git)

| Setting | SSM path pattern | Written by |
|---------|------------------|------------|
| Site Manager public URL | `…/sm/…` + `sitemanager_endpoint` (parameter store stack) | Terraform stage parameter store |
| Minisoft container endpoint | `…/minisoft/endpoint` | Same |
| Order facade | `…/orderfacade/…` | Per-service deploy |
| Inventory facade | `…/inventoryfacade/…` | Per-service deploy |
| Task scheduler | `…/taskscheduler/…` | ECS deploy |
| Service Manager scheduler API | `…/servicemanagerscheduler/…` | ECS `22-servicemanagerscheduler` |
| Batch platform metadata | `…/batch/platform/{batch_shared_name}/metadata` | Batch stage A |
| Per Batch job | `…/{jobname}/batch/metadata` | Batch stage B |

**Operator tip:** In AWS Console → Systems Manager → Parameter Store, search `/{your owners}/{space}/{env}/`.

RDS init SQL templates reference placeholders like `sitemanger_endpoint_replace` — real values are injected at estate bootstrap (`01-infrastructure/06-database-operation/01-rds-init/database-metadata/`).

---

## Harness pipelines (which YAML deploys what)

Under `oms-infrastructure/01-infrastructure/08-core/harness-pipeline-source/`:

| File | Deploys |
|------|---------|
| `oms15-inf.yaml` | Foundation: KMS, **parameter store**, VPC, RDS, MQ, bastion, … |
| `oms15-ECS.yaml` | ECS services (see table below) |
| `oms15-lambda.yaml` | Lambda stacks (`03-application/02-aws-lambda`) |
| `oms15-core.yaml` | Legacy **eom-terraform-master** paths (older AWS layout) |

**oms15-ECS.yaml** stages (folder paths):

| Stage | Terraform folder | Service |
|-------|------------------|---------|
| keycloak_deploy | `03-keycloak` | Keycloak |
| minisoft_deploy | `04-minisoft` | Site Manager |
| extensibility_deploy | `05-extensibility` | Extensibility API |
| taskscheduler_deploy | `06-taskscheduler` | Task scheduler |
| omsfeed_deploy | `07-omsfeed` | Order feeds |
| omsinventoryfeed_deploy | `08-omsinventoryfeed` | Inventory feeds |
| taskprocessor_deploy | `09-taskprocessor` | Task processor |
| orderfacade_deploy | `10-orderfacade` | Order facade |
| inventoryfacade_deploy | `11-inventoryfacade` | Inventory facade |

**Not in this YAML (still in repo):** `15`–`22` stacks (coreapi, taxation, **servicemanagerscheduler**, …) — likely separate pipeline or newer stages; search Harness for `folderPath: 03-application/01-aws-ecs-service/`.

---

## Batch example resources (pod-style names)

From `batch_catalog_upsert.sql` sample (account `268173716021`, region `us-east-1`):

| Resource | Example name |
|----------|----------------|
| Compute environment | `oms-pod-dev-servicemanager-scheduled-ce` |
| Job queue | `oms-pod-dev-servicemanager-scheduled-jq` |
| Job definition | `oms-pod-dev-inventory-feed-jd` |
| ECR image | `767398067331.dkr.ecr.us-east-1.amazonaws.com/oms-aws-service-manager-batch-inventory-feed:latest` |

Your account IDs and tags will differ — use **SSM job metadata** after stage B apply.

---

## Site Manager feature flags (SSM)

| Parameter | Path suffix | Notes |
|-----------|-------------|--------|
| Batch Job Manager enabled | `…/sm/batchjobmanager/enabled` | **Site Manager owns value after create** — Terraform `ignore_changes`; toggle in UI for non-prod |
| Authentication mode | `…/appconfig/sitemanager/authenticationmode` | Cognito vs legacy |
| iZenda reporting | `…/sm` izenda params | Reporting embed |
| Strategy / analytics | `sitemanager_strategy_*` | Optional modules |

See Terraform comments in `4-03-parameterstore-resource.tf` around `sitemanager_batchjobmanager_enable` — production refuses the feature regardless of flag.

---

## QA: mapping host → `qa-tester` site

| Browser site key | Base URL | Login path |
|------------------|----------|------------|
| `oms-pod-dev-sitemanager` | `https://oms-pod-dev-sm.dev.eom.aptos.io/` | `/backadmin/login.aspx` |

Configure in `qa-tester/environments.local.md` (gitignored).

---

## Environment checklist (new hire)

| # | Question | Where to find answer |
|---|----------|----------------------|
| 1 | What is my `space` / `environment`? | Team Confluence or Harness pipeline variables |
| 2 | Site Manager URL? | SSM `sitemanager_endpoint` or team matrix |
| 3 | Can I use Batch Job Manager? | SSM `…/sm/batchjobmanager/enabled` + non-prod |
| 4 | Which Batch jobs exist? | SSM `…/batch/platform/…/metadata` + per-job metadata |
| 5 | Who do I ask for URLs? | Estate owner / Confluence “OMS environments” |

---

## Related pages

- [03-qa-environments.md](./03-qa-environments.md) — browser testing  
- [13-deployables-catalog.md](./13-deployables-catalog.md) — every deployable + image hints  
- [10-platform-data-delivery.md](./10-platform-data-delivery.md) — bootstrap order  
