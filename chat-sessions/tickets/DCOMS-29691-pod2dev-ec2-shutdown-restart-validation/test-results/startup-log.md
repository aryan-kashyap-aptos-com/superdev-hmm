# Startup log - oms-pod2-dev

**Ticket:** DCOMS-29691  
**Action:** Restore after ASG scale-to-0 shutdown  
**Initiated:** 2026-09-04  

## Restore command

```powershell
.\scripts\restore-asg-capacity.ps1
```

## New instance IDs (post-restore)

| Tier | Instance ID | ASG health |
|---|---|---|
| oms-pod2-dev-content | i-0d23caf16cd2c5adb | Healthy |
| oms-pod2-dev-services | i-0f603ed7f8f947bd7 | Healthy |
| oms-pod2-dev-sitemanager | i-036505377f8ad5c6e | Healthy |
| oms-pod2-dev-api | i-02b70bcb094c2dcec | Healthy |
| oms-pod2-dev-toronado | i-0aee83fe4726581e4 | Healthy |
| oms-pod2-dev-BastionHost | i-0b489a48f31463d74 | running (same instance, was stopped) |
| oms-pod2-dev-rds-migration-host | i-0f2a63e597d421e39 | running (same instance, was stopped) |

All 5 ASGs restored to saved capacity (min/max/desired from `asg-settings-before-shutdown.json`).

## Post-restart validation (pending)

- [ ] Site Manager
- [ ] Order flow
- [ ] Compare to `01-pre-shutdown-validation.md`
