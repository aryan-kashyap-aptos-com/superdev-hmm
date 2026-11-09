# SSM Parameter Store catalog (foundation stack)

**Audience:** Platform, developers debugging “where is the URL stored?”  
**Terraform:** `01-infrastructure/01-parameterstore` — **83** `aws_ssm_parameter` resources in `4-03-parameterstore-resource.tf`.  
**Prefix:** `/{owners}/{space}/{environment}/…` (`parameterstoreprefix` in `3-local-values.tf`).

Secrets (passwords) are **SecureString** parameters — this table lists **names and purpose**, not values.

---

## Database identity fragments

| Parameter resource | Typical use |
|-------------------|-------------|
| `dbname` | OMS Postgres database name |
| `dbuser` / `dbpassword` | Main DB credentials |
| `keycloakdbname` + keycloak user/password | Keycloak DB |
| `extensibilitydbname` | Extensibility service schema/db |
| `taskschedulerdbname` | Task scheduler DB |
| `servicemanagerschedulerdbname` | **Batch scheduler API** schema (`SearchPath` on ECS) |
| `orderadapterdbname` / `fulfillmentdbname` | Adapter DB names |
| `pgkeycloak*` / `pgscheduler*` | Postgres host/user/password variants |
| `mssql*` / `mssqlsv*` / `mssqltoro*` | Legacy MSSQL fragments |
| `dbomsqa*` / `dbomsapp*` | QA vs app DB users |
| `dbizenda*` | Reporting DB user |
| `dbomsdataapi*` read/write | Data API users |

Paths often under `…/aws-db-pgsql/dbConnectionString/…` and service-specific prefixes — see `3-local-values.tf` (`dbparameterprefix`, `pgschedulerparameterprefix`, etc.).

---

## Service endpoints (public URLs)

| Parameter | Service |
|-----------|---------|
| `sitemanager_endpoint` | Site Manager URL (Route53 reads this) |
| `minisoft_endpoint` | Minisoft / SM container endpoint |
| `api_endpoint` | Core API |
| `paymentapi_endpoint` | Payments API |
| `services_endpoint` | Core services |
| `kek_endpoint` | KEK service |
| `taskscheduler_endpoint` | Task scheduler ECS |
| `servicemanagerscheduler_endpoint` | **Batch scheduler API** |
| `keycloak_endpoint` | Keycloak |
| `taxation_endpoint` / `taxationfacade_endpoint` | Tax services |
| `extensibility_endpoint` | Extensibility |
| `orderfacade_endpoint` / `inventoryfacade_endpoint` | Facades |
| `configrulemanager_endpoint` | Config rule manager |
| `izenda_endpoint` / `crm_endpoint` | Reporting / CRM |
| `content_ftp_endpoint` | Content FTP |

---

## Keycloak client (facades / APIs)

| Parameter | Purpose |
|-----------|---------|
| `keycloak_clientid` | Client ID |
| `keycloak_clientsecret` | Client secret |
| `keycloakusername` / `keycloakpassword` | Admin (legacy) |

---

## Site Manager feature & UX flags

| Parameter | Purpose |
|-----------|---------|
| `sitemanager_authentication_mode` | Auth mode (e.g. cognito) |
| `sitemanager_izenda_enable` | iZenda reporting |
| `sitemanager_strategy_enable` | Strategy module |
| `sitemanager_strategy_application_id` | Strategy app id |
| `sitemanager_batchjobmanager_enable` | **Batch Job Manager** (`…/sm/batchjobmanager/enabled`) — **lifecycle ignore_changes** after create; SM owns value |
| `sitemanager_estimatedshiptimeout` | Ship estimate UI |
| `session_timeout` | Session length |
| `servicemanager_fetchlimit` / `servicemanager_batchsize` | Service Manager batching |
| `sitename` | Display site name |
| `contentpath` | Content filesystem path |

---

## Worklist & commerce UI toggles

| Parameter | Purpose |
|-----------|---------|
| `worklist_display_vendor_fields` | Worklist columns |
| `worklist_display_internal_external_order_id` | Order id display |
| `worklist_display_multiple_upcs` | UPC display |
| `aspmigration_routeswitch_config` | Route switch migration |
| `smtp_settings` | SMTP JSON for notifications |

---

## ISL / integration layer

| Parameter | Purpose |
|-----------|---------|
| `isl_cognito_client_id` / `secret` / `token_url` | ISL Cognito |
| `isl_base_url` | ISL API base |
| `isl_detail_type` | Event detail type |
| `isl_carrier_enabled` | Carrier integration flag |

---

## SIMFA

| Parameter | Purpose |
|-----------|---------|
| `simfa_mv_window_days` | Materialized view window |
| `simfa_mv_start_datetime` | MV start |

---

## Amazon MQ

| Parameter | Purpose |
|-----------|---------|
| `mqbrokeradminusername` / `mqbrokeradminpassword` | MQ broker admin |

---

## Batch-specific (beyond foundation stack)

Per-job and platform metadata parameters are written by **Batch stages A/B** — not in this file:

- `…/batch/platform/{batch_shared_name}/metadata`  
- `…/{jobname}/batch/metadata`  
- `…/{jobname}/dbConnStr/connectionstring`  

See [02-terraform.md](./02-terraform.md).

---

## How apps consume parameters

| Consumer | Pattern |
|----------|---------|
| ECS task defs | `data.aws_ssm_parameter.*` in each service stack |
| Site Manager | Reads `…/sm/…` and appconfig paths; Infrastructure Settings table for some URLs |
| Batch workers | `ssm_connectionstring` env → parameter **name** only |
| Scheduler API | DB connection string built in `22-servicemanagerscheduler` task def |

---

## Related

- [11-environments-matrix.md](./11-environments-matrix.md)  
- [15-infrastructure-stack-index.md](./15-infrastructure-stack-index.md)  
