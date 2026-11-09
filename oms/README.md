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
| **0** | [00-onboarding.md](./product-knowledge/00-onboarding.md) | **Start here** — what OMS is, glossary, diagram, who reads what |
| 1 | [01-batch.md](./product-knowledge/01-batch.md) | Batch jobs, JSON payloads, exit codes, Docker (with plain-English intros) |
| 2 | [02-terraform.md](./product-knowledge/02-terraform.md) | Terraform layers, A→C→B→D, SSM/state, ECR wiring (with analogies) |
| 3 | [03-qa-environments.md](./product-knowledge/03-qa-environments.md) | **QA** — Site Manager / backadmin, pod URLs, browser login, many services per env |

## Project skills (Cursor agents)

| Skill | When to use |
|-------|-------------|
| [oms-product-knowledge](../.cursor/skills/oms-product-knowledge/SKILL.md) | Start here — links to full docs |
| [oms-aws-service-manager-batch](../.cursor/skills/oms-aws-service-manager-batch/SKILL.md) | Batch app; see `reference.md` in same folder |
| [oms-infrastructure](../.cursor/skills/oms-infrastructure/SKILL.md) | Terraform; see `reference.md` in same folder |

## Cursor skills inventory

Bundled manifest: [cursor-skills-inventory.json](./cursor-skills-inventory.json) (personal skills under `~/.cursor/skills-cursor/`).

Atlassian plugins (when enabled): `~/.cursor/plugins/cache/cursor-public/atlassian/.../skills/` — Jira, Confluence, sprint dashboard, etc.
