# Backup and baseline summary - oms-pod2-dev

**Captured:** 2026-09-04T12:16:29Z (post-recovery)  
**Prior baseline:** 2026-09-04 morning (pre-terminate instances — superseded)  
**AWS account:** `268173716021`  
**Region:** `us-east-1`  
**Ticket:** [DCOMS-29691](https://aptos.atlassian.net/browse/DCOMS-29691)

**Context:** Instances were terminated via ASG scale-to-0, restored, then recovered with OMS-App-Deploy + OMS-DFS-Namespace. This baseline reflects the **new** running fleet.

---

## Executive summary

| Resource type | Status | Notes |
|---|---|---|
| EC2 (7 instances) | All **running** | Launched 2026-09-04 ~07:54 UTC (post ASG restore) |
| RDS Aurora | Unchanged | 7-day automated backups |
| EBS | New volumes on new instances | Old terminated-instance volumes may appear in `ebs-volumes-orphaned.json` |
| SM application | **Working** (login verified) | ALB target still unhealthy on `/hashcheck.asp` |
| DFS | Repointed | `\\omspod.aptos.com\pod2-dev\dev` → `\\pod-cnt-d-2966\dev` |

---

## Current EC2 inventory

| Name | Instance ID | Private IP | Launch (UTC) | State |
|---|---|---|---|---|
| oms-pod2-dev-sitemanager | i-036505377f8ad5c6e | 20.115.11.102 | 2026-09-04 07:54:16 | running |
| oms-pod2-dev-api | i-02b70bcb094c2dcec | 20.115.11.82 | 2026-09-04 07:54:28 | running |
| oms-pod2-dev-content | i-0d23caf16cd2c5adb | 20.115.11.54 | 2026-09-04 07:54:29 | running |
| oms-pod2-dev-services | i-0f603ed7f8f947bd7 | 20.115.11.135 | 2026-09-04 07:54:39 | running |
| oms-pod2-dev-BastionHost | i-0b489a48f31463d74 | 20.115.111.220 | 2026-09-04 07:54:40 | running |
| oms-pod2-dev-rds-migration-host | i-0f2a63e597d421e39 | 20.115.11.208 | 2026-09-04 07:54:45 | running |
| oms-pod2-dev-toronado | i-0aee83fe4726581e4 | 20.115.11.213 | 2026-09-04 07:54:48 | running |

**Terminated (pre-recovery — do not use):**

| Name | Old instance ID |
|---|---|
| sitemanager | i-05692759bfaaa9cc3 |
| api | i-0548397f26e0277c5 |
| content | i-05b829a2f1fd2d7b9 |
| services | i-077bb903286497148 |
| toronado | i-0ebec6c5bc911d854 |

Bastion + migration host IDs **unchanged** (were stopped, not terminated).

---

## ASG settings (live)

| ASG | Min | Max | Desired | Suspended processes |
|---|---|---|---|---|
| oms-pod2-dev-sm-asg | 1 | 3 | 1 | ReplaceUnhealthy, HealthCheck |
| oms-pod2-dev-api-asg | 1 | 3 | 1 | ReplaceUnhealthy, HealthCheck |
| oms-pod2-dev-cnt-asg | 1 | 3 | 1 | ReplaceUnhealthy, HealthCheck |
| oms-pod2-dev-svc-asg | 1 | 3 | 1 | HealthCheck, ReplaceUnhealthy |
| oms-pod2-dev-toronado-asg | 1 | 1 | 1 | (none) |

Full detail: `asg-settings.json`

---

## ALB target health (at capture)

| Target group | Instance | Health | Detail |
|---|---|---|---|
| oms-pod2-dev-sm-tg | i-036505377f8ad5c6e | unhealthy | 404 on `/hashcheck.asp` |
| oms-pod2-dev-api-tg | i-02b70bcb094c2dcec | unhealthy | 404 |
| oms-pod2-dev-cnt-tg | i-0d23caf16cd2c5adb | unhealthy | failed checks |
| oms-pod2-dev-svc-tg | i-0f603ed7f8f947bd7 | unhealthy | failed checks |
| oms-pod2-dev-sftptg | i-036505377f8ad5c6e | unhealthy | SSH check |

SM login works via ALB despite unhealthy target (missing `hashcheck.asp`).  
Full detail: `target-group-health.json`

---

## RDS Aurora backup (unchanged)

| Field | Value |
|---|---|
| Cluster | `oms-pod2-dev-aurora` |
| Engine | Aurora PostgreSQL 16.11 |
| Backup retention | 7 days |
| Encrypted | Yes |
| Deletion protection | Enabled |

Detail: `rds-cluster.json`, `rds-cluster-snapshots.json`

---

## EBS notes

- **Attached volumes:** `ebs-volumes.json` (current 7 instances)
- **Available/orphaned volumes:** `ebs-volumes-orphaned.json` — review for cleanup after terminate
- Content 300 GB data volume was **recreated empty** on terminate (`DeleteOnTermination=true`)
- No automated EBS snapshot policy for pod2 in this account

---

## Baseline files

| File | Contents |
|---|---|
| `captured-at.json` | Timestamp + instance ID list |
| `ec2-instances-summary.json` | Instance table |
| `ec2-instances-full.json` | Full describe-instances |
| `ebs-volumes.json` | Attached volumes |
| `ebs-volumes-orphaned.json` | Detached available volumes |
| `asg-settings.json` | Live ASG config |
| `target-group-health.json` | ELB health at capture |
| `load-balancers.json` | ALB inventory |
| `target-groups.json` | TG inventory |
| `rds-cluster.json` | Aurora cluster |
| `elastic-ips.json` | EIPs |
| `amis.json` | AMIs in use |
| `route53-oms-pod2-dev-local.json` | DNS records |

---

## Refresh baseline

```powershell
cd C:\PROD\ConnectorSuite\tickets\DCOMS-29691-pod2dev-ec2-shutdown-restart-validation\scripts
.\fetch-baseline.ps1 -IncludeTargetHealth
```

Script auto-discovers `oms-pod2-dev-*` instances (no hardcoded IDs).

---

## Related docs

- Recovery runbook: `../runbook/post-termination-recovery.md`
- Post-validation: `../test-results/02-post-shutdown-validation.md`
- SSM inventory: `../../oms_ec2_connector/.env.pod2dev`
