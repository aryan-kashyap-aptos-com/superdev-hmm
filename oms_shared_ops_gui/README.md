# OMS Shared Ops GUI

Desktop UI to check and control **Toronado** Windows services and **Site Manager** IIS (app pool recycle / site restart) on shared and standalone OMS stacks via **AWS SSM**, plus **log tails** (ShopLogic on SM, Toro on Toronado host, API via CloudWatch).

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
