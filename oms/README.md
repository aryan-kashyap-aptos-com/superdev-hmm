# OMS branch — Cursor skills & product knowledge

This branch holds **project skills** and pointers for Order Management System (OMS) work on Aptos Retail AWS estates.

## Local repo paths (RepoSuite)

| Repo | Path |
|------|------|
| Batch job code (.NET 8) | `/Users/akashyap/RepoSuite/oms-aws-service-manager-batch` |
| Terraform / Harness infra | `/Users/akashyap/RepoSuite/oms-infrastructure` |

## Product knowledge (read in order)

| # | Document | Contents |
|---|----------|----------|
| 1 | [01-batch.md](./product-knowledge/01-batch.md) | All five jobs, submit JSON, exit codes, SSM, Docker, tests, ODX legacy |
| 2 | [02-terraform.md](./product-knowledge/02-terraform.md) | Layers, A→C→B→D, SSM/state, Harness, ECR wiring, ECS list, gotchas |

## Project skills (Cursor agents)

| Skill | When to use |
|-------|-------------|
| [oms-product-knowledge](../.cursor/skills/oms-product-knowledge/SKILL.md) | Start here — links to full docs |
| [oms-aws-service-manager-batch](../.cursor/skills/oms-aws-service-manager-batch/SKILL.md) | Batch app; see `reference.md` in same folder |
| [oms-infrastructure](../.cursor/skills/oms-infrastructure/SKILL.md) | Terraform; see `reference.md` in same folder |

## Cursor skills inventory

Bundled manifest: [cursor-skills-inventory.json](./cursor-skills-inventory.json) (personal skills under `~/.cursor/skills-cursor/`).

Atlassian plugins (when enabled): `~/.cursor/plugins/cache/cursor-public/atlassian/.../skills/` — Jira, Confluence, sprint dashboard, etc.
