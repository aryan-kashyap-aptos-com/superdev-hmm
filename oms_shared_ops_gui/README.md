# OMS Engine

Desktop UI (**OMS Engine**) to check and control **Toronado** Windows services and **Site Manager** IIS on shared and standalone OMS stacks via **AWS SSM**, plus **log tails**, **remote file browse/download**, and optional **live sync** polling.

UI reference mockup (HTML): [docs/oms-engine-ui-reference.html](./docs/oms-engine-ui-reference.html).

### SFTP (large files)

- **SFTP** tab: hosts come from `inventory.json` per stack (shared dev + pod2 configured).
- Set `OMS_SFTP_USER` / `OMS_SFTP_PASSWORD` in `.env`, or use **Connect SFTP** (prompt; session only, not saved in repo).
- **SM path from IIS site** maps `\\dev\\{env}\\sm` → `/dev/{env}/sm` on SFTP.
- **Files (SSM)** tab: small files inline (≤8 MB); larger files download in 1 MB chunks with a progress bar.

### How OMS environments are detected

There is **no fixed env list** in the app. On each refresh, rows from `Get-Service` / `Get-Website` are classified using heuristics in `env_detection.py` (Toro `OMS-*-{env}-{slot}` names, IIS `\\dev\\{env}\\` paths, `-sm` / `-shoplogic` site suffixes). Use **Detection rules** in the title bar for the full explanation. New regression or pod tenants appear automatically when IIS/Toro lists them.

**Log architecture and SFTP vs SSM:** see [LOGS-INTEGRATION.md](./LOGS-INTEGRATION.md).

## What to call the servers

| You say | AWS Name tag | Role |
|---------|----------------|------|
| **Shared Toro server** | `eom-core-shared-dev-toronado` | Many `OMS-JobManager-*` / `OMS-JobProcessor-*` (regression*, poddev, omnipod*, …) |
| **Shared Site Manager** | `eom-core-shared-dev-sitemanager` | IIS — recycle app pool / restart site |
| **Pod2 Toro** | `oms-pod2-dev-toronado` | Standalone pod2-dev |
| **Pod2 Site Manager** | `oms-pod2-dev-sitemanager` | IIS for pod2-dev |

See [../oms-infra-knowledge/toronado-hosts.md](../oms-infra-knowledge/toronado-hosts.md) for the full map.

## Setup

```powershell
cd C:\PROD\ConnectorSuite\oms_shared_ops_gui
copy .env.example .env
pip install -r requirements.txt
```

Use the same AWS credentials as `oms_ec2_connector` (default profile or `.env` / `OMS_OPS_ENV_FILE`).

## Run

Double-click **`run_gui.bat`** or:

```powershell
python app.py
```

On open, the app **refreshes status** for the selected stack:

1. **Hosts** table - role, name tag, instance ID, private IP, **S/N** (BIOS serial via SSM), SSM status  
2. **Toronado** - all `OMS-*` services with readable **Running / Stopped / Start pending** (not numeric codes)  
3. **Site Manager (IIS)** - sites, pools, **physical path** (for ShopLogic logs)  
4. **Logs** - tail ShopLogic on SM, latest Toro `.log`, or CloudWatch **SHOPLOGICAPI** groups  

Actions ask for confirmation before start / stop / restart / recycle.

## Refresh instance IDs after ASG replace

```powershell
python refresh_inventory.py
```

Or use **Refresh EC2 IDs from AWS** in the GUI.

## Stacks in `inventory.json`

- **EOM Core Shared Dev** — multi-tenant Toro + SM  
- **OMS Pod2 Dev** — standalone  
- **EOM Core Perf15 QA** — standalone perf15  

Edit `inventory.json` to add stacks or hosts (e.g. `api`, `services`).

## Safety

- On **shared Toro**, restart **one** service at a time (e.g. `OMS-JobProcessor-regression202510qa-26`). Do not kill all `JobProcessor` processes globally.  
- IIS recycle affects the selected site’s app pool only.  
- Requires SSM **Online** on the instance (`AmazonSSMManagedInstanceCore`).
