# OMS QA — environments, Site Manager, and how to test

> Read [00-onboarding.md](./00-onboarding.md) for what OMS is. This page is for **QA and explorers**: where things live, what “backadmin” means, and how to open **Site Manager** in a pod dev environment.

---

## One OMS “environment” is not one URL

A single OMS deployment (e.g. **pod dev**) is a **mesh of services**. You will see different hostnames or paths for each concern. Names in code and docs do not always match marketing names.

| You hear… | Often means… | Typical role |
|-----------|--------------|--------------|
| **Site Manager** | **backadmin** in URLs and legacy code | Operations UI: orders, catalog admin, configuration |
| **Keycloak** | Identity / SSO | Login and tokens for newer APIs |
| **EOM / core APIs** | ECS facades (`orderfacade`, `coreservice`, …) | HTTP APIs over the OMS database |
| **Integration layers** | Feeds, external systems | Imports/exports, partner connectivity |
| **SIMFA** | (site-specific integration) | Ask your team’s Confluence space for exact scope |
| **Label printing** | Dedicated service | Warehouse / store label workflows |
| **Batch jobs** | AWS Batch containers | Scheduled bulk work ([01-batch.md](./01-batch.md)) |

Terraform maps many of these under `oms-infrastructure/03-application/01-aws-ecs-service/` — each folder is one deployable service.

---

## Site Manager vs “backadmin”

**Site Manager** is the **human-facing admin UI** retailers use to work orders and site configuration. In older Aptos OMS code and URLs, the path **`/backadmin/`** is the Site Manager web application (ASP.NET WebForms era).

**QA entry (pod dev example):**

- **Login:** [https://oms-pod-dev-sm.dev.eom.aptos.io/backadmin/login.aspx](https://oms-pod-dev-sm.dev.eom.aptos.io/backadmin/login.aspx)
- **Host pattern:** `oms-pod-dev-sm` = OMS **pod** tenant, **dev** space, **sm** = Site Manager entry host (naming varies by estate).

If you already have a session cookie, the app may **skip the login page** and land inside backadmin — that is expected.

---

## QA test mode credentials (pod dev Site Manager)

For **manual QA** on the pod dev Site Manager host above:

| Field | Value |
|-------|--------|
| Username | `test-mode` |
| Password | *(team QA password — store in private config, not in git)* |

**Do not commit passwords** to `superdev-hmm`. Use:

- `qa-tester/environments.local.md` (gitignored) + env vars `QA_OMS_POD_DEV_USER` / `QA_OMS_POD_DEV_PASSWORD`, or  
- A test run’s `plan.md` **Login** section for a one-off scenario.

Example private row (already in `qa-tester/environments.local.md` on this machine):

```markdown
| oms-pod-dev-sitemanager | https://oms-pod-dev-sm.dev.eom.aptos.io/ | qa | `QA_OMS_POD_DEV_USER`, `QA_OMS_POD_DEV_PASSWORD` | login: `/backadmin/login.aspx` |
```

---

## Using superdev-hmm QA browser on Site Manager

```bash
cd superdev-hmm
export QA_OMS_POD_DEV_USER='test-mode'
export QA_OMS_POD_DEV_PASSWORD='...'   # from team vault

python3 qa-tester/browser/run.py start https://oms-pod-dev-sm.dev.eom.aptos.io/
python3 qa-tester/browser/run.py login --site oms-pod-dev-sitemanager
python3 qa-tester/browser/run.py snapshot    # see headings, buttons after login
python3 qa-tester/browser/run.py elements    # list clickable controls
```

Or create a formal run:

```bash
python3 qa-tester/test-run.py new "OMS Site Manager smoke" --site https://oms-pod-dev-sm.dev.eom.aptos.io/
# Fill plan.md Login: Sign-in page /backadmin/login.aspx, user, password
python3 qa-tester/browser/run.py play qa-tester/scenarios/<your>.json --run <run> --go
```

**Allowed sites:** only hosts listed in the active run’s `plan.md` or `environments.local.md` (`qa-tester/browser/run.py status`).

---

## What we see after login (pod dev, verified)

Login with `test-mode` on [backadmin/login.aspx](https://oms-pod-dev-sm.dev.eom.aptos.io/backadmin/login.aspx):

1. Browser talks to **Amazon Cognito** (`cognito-idp.us-east-1.amazonaws.com`) — Site Manager auth is tied to the estate’s identity layer (related to **Keycloak** in the broader OMS stack).
2. backadmin endpoints such as `ProcessSuccessfulLogin` / `RedirectUser` run over XHR.
3. Landing page is often **Releases and Maintenance** (`releaseschedule.aspx`, title “Releases and Maintenance”), build **Version 2026.7.0.0** in the footer on a recent visit.
4. **Top navigation** (same on inner pages): **Users**, **Content**, **Commerce**, **CRM**, **Analytics**, plus knowledge-base and user utilities.
5. **Commerce** (`commerce.aspx`) exposes sections such as **Affiliates**, **Shipping**, **Orders** (expandable menus — core order QA often lives under Commerce → Orders).

Minor console noise (`Permissions policy violation: unload`) appeared on smoke login; no failed document requests.

## What to explore after login (smoke ideas)

Non-exhaustive checklist for new QA:

1. **Login** — form accepts `test-mode`; lands past `login.aspx` (or Cognito-equivalent flow).
2. **Navigation** — all five top-level areas load (Users, Content, Commerce, CRM, Analytics).
3. **Commerce → Orders** — order search/list (permissions may limit `test-mode`).
4. **Session** — refresh page: still signed in if cookie cached.

Document findings in the run’s `tasks/…/results.md`, not in public git if screenshots show customer data.

---

## Other OMS envs (pattern)

Hostnames usually encode **tenant**, **stage**, and **surface**:

```text
oms-<tenant>-<role>.<stage>.eom.aptos.io
```

Examples of **roles** (vary by estate): `sm` (Site Manager), API gateways, Keycloak hosts, etc. Your team’s **Confluence** space should list canonical URLs per pod/UAT/prod-like env.

When Confluence is connected, search for: `Site Manager`, `pod dev`, `OMS environments`, `backadmin`, `QA test account`.

---

## Relationship to Batch / Terraform QA

| Layer | What QA often validates |
|-------|-------------------------|
| **Site Manager** | UI workflows, order states, user-visible exports |
| **Batch** | Scheduled jobs ran (CloudWatch, order notes, S3 files) |
| **Terraform** | Not UI-tested — validate via deploy pipeline + smoke URLs |

A full release may need **UI smoke on Site Manager** plus **job verification** for feeds — different tools, same OMS database underneath.

---

## Confluence and internal docs

Augment this page from your Atlassian wiki:

- Environment URL matrix (pod / UAT / perf)
- Which services run on which clusters
- Standard QA accounts (`test-mode`, etc.) and **forbidden** prod-like accounts
- SIMFA and integration-layer test endpoints

Repo connector (if configured): `python3 connectors/confluence/run.py search '…'`

---

## Quick reference links

| Resource | Link |
|----------|------|
| Pod dev Site Manager login | [backadmin/login.aspx](https://oms-pod-dev-sm.dev.eom.aptos.io/backadmin/login.aspx) |
| Batch product knowledge | [01-batch.md](./01-batch.md) |
| Infra map | [02-terraform.md](./02-terraform.md) |
