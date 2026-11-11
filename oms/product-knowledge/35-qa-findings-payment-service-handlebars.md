# QA findings — online payment service handlebars fix (DCOMS-30072)

> Written from a real QA session. Read [03-qa-environments.md](./03-qa-environments.md) first for the environment basics. No credentials are recorded here; get them from the run's own `plan.md` or the team vault.

## What was tested

The Snyk fix for `scp-service-online-payment` raised **handlebars** to 4.7.10 (build `v1.8.0-gold-3ef71c3`). Question: does it break anything?

| Finding | Detail |
|---------|--------|
| Where handlebars is used | Only as the **Swagger UI view engine**. No payment, label or order flow uses it. Risk is low. |
| Snyk | Clean after the fix. |
| Unit tests | 24 mocha tests pass. |
| `npm ci` on Windows | The postinstall script fails under `cmd.exe` and wipes `node_modules`. Use `npm ci --ignore-scripts`. |
| Swagger UI, run locally | Served on a local port with stub handlers and a dummy `jwt` auth. Page loads, definition loads, models render, no `{{` leaking into the page. |

## Why only some environments can test the label flow

The shipping-label call goes through the **extensibility** service, which calls the payment service. The SIMFA routes depend on the `is_simfa_enabled` setting, which is not on in every environment, so a pod environment having extensibility deployed is not enough. The regression environments (`regression202530`, `regression202540`) are where it was enabled and could be verified by reading the database.

- Label call: `POST {{host}}/app/extensibility/v1/extensions/shipping-label/transactions/` with a UPS shipment request.
- Working store in `regression202530`: **2600**.
- Stores 0010, 8001 and 0003 fail with UPS error **120100**. Cause is store data in the DB, not the code change.
- Keycloak must be reachable for a token; in `regression202540` Keycloak was already scaled to 0.

## Environment changes made during the session

| Environment | Change |
|-------------|--------|
| `regression202530` | Extensibility rolled back from 1.8.0 to task definition `:15` (`v1.7.10-gamma-7c80999`), then scaled to **0**. |
| `regression202540` | Extensibility scaled to **0**. |

If someone finds these services down, this is why. Scale them back up before the next test that needs them.

## Verdict recorded

Low risk. Swagger UI is the only runtime use, the label flow works for store 2600, tests and Snyk are clean. Not claimed: every store or every payment route was exercised.

## QA tooling lessons from the same session

The qa-tester report rules (ticket + timestamp names, one session per report, 3-page stakeholder PDF, flag number mismatches) live in `qa-tester/method.md` under "Hard rules for reports and file names" on the `main` branch and are merged into this branch. Short version:

1. File name `<TICKET>-<Title> -<DDMMYYYY>-<HHMMSS>.pdf`; never reuse a name.
2. Always open the file the `report` command printed.
3. After changing the tool, `run.py stop` then `start` (panel buttons run old code).
4. The `page-text` check also scans the runner panel's frame; check a specific selector instead.
5. In Git Bash, `/path` arguments are rewritten to Windows paths. Check the plan after `new`.
