# Shutdown log - oms-pod2-dev

**Ticket:** DCOMS-29691  
**Action:** Stop all 7 EC2 instances (off-hours cost-saving test)  
**Initiated:** 2026-09-04  
**Approved by:** User confirmed via chat  

## Instances stopped

| Name | Instance ID | State at stop |
|---|---|---|
| oms-pod2-dev-content | i-00000000000000046 | stopping → stopped |
| oms-pod2-dev-services | i-00000000000000047 | stopping → stopped |
| oms-pod2-dev-sitemanager | i-00000000000000044 | stopping → stopped |
| oms-pod2-dev-api | i-00000000000000045 | stopping → stopped |
| oms-pod2-dev-toronado | i-00000000000000048 | stopping → stopped |
| oms-pod2-dev-BastionHost | i-00000000000000042 | stopping → stopped |
| oms-pod2-dev-rds-migration-host | i-00000000000000043 | stopping → stopped |

## Command used

```powershell
aws ec2 stop-instances --instance-ids i-00000000000000046 i-00000000000000047 i-00000000000000044 i-00000000000000045 i-00000000000000042 i-00000000000000048 i-00000000000000043
```

## Not stopped

- RDS Aurora (`oms-pod2-dev-aurora`)
- ECS Fargate services
- ALBs / NAT / Elastic IPs

## ASG scale-down (2026-09-04)

EC2 `stop-instances` alone was insufficient - ASGs replaced stopped instances (notably toronado).

**Saved pre-shutdown ASG settings:** `test-results/asg-settings-before-shutdown.json`

| ASG | Restored settings (min/max/desired) |
|---|---|
| oms-pod2-dev-sm-asg | 1 / 3 / 1 |
| oms-pod2-dev-api-asg | 1 / 3 / 1 |
| oms-pod2-dev-cnt-asg | 1 / 3 / 1 |
| oms-pod2-dev-svc-asg | 1 / 3 / 1 |
| oms-pod2-dev-toronado-asg | 1 / 1 / 1 |

All 5 ASGs scaled to **0/0/0**. Restore with `scripts/restore-asg-capacity.ps1`.

## Restart (pending)

```powershell
.\scripts\restore-asg-capacity.ps1
```

After restart: re-test SM + order flow, record in `02-post-shutdown-validation.md`.
