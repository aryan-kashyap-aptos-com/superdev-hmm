# OMS Engine

Desktop UI (**OMS Engine**) to check and control **Toronado** Windows services and **Site Manager** IIS on shared and standalone OMS stacks via **AWS SSM**, plus **log tails**, **remote file browse/download**, **Parameter Store** editing, and optional **live sync** polling.

UI reference mockup (HTML): [docs/oms-engine-ui-reference.html](./docs/oms-engine-ui-reference.html).

### Files and logs

- **Files** tab: browse on content / Site Manager / Toronado hosts. **View full file** loads the entire file (chunked SSM for large files, no tail trimming). **Download** saves to `%USERPROFILE%\Downloads\OMS Engine\`.
- **Logs** tab: ShopLogic tails on the **content** server (1,500 lines), Toronado service logs (1,500 lines), CloudWatch API groups with selectable scan window.

### How OMS environments are detected

There is **no fixed env list** in the app. On each refresh, rows from `Get-Service` / `Get-Website` are classified using heuristics in `env_detection.py`. Use **Detection** in the title bar for the full explanation. **Tenant sites** on IIS filters to classified OMS tenant sites (not shared infrastructure).

**Log architecture:** see [LOGS-INTEGRATION.md](./LOGS-INTEGRATION.md).

## What to call the servers

| You say | AWS Name tag | Role |
|---------|----------------|------|
| **Shared Toro server** | `eom-core-shared-dev-toronado` | Many `OMS-JobManager-*` / `OMS-JobProcessor-*` |
| **Shared Site Manager** | `eom-core-shared-dev-sitemanager` | IIS - recycle app pool / restart site |
| **Shared content** | `eom-core-shared-dev-cont` | UNC site files, ShopLogic logs |
| **Pod2 Toro** | `oms-pod2-dev-toronado` | Standalone pod2-dev |
| **Pod2 Site Manager** | `oms-pod2-dev-sitemanager` | IIS for pod2-dev |

Sidebar also shows **bastion public IP** when configured in `inventory.json`.

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

## Refresh instance IDs after ASG replace

```powershell
python refresh_inventory.py
```

Or open **Detection** and use **Refresh instance IDs from AWS**.

## Stacks in `inventory.json`

- **EOM Core Shared Dev** - multi-tenant Toro + SM + content  
- **OMS Pod2 Dev** - standalone  
- **EOM Core Perf15 QA** - standalone perf15  

Edit `inventory.json` to add stacks, hosts, bastion, or `ssm_parameter_prefix`.

## Safety

- On **shared Toro**, restart **one** service at a time. Do not kill all `JobProcessor` processes globally.  
- IIS recycle affects the selected site's app pool only.  
- Parameter Store saves overwrite values in AWS; confirm before changing production parameters.  
- Requires SSM **Online** on the instance (`AmazonSSMManagedInstanceCore`).
