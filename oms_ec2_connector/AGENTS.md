# OMS EC2 Connector — Agent Guide

Remote PowerShell on Windows EC2 instances via AWS Systems Manager (SSM). No RDP required once SSM is enabled on the target instances.

## When to use

- Run health checks on pod2-dev servers (sitemanager, api, services, toronado, content)
- Execute PowerShell without RDP hops through bastion/domain controller
- List instance IDs and private IPs for the environment

## Setup

```powershell
cd C:\PROD\ConnectorSuite\oms_ec2_connector
copy .env.example .env.pod2dev
pip install -r requirements.txt
```

`.env.pod2dev` already contains live pod2-dev instance IDs and IPs. **Never read or print `.env.*` contents with credentials.**

## Environment variables

| Variable | Purpose |
|----------|---------|
| `ENV_NAME` | Environment label (e.g. `pod2dev`) |
| `AWS_REGION` | AWS region (default `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | Optional if default AWS profile is configured |
| `AWS_SECRET_ACCESS_KEY` | Optional |
| `AWS_SESSION_TOKEN` | Optional (required for STS creds) |
| `EC2_NAME_PREFIX` | Name tag prefix for `refresh` |
| `INSTANCE_<alias>_ID` | EC2 instance ID |
| `INSTANCE_<alias>_IP` | Private IP |
| `INSTANCE_<alias>_PUBLIC_IP` | Public IP (bastion only) |

### pod2-dev aliases

| Alias | Server |
|-------|--------|
| `bastion` | oms-pod2-dev-BastionHost |
| `api` | oms-pod2-dev-api |
| `services` | oms-pod2-dev-services |
| `sitemanager` (or `sm`) | oms-pod2-dev-sitemanager |
| `content` | oms-pod2-dev-content |
| `toronado` | oms-pod2-dev-toronado |
| `rds-migration` | oms-pod2-dev-rds-migration-host |

## CLI commands

```powershell
python oms_ec2.py --env .env.pod2dev list
python oms_ec2.py --env .env.pod2dev test sitemanager
python oms_ec2.py --env .env.pod2dev exec toronado "Get-Service | Where-Object Status -eq Running | Select -First 5"
python oms_ec2.py --env .env.pod2dev script sitemanager ..\tickets\DCOMS-29691-pod2dev-ec2-shutdown-restart-validation\scripts\Check-Pod2Dev-SM-Health.ps1
python oms_ec2.py --env .env.pod2dev refresh
```

## Agent rules

1. **Default env file** — use `--env .env.pod2dev` for pod2-dev work.
2. **Never read or commit** `.env`, `.env.*` credential values.
3. **Run `list` first** — confirms instance IDs, IPs, and SSM status.
4. **SSM must be Online** — `exec` and `script` fail if the instance is not SSM-managed.
5. **Prefer `script`** for multi-line PowerShell or existing `.ps1` health checks.
6. **Read-only by default** — only run mutating commands when the user explicitly asks.

## Typical workflow

```powershell
python oms_ec2.py --env .env.pod2dev list
python oms_ec2.py --env .env.pod2dev test sitemanager
python oms_ec2.py --env .env.pod2dev exec sitemanager "Get-Website | Select Name,State"
```

## File map

| File | Role |
|------|------|
| `oms_ec2.py` | CLI entry point |
| `client.py` | Env loading, boto3 session |
| `instances.py` | Instance alias resolution, SSM status |
| `ssm_exec.py` | SSM Run Command (PowerShell) |
| `.env.pod2dev` | pod2-dev instance inventory |
| `.env.example` | Env template |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| SSM shows `NotManaged` | Install/start SSM agent; attach `AmazonSSMManagedInstanceCore` to instance role |
| SSM not Online | Add VPC endpoints for `ssm`, `ssmmessages`, `ec2messages` in private subnet |
| Wrong instance after redeploy | Run `refresh` and update `.env.pod2dev` |
| Auth error | Set AWS creds in `.env.pod2dev` or configure default AWS profile |
| Script timeout | Use `--timeout 600` on `script` or `exec` |

## Updating IPs after instance replacement

```powershell
python oms_ec2.py --env .env.pod2dev refresh
```

Copy the printed `INSTANCE_*` lines into `.env.pod2dev`.
