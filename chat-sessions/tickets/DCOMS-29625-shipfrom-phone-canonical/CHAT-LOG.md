## 2026-09-20 — Implement shipFrom telephoneNumbers (oms-isl-client 1.6.1 + OMS bump)

**Status when closed:** in progress

- Branch `feature/akashyap/DCOMS-29625-shipfrom-phone-canonical-fix` in `oms-isl-client` and `oms`.
- `BusinessUnit.telephoneNumbers`, `BusinessUnitPhone` helper, mapper + `LabelService` updates, tests; package **1.6.1** packed to `artifacts/nuget/`.
- OMS: `packages.config` + Shell csproj → 1.6.1; local DLL under `packages/Aptos.OMS.Isl.1.6.1/` for build until feed publish.

## 2026-09-20 — Checkout all workspace repos to master

**Status when closed:** done

- `oms`, `oms-isl-client`, `scp-types-canonical-shipping`, `isl-service-middleware-shippo-api` → `master`, fast-forwarded to `origin/master`.
- Stashed: Shippo `CG-3789` WIP (`git stash list` in shippo repo); `scp-types` local `package-lock.json` stash.
- `ConnectorSuite` is not a git repo. Untracked files left in place (OMS `tools/`, scp-types local JSON samples, etc.).

## 2026-09-20 — Shippo adapter vs OMS alignment plan

**Status when closed:** done

- Compared `isl-service-middleware-shippo-api` INTSER-579 (on `origin/master`) with local `CG-3789` WIP and `oms-isl-client` / OMS `Aptos.OMS.Isl` 1.6.0.
- Deliverable: execution plan for DCOMS-29625 (no code changes this chat).

## 2026-09-20 — Read and summarize Jira DCOMS-29625

**Status when closed:** done

- Pulled full Jira issue, comments, and links; wrote ticket workspace `README.md`.
- Files touched: `tickets/DCOMS-29625-shipfrom-phone-canonical/README.md`, `CHAT-LOG.md`
