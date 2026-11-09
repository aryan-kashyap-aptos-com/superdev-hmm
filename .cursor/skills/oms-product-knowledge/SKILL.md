---
name: oms-product-knowledge
description: >-
  OMS on AWS — start here. Batch app repo then Terraform infra repo, A→C→B→D
  pipeline, SSM contracts, legacy ODX migration. Points to deep product knowledge
  in oms/product-knowledge/01-batch.md and 02-terraform.md.
---

# OMS product knowledge (start here)

## Read order

0. **Onboarding (anyone new to OMS)** — `oms/product-knowledge/00-onboarding.md`  
   Glossary, mental model, business view of the five jobs, beginner mistakes.

1. **Batch (application)** — `oms/product-knowledge/01-batch.md`  
   Skill: `oms-aws-service-manager-batch` (+ `reference.md`)

2. **Terraform (infrastructure)** — `oms/product-knowledge/02-terraform.md`  
   Skill: `oms-infrastructure` (+ `reference.md`)

## Two repositories

| Repo | Path | Owns |
|------|------|------|
| **oms-aws-service-manager-batch** | `RepoSuite/oms-aws-service-manager-batch` | .NET 8 containers, submit JSON, exit codes, S3/EOM behavior |
| **oms-infrastructure** | `RepoSuite/oms-infrastructure` | VPC, RDS, ECS, Batch CE/JQ/JD, SSM, Harness state |

## One picture

```text
Scheduler / Step Functions
        │
        ▼ SubmitJob (parameters → Ref:: on command)
┌───────────────────────────────────────┐
│  Batch job container (.NET)           │  ← oms-aws-service-manager-batch
│  SSM DB bootstrap, exit code → process│
└───────────────────────────────────────┘
        ▲
        │ image, JD, retry, logs, IAM
        │
┌───────────────────────────────────────┐
│  Terraform stages A → C → B → D       │  ← oms-infrastructure
└───────────────────────────────────────┘
```

## Migration pipeline (memorize)

**A → C → B → D** — platform, catalog platform DB, job definition, catalog job DB.

## Cross-repo rules

| Change in batch repo | Must update in infra |
|----------------------|----------------------|
| New exit code | Job definition `evaluateOnExit` (stage B) |
| New env var / SSM name | Stage B environment block |
| New container / DLL | ECR repo, tag, command |
| New job | Full B+D for new `jobname`; A+C if new platform |

## Legacy context

- **RabbitMQ paths removed** for inventory feed and export order items in batch repo.
- **Windows Service Manager** scheduled tasks → Batch + Toronado/scheduler catalog Postgres.
- **ODX** task handler **behavior** preserved; transport is in-process + Batch.

## Index on OMS branch

`superdev-hmm/oms/README.md` — skills inventory and local paths.
