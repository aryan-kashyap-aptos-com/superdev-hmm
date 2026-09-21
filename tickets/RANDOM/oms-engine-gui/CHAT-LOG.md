## 2026-09-21 — OMS Engine UX overhaul

**Status when closed:** in progress

- Fix SSM list dir PowerShell `Sort-Object` parser error; friendly error dialog + activity colors
- UI polish: wider sidebar, health bar, dark toolbar buttons, zebra tables, host pills/tooltips
- SFTP tab (paramiko), inventory `sftp` blocks, Connect + browse + download with progress bar
- SSM chunked download (>8MB) with transfer progress; IIS pool-state poll + row coloring (site + pool)
- Rebranded GUI to OMS Engine; dark theme, sidebar hosts, tab counts, activity dock
- IIS green/red status tags; start/stop uses live SSM polling (no fixed 5s sleep)
- Parallel refresh (host ping + Toro/IIS loads); deferred BIOS serial
- Files tab: SSM directory browse + download to local PC (≤8 MB per file)
- Detection rules dialog + `env_detection.py` heuristics for OMS tenants
- Files touched: `oms_shared_ops_gui/app.py`, `theme.py`, `env_detection.py`, `ssm_runner.py`, `display_utils.py`, `README.md`, `docs/oms-engine-ui-reference.html`
