# DCOMS-29691 - pod2dev EC2 shutdown/restart validation

Working area for [DCOMS-29691](https://aptos.atlassian.net/browse/DCOMS-29691): validate oms-pod2-dev stability across a full EC2 shutdown/restart cycle, document findings, build the recovery runbook, and track any infra or config changes made along the way.

## Folder structure

```
DCOMS-29691-pod2dev-ec2-shutdown-restart-validation/
  README.md                          # This file
  baseline/                          # AWS inventory (refresh after recovery)
    captured-at.json                 # Capture timestamp + instance IDs
    backup-summary.md
    ec2-instances-summary.json
    ec2-instances-full.json
    ebs-volumes.json
    ebs-volumes-orphaned.json
    asg-settings.json
    target-group-health.json         # when using -IncludeTargetHealth
    rds-cluster.json
    rds-cluster-snapshots.json
    elastic-ips.json
    load-balancers.json
    target-groups.json
    amis.json
    route53-oms-pod2-dev-local.json
  scripts/                           # Automation and repeatable commands
    fetch-baseline.ps1
    stop-pod2-dev-safe.ps1           # Off-hours shutdown (suspend ASG + stop)
    start-pod2-dev-safe.ps1          # Morning startup (same instance IDs)
  runbook/
    safe-stop-start.md               # Safe stop/start procedure
    post-termination-recovery.md     # Recovery after accidental terminate
  test-results/
    01-pre-shutdown-validation.md    # SM + order flow pass (before shutdown)
    02-post-shutdown-validation.md # (after restart - to be completed)
  # Add as needed:
  # runbook/                         # Recovery steps if restart fails
  # changes/                         # Config or infra modifications made during validation
```

## Quick start

Requires AWS CLI with access to account `123456789012` (us-east-1).

```powershell
# Re-collect all baseline data
.\scripts\fetch-baseline.ps1

# Include target group health checks
.\scripts\fetch-baseline.ps1 -IncludeTargetHealth

# Safe off-hours shutdown / next-day startup (see runbook/safe-stop-start.md)
.\scripts\stop-pod2-dev-safe.ps1
.\scripts\start-pod2-dev-safe.ps1
```

## Environment scope

7 EC2 instances in `oms-pod2-dev`:

| Instance | Role |
|---|---|
| oms-pod2-dev-content | Content server |
| oms-pod2-dev-services | Services server |
| oms-pod2-dev-sitemanager | Site manager |
| oms-pod2-dev-api | API server |
| oms-pod2-dev-toronado | Toronado app |
| oms-pod2-dev-BastionHost | Bastion (public IP) |
| oms-pod2-dev-rds-migration-host | RDS migration utility |

Plus Aurora PostgreSQL cluster `oms-pod2-dev-aurora`, 6 load balancers, and Route53 zone `oms-pod2-dev.local`.

## Key finding

RDS has automated 7-day backups. **EBS volumes have no automated snapshots in this account.** Create manual snapshots before the shutdown test (see `baseline/backup-summary.md`).

## Ticket acceptance criteria

- [ ] Test executed and results logged
- [ ] Recovery steps documented for any failures
- [ ] Runbook produced and attached to ticket
- [ ] Findings inform v1 infra cost-reduction feasibility
