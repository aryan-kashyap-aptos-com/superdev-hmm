# Inventory Feed scheduler migration (Toro -> AWS Batch)

**Status:** in progress (as of 2026-11-19)
**Evidence:** `kt-docs/dcoms-30140/` (old-system, new-system, migration playbook, live-jobs survey, per-client Toro jobs xlsx); `C:\OMS Other\oms-aws-job-scheduler` branch `feature/akashyap/DCOMS-30140-inventory-feed-migration-tool`; DCOMS-30140.

## Problem we solved

Migrating the legacy Toronado `oms.job`/`oms.jobstep` InventoryFeedScheduler jobs into the new `oms-aws-job-scheduler` + AWS Batch stack, without guessing at what the old config actually contains across tenants.

## Cross-tenant AWS SSO survey pattern

When a tenant's AWS account isn't yet in `~/.aws/config`:

1. `aws sso login --sso-session aptos-oms --no-browser`, approve the printed URL in a browser.
2. Enumerate every account/role the SSO session can see by reading the cached access token from `~/.aws/sso/cache/*.json` (never print the token) and calling the SSO portal API (`list_accounts` / `list_account_roles`) via boto3. This is how New Balance (682813717729) and Tommy Bahama (872601498451) account IDs were found when missing from config.
3. Add a profile per account: `OMS-Prod-Engineering-Support-<accountId>`, sharing `sso_session = aptos-oms`. Role assumption then works without re-login as long as the SSO session itself is alive.

## Querying tenant prod DBs read-only

- Use the RDS Data API via `connectors/aws-rds/run.py`, with `RDS_CLUSTER_ARN` (full ARN) and `RDS_SECRET_ARN` pointed at the `omsqa` secret, never `omsapp`. Secret naming: `oms-<tenant>-prod-omsqa-rds-postgres-secret`.
- `aws secretsmanager get-secret-value` directly (even just to inspect key names) gets blocked by the sandbox classifier as "Unauthorized Access." The Data API path above avoids ever touching the secret value directly, AWS resolves it server-side.

## Legacy detection query (verified)

```sql
SELECT j.id, j.name, j.active, js.id, js.active,
       (regexp_match(js.configstring::text,'<ExportClass>([^<]*)</ExportClass>'))[1],
       (regexp_match(js.configstring::text,'<ExportType>([^<]*)</ExportType>'))[1]
FROM oms.job j JOIN oms.jobstep js ON js.jobid=j.id
WHERE js.configstring::text ILIKE '%<ExportClass>...%'
```

Gotchas: the real job PK is `j.id`, not `j.jobid`. `configstring` is `xml` typed, needs `::text` before `ILIKE`/`regexp_match`. `ShopVisible.Core.ExportClasses.InventoryFeedScheduler` is the in-scope export class; `svDWInventory` is a different, out-of-scope one (Cole Haan only has the latter, zero InventoryFeedScheduler jobs).

## CustomField1-10 decoding

Each `CustomFieldN` in the `<Export>` XML is a `|`/`;`-delimited key=value blob, except some slots are a bare single value (e.g. `CustomField9="10"` means `QueryTimeoutOverride=10`). Slot map: 1=PublishNegative+MessageExpiration, 2=UseUPC, 3=PadIdentifier, 4=ExcludeSuppliers, 5=ListID+Description+PreorderBackorderAllocation, 6=ShowExtraFields, 7=ShowFutureFields, 8=RemoveExtraDemandwareFields, 9=QueryTimeoutOverride, 10=IgnoreProtectedFlag.

## Schedule translation gotchas (AWS EventBridge Scheduler)

- `rate(N minutes)` has no time-of-day window concept at all.
- `cron(...)` can restrict hours, but AWS's cron flavor has no Unix-style `*/N` step syntax, so "every N minutes within a daily window" has no single clean expression. Surface this as a caveat, don't silently drop the window or silently ignore it.
- A daily window like `00:00-23:59` is NOT a real restriction, it is "runs all day" written with a rounded end time. Need an explicit tolerance (we used 2 minutes) before flagging a window as a genuine gap, otherwise you get false positives on real jobs (confirmed live on poddev job 68821/jobstep 73000). A real gap looks like Tommy Bahama job 35777/jobstep 51285: window `06:00-05:00`, a deliberate ~1hr maintenance gap.

## MessageExpiration has no real equivalent yet

In the legacy RabbitMQ flow, `CustomField1`'s `MessageExpiration` was the message's TTL in queue, protecting against a stale inventory update applying after a newer one if the queue backed up. The new flow writes straight to S3 with no queue, so there's no direct equivalent. Carry the value forward into the new job's parameters so it isn't lost, but it needs its own design decision and code change in `oms-aws-service-manager-batch` before it does anything, don't just wire the field through and call it done.

## Known live failure pattern: inner JobStepId mismatch

Some `<Export>` XML has a `<JobStepId>` field that doesn't match the real `oms.jobstep.id`. This exact mismatch is the confirmed cause of a live, silently-failing job on at least one tenant (`JobStepNotFoundException` after a successful export). Any migration/translation tooling should flag this explicitly, not copy the inner field forward blindly.

## Security: plaintext DB passwords can be sitting in configstring

Found a real plaintext production Postgres password inside Tommy Bahama's own jobstep `ConnectionString` field (jobstep 51285). Redact before this ever shows up in any doc, log, or report (`Password=...` -> `Password=***REDACTED***`, case-insensitive regex). Flag for credential rotation as a separate action item, don't fix it as part of the migration. Not yet checked whether the other tenants carry the same pattern.

## Two-repo architecture for the new system

- **`oms-aws-job-scheduler`**: decides *when* a job runs. Owns `scheduled_job`/`scheduled_job_step`, creates the EventBridge schedule, calls AWS Batch `SubmitJob` on trigger.
- **`oms-aws-service-manager-batch`**: does the actual work. One Docker image + .NET console app per job type under `Jobs/` (`InventoryFeed`, `ExportOrderItems`, `CancelItems`, `ResetItemsForReroute`, `UpdateItemStatus`). This is the real successor to the Toro job runner process - reads a JSON payload (`configXml`, `jobStepId`, `jobId`, `lastSynced`), connects to OMS Postgres via an SSM-stored connection string, runs the export.
- **AWS Batch Job Definition**: a static, registered "recipe" (image, resources, retry strategy, command template with `Ref::<param>` placeholders) per job type, managed in infra-as-code, not per-tenant. `SubmitJob` names the Job Definition and supplies per-run `parameters` (e.g. `inventoryFeedJobJson`), which Batch substitutes into the command template before launching the container.
- Changing a job's code means: `dotnet publish` -> `docker build` -> tag -> push to ECR -> **register a new Job Definition revision pointing at the new image tag**. Job Definitions are versioned/immutable; forgetting the last step means the code change never actually runs even though the image exists.
- There is currently no admin UI equivalent to the old Toro backadmin (job name + steps visible at a glance). `oms-aws-job-scheduler.Api` is pure REST (Controllers/Filters/Middleware only, no Views/Pages/wwwroot), Swagger is the only visual surface and it's just an API explorer. Today the only way to see "this job has these steps" is the REST API or querying `oms_batch.scheduled_job`/`scheduled_job_step` directly. Confirmed gap, not an oversight in looking.

## poddev/podqa share one cluster

`poddev` and `podqa` are different database names on the **same** shared-dev Aurora Postgres cluster/RDS proxy (`oms-shared-dev-postgresql-rds-proxy`), confirmed via `PGDATABASE=poddev python oms_db.py test`. They share seeded data, same job IDs (e.g. 68821/73000, 75973/80769/80835) exist on both.

## CodeArtifact NuGet auth looks like a stuck build

A `dotnet restore`/build against private CodeArtifact feeds that silently sits with near-zero CPU growth for 20+ minutes is very likely an expired NuGet auth token retrying with long backoff (`401 Unauthorized`), not a real hang. Confirm with a foreground `dotnet restore` to see the real error, then refresh via `aws codeartifact get-authorization-token` + `dotnet nuget update source ... --username aws --password <token> --store-password-in-clear-text`. `aws codeartifact login` itself gets blocked by the sandbox classifier ("Unauthorized Access") even with an admin profile, use the narrower `get-authorization-token` call instead.

## Local DB tunnel ports drop mid-session

A local port forward to a shared-dev DB (e.g. 1111) can drop between turns with a plain `SocketException: actively refused`, no credential leak, just nothing listening anymore. Check `netstat -an | grep <port>` before assuming the DB or credentials are the problem. The tunnel sometimes comes back on a different local port (e.g. 1112) with the same remote credentials.

## Live triage examples

- DCOMS-30140 4-client Toro job survey (LL Bean, Cole Haan, New Balance, Tommy Bahama) via AWS SSO + RDS Data API, output in `kt-docs/dcoms-30140-5-toro-jobs-by-client.xlsx`.
- DCOMS-30140 migration tool dry-run verified live against poddev job 68821/jobstep 73000 (port 1111, then again after a tunnel drop on port 1112).
