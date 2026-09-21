# OMS infra knowledge

ConnectorSuite reference for **where OMS workloads run** in shared dev / QA (AWS `us-east-1`). Use this when debugging Toronado jobs, DB connectivity, or picking the right EC2 host for SSM.

| Doc | Contents |
|-----|----------|
| [toronado-hosts.md](./toronado-hosts.md) | Shared multi-tenant Toronado vs standalone stacks, instance inventory, service naming |
| [databases-and-local-access.md](./databases-and-local-access.md) | Postgres DB names vs Toronado host, SSH tunnel / MCP notes |

## Related tooling in this repo

| Path | Use |
|------|-----|
| [oms_ec2_connector](../oms_ec2_connector/) | SSM exec CLI for **pod2-dev** (sitemanager, api, services, toronado, …) |
| [oms_shared_ops_gui](../oms_shared_ops_gui/) | **GUI** — Toro services + IIS recycle on shared / pod2 / perf15 stacks |
| [oms_db_connector](../oms_db_connector/) | Bastion SSH tunnel + read-only SQL (configure `PGDATABASE` per target DB) |
| [oms_harness_connector](../oms_harness_connector/) | Harness MCP; see [docs/OMS-HARNESS-PIPELINE-REFERENCE.md](../oms_harness_connector/docs/OMS-HARNESS-PIPELINE-REFERENCE.md) |

## Keeping this accurate

Instance IDs and private IPs **change** when ASGs replace instances. Refresh with:

```powershell
aws ec2 describe-instances --region us-east-1 `
  --filters "Name=tag:Name,Values=*toronado*" "Name=instance-state-name,Values=running,stopped" `
  --query "Reservations[].Instances[].{Name:Tags[?Key=='Name']|[0].Value,Id:InstanceId,State:State.Name,PrivateIp:PrivateIpAddress}" `
  --output table
```

Last full Toronado inventory pass: **2026-09-16**.
