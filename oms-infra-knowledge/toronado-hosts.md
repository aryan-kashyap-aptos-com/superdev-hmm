# Toronado (Toro) hosts — shared vs standalone

Toronado is the Windows job scheduler/processor tier (`OMS-JobManager-*`, `OMS-JobProcessor-*`). **Which EC2 box matters depends on the Postgres database / environment name**, not on where you pointed Cursor MCP.

## Mental model

```text
                    ┌─────────────────────────────────────────┐
                    │  eom-core-shared-dev-toronado           │
                    │  ONE host, MANY environments            │
                    │  (regression202510qa, poddev, podqa,    │
                    │   omnipod*, automationqa, …)            │
                    └─────────────────────────────────────────┘

   ┌──────────────────────────┐     ┌──────────────────────────┐
   │  oms-pod2-dev-toronado   │     │  eom-core-perf15-qa-     │
   │  Standalone pod2-dev     │     │  toronado                │
   │  stack (poddev DB)       │     │  Standalone perf15 QA    │
   └──────────────────────────┘     └──────────────────────────┘
```

| Pattern | Host naming | Toro services | Typical databases / envs |
|---------|-------------|---------------|---------------------------|
| **Shared multi-tenant** | `eom-core-shared-dev-toronado` | Many `OMS-JobManager-{env}-*` / `OMS-JobProcessor-{env}-*` on **one** server | `regression202510qa`, `regression202520qa`, `poddev`, `podqa`, `omnipoddev`, `omnipodqa2`, `automationqa`, `integrationqa`, … |
| **Standalone stack** | `oms-pod2-dev-toronado` | Services for **pod2-dev** deploy suffix only | **`poddev`** (pod2 shared dev server tier) |
| **Standalone stack** | `eom-core-perf15-qa-toronado` | `OMS-*-perf15qa-*` only | **perf15 QA** (not `regression202510qa`) |
| **Standalone stack** | `eom-core-appsec-dast-toronado` | DAST / appsec slice | AppSec DAST envs |
| **Standalone stack** | `oms-gamma-ops-toronado` | Gamma ops | Gamma ops envs |

**Common mistake:** Changing Postgres MCP from `poddev` to `regression202510qa` does **not** stop Toronado. Jobs for `regression202510qa` are processed on **`eom-core-shared-dev-toronado`**, not on `oms-pod2-dev-toronado`.

## Inventory (2026-09-16)

Refresh IDs before SSM; ASGs replace instances.

| Name tag | Instance ID | State | Private IP | Role |
|----------|-------------|-------|------------|------|
| `eom-core-shared-dev-toronado` | `i-03b3fb1c107fde172` | running | `20.108.20.254` | **Shared** — many regression / omnipod / pod QA envs |
| `oms-pod2-dev-toronado` | `i-09ed32ca27fa7ec17` | running | `20.115.11.25` | **Standalone** — pod2-dev |
| `eom-core-perf15-qa-toronado` | `i-04d71cb70d26088a9` | running | `20.110.20.244` | **Standalone** — perf15 QA |
| `eom-core-appsec-dast-toronado` | `i-080b667ee963e8368` | running | `10.106.20.250` | **Standalone** — appsec DAST |
| `oms-gamma-ops-toronado` | `i-06ed2dc137c742fa8` | running | `20.116.13.49` | **Standalone** — gamma ops |

`oms_ec2_connector` `.env.pod2dev` may list an **older** Toronado instance ID; always resolve current `oms-pod2-dev-toronado` from AWS before SSM.

## Shared host: how to read service names

On **`eom-core-shared-dev-toronado`**, each logical environment gets its own manager/processor pair:

```text
OMS-JobManager-regression202510qa-26
OMS-JobProcessor-regression202510qa-26
```

- Middle segment = **environment / DB name** (e.g. `regression202510qa`, `poddev-26` style suffixes vary by deploy).
- Trailing number = **deploy sequence** (multiple `-26` / `-11` sets can exist after redeploys).

Example services observed on shared-dev Toro (not exhaustive):

| Environment segment | Manager | Processor (example) |
|---------------------|---------|---------------------|
| `regression202510qa` | Running | Must be **Running** (not StopPending) |
| `regression202520qa` | Running | Running |
| `regression202530qa` | Running | Running |
| `regression202540qa` | Running | Running |
| `poddev` | Running | Running |
| `podqa` | Running | Running |
| `omnipoddev` | Running | Running |
| `omnipodqa2` | Running | Running |
| `automationqa` | Running | Running |
| `integrationqa` | Running | Running |

## Standalone perf15 QA host

On **`eom-core-perf15-qa-toronado`**, naming is **not** per regression DB:

```text
OMS-JobManager-perf15qa-35
OMS-JobProcessor-perf15qa-35
```

Multiple sequence suffixes (e.g. 35, 36, 39) may all show **Running** after redeploys — treat duplicate sets as a cleanup/misconfiguration risk (same pattern as pod2-dev runbooks).

## Health check via SSM

Use a parameters JSON file so PowerShell commas do not break `aws ssm send-command`.

**List Toro-related services (shared host):**

```powershell
@'
{
  "commands": [
    "Get-Service | Where-Object { $_.Name -like 'OMS*' } | Select-Object Name, Status | Sort-Object Name | Format-Table -AutoSize | Out-String -Width 300"
  ]
}
'@ | Set-Content -Path $env:TEMP\ssm-toro.json -Encoding utf8

aws ssm send-command --region us-east-1 `
  --instance-ids i-03b3fb1c107fde172 `
  --document-name AWS-RunPowerShellScript `
  --parameters file://$env:TEMP/ssm-toro.json `
  --query Command.CommandId --output text
```

**Check one environment (example: `regression202510qa`):**

```powershell
Get-Service 'OMS-JobManager-regression202510qa-26','OMS-JobProcessor-regression202510qa-26' |
  Format-List Name, Status, StartType
```

Both should be **Running**. **StopPending** on the processor with a running manager matches “jobs enqueue in DB but nothing completes.”

**Recovery (on-host, after approval):**

```powershell
Restart-Service 'OMS-JobProcessor-regression202510qa-26' -Force
# if stuck in StopPending:
Stop-Service 'OMS-JobProcessor-regression202510qa-26' -Force
Start-Service 'OMS-JobProcessor-regression202510qa-26'
```

## DB correlation

| `oms.environment.name` (Postgres) | Toronado host |
|-----------------------------------|---------------|
| `regression202510qa` | `eom-core-shared-dev-toronado` |
| `poddev` (pod2-dev tier) | `oms-pod2-dev-toronado` (and possibly shared-dev services for other `poddev-*` deploy names) |

When jobs stall, confirm **processor** status on the host for **that** environment name, then query `oms.job` / `oms.jobqueue` for the same database.
