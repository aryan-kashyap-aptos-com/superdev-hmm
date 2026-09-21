# Shutdown log - oms-pod2-dev

**Ticket:** DCOMS-29691  
**Action:** Stop all 7 EC2 instances (off-hours cost-saving test)  
**Initiated:** 2026-09-04  
**Approved by:** User confirmed via chat  

## Instances stopped

| Name | Instance ID | State at stop |
|---|---|---|
| oms-pod2-dev-content | i-05b829a2f1fd2d7b9 | stopping → stopped |
| oms-pod2-dev-services | i-077bb903286497148 | stopping → stopped |
| oms-pod2-dev-sitemanager | i-05692759bfaaa9cc3 | stopping → stopped |
| oms-pod2-dev-api | i-0548397f26e0277c5 | stopping → stopped |
| oms-pod2-dev-toronado | i-0ebec6c5bc911d854 | stopping → stopped |
| oms-pod2-dev-BastionHost | i-0b489a48f31463d74 | stopping → stopped |
| oms-pod2-dev-rds-migration-host | i-0f2a63e597d421e39 | stopping → stopped |

## Command used

```powershell
aws ec2 stop-instances --instance-ids i-05b829a2f1fd2d7b9 i-077bb903286497148 i-05692759bfaaa9cc3 i-0548397f26e0277c5 i-0b489a48f31463d74 i-0ebec6c5bc911d854 i-0f2a63e597d421e39
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
