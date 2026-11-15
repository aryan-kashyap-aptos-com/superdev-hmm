## 2026-09-20 — Stale Name-gap audit (safe delete guidance)

- Ran `audit-stale-missing-name.py`: 36 orphan API GW tag records; 21 failed CF stacks (ROLLBACK/DELETE_FAILED); 9 managed EventBridge rules; SG in use (20 ENIs).

## 2026-09-20 — Terminal clear between setup / results

- `clear_screen()` after menus and after scan (TTY); `--no-clear` to disable.

## 2026-09-20 — Faster single-pass scan + cleaner TTY UI

**Status when closed:** done

- Scan: one Resource Groups API pagination for all types (was ~45 calls/region); lazy API GW names; ECS check off by default (`--ecs-check`).
- UI: banner, sections, spinner, progress bar, 20 default workers.

## 2026-09-20 — Interactive wizard, scan-then-apply, threading

**Status when closed:** done

- Reworked flow: menu (dry-run vs apply, region / all regions), scan report with missing counts, then apply with thread pool; final applied/failed sections.
- Files: `apply-missing-name-tags.py`, `CHAT-LOG.md`

## 2026-09-20 — Script UX: color and ECS wording

**Status when closed:** done

- Improved `apply-missing-name-tags.py`: ANSI colors (Windows VT), applied-resource table, failed summary by type/error, `--verbose` / `--no-color`, `applied.jsonl` per run.
- Clarified ECS post-check: counts unique task defs attached to ECS services; `0/223` meant all 223 have Name (not "0 applied").
- Files touched: `tickets/RANDOM/name-tag-runs/apply-missing-name-tags.py`, `CHAT-LOG.md`
