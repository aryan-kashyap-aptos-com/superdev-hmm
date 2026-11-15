# Safe EC2 stop/start — oms-pod2-dev

**Ticket:** DCOMS-29691  
**Use when:** Off-hours cost saving without losing IIS/content/config.

## Do not use

- `scale-asg-to-zero.ps1` — **terminates** instances
- `restore-asg-capacity.ps1` — only after scale-to-0 terminate

## Shutdown (end of day)

```powershell
cd C:\PROD\ConnectorSuite\tickets\DCOMS-29691-pod2dev-ec2-shutdown-restart-validation\scripts

# Optional: refresh instance IDs in baseline first
.\fetch-baseline.ps1

.\stop-pod2-dev-safe.ps1
```

**What it does:**

1. Suspends ASG `Launch`, `ReplaceUnhealthy`, `HealthCheck` on all 5 ASGs
2. Does **not** change min/max/desired
3. Stops all 7 `oms-pod2-dev-*` instances
4. Saves state to `test-results/safe-shutdown-state.json`

## Startup (next day)

```powershell
.\start-pod2-dev-safe.ps1
```

**What it does:**

1. Starts the **same** instance IDs from saved state
2. Waits for `running`
3. Restores normal ASG suspended processes from `test-results/asg-settings-before-shutdown.json`

**No** OMS-App-Deploy or DFS required after a clean stop/start.

## Verify

- SM login: https://oms-pod2-dev-sm.dev.eom.aptos.io/backadmin/login.aspx
- SSM: `python oms_ec2.py --env .env.pod2dev list`

## What still costs money while stopped

RDS, ALBs, NAT, EBS storage, ECS (if running).
