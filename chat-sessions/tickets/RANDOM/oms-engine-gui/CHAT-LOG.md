## 2026-09-22 — Feedback: SFTP out, Parameter Store, logs/files UX

**Status when closed:** done

- Git commit `b277ecf` (prior OMS Engine expansion); follow-up commit for this feedback
- Removed SFTP tab and paramiko; full-file preview via chunked SSM; downloads to `Downloads\OMS Engine`
- Logs: ShopLogic on content only, 1,500-line tails; CloudWatch scan window selector
- Site Manager: Tenant sites filter tooltip; Stop/Start/Restart site buttons + selection hint
- Parameter Store tab (list/edit/create); bastion IP in sidebar; removed EC2 IDs toolbar button
- Files touched: `oms_shared_ops_gui/app.py`, `parameter_store.py`, `inventory.json`, `inventory_io.py`, `cloudwatch_logs.py`, `ssm_runner.py`, `README.md`, deleted `sftp_*.py`

## 2026-09-21 — OMS Engine UX overhaul

**Status when closed:** done

- Fix SSM list dir PowerShell `Sort-Object` parser error; friendly error dialog + activity colors
- UI polish: wider sidebar, health bar, dark toolbar buttons, zebra tables, host pills/tooltips
- SSM chunked download (>8MB) with transfer progress; IIS pool-state poll + row coloring
- Rebranded GUI to OMS Engine; dark theme, sidebar hosts, tab counts, activity dock
- Files tab: SSM directory browse + download; Detection rules + `env_detection.py`
