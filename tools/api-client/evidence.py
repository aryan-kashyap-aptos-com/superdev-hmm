"""Screenshot evidence for an API call, built the same way the qa-tester reports are:
a static HTML card rendered server-side, printed to PNG with Playwright.

Complements qa-tester: a UI step gets a screenshot automatically; an API step
run through Claude's own tool calls doesn't. This gives API steps the same
kind of visual proof, and can drop the PNG straight into an existing
qa-tester run/task's screenshots/ folder.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE_DIR = ROOT / "evidence"
QA_RUNS_DIR = ROOT.parent.parent / "qa-tester" / "runs"
EVIDENCE_DIR.mkdir(exist_ok=True)

CARD_HTML = """<!doctype html><html><head><meta charset="utf-8">
<style>
body{{margin:0;background:#0c0c0d;font:14px/1.6 -apple-system,"Segoe UI",Arial,sans-serif;color:#f5f5f7;padding:28px}}
.card{{max-width:820px;margin:0 auto;background:#161617;border:1px solid rgba(255,255,255,.07);border-radius:16px;padding:22px 26px}}
.row{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.method{{font-weight:700;font-size:13px;padding:3px 9px;border-radius:7px;background:rgba(90,162,255,.13);color:#5aa2ff}}
.url{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;color:#a1a1a6;word-break:break-all}}
.status{{margin-left:auto;font-weight:600;font-size:13px;padding:3px 10px;border-radius:999px}}
.status.ok{{background:rgba(61,210,127,.12);color:#3dd27f}}
.status.bad{{background:rgba(255,95,90,.12);color:#ff5f5a}}
.meta{{color:#6e6e73;font-size:12.5px;margin-top:8px}}
h4{{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:#6e6e73;margin:18px 0 8px}}
pre{{background:#1c1c1e;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:14px 16px;
     font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;white-space:pre-wrap;word-break:break-word;margin:0;max-height:480px;overflow:auto}}
</style></head><body>
<div class="card">
  <div class="row">
    <span class="method">{method}</span>
    <span class="url">{url}</span>
    <span class="status {status_class}">{status}</span>
  </div>
  <div class="meta">{timing}</div>
  <h4>Request headers</h4><pre>{req_headers}</pre>
  {req_body_block}
  <h4>Response body</h4><pre>{resp_body}</pre>
</div>
</body></html>"""


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "request"


def build_card_html(entry: dict) -> str:
    req = entry.get("request", {})
    ok = entry.get("ok", False)
    status = entry.get("status", "ERR")
    status_class = "ok" if ok and 200 <= int(status or 0) < 400 else "bad"
    req_headers = json.dumps(req.get("headers", {}), indent=2)
    resp_body = entry.get("body_text")
    if resp_body is None:
        resp_body = json.dumps(entry.get("body_json"), indent=2) if entry.get("body_json") is not None else entry.get("error", "")
    req_body_block = ""
    if req.get("json") is not None or req.get("data"):
        body = json.dumps(req.get("json"), indent=2) if req.get("json") is not None else str(req.get("data"))
        req_body_block = f"<h4>Request body</h4><pre>{html.escape(body)}</pre>"
    return CARD_HTML.format(
        method=html.escape(req.get("method", "")),
        url=html.escape(req.get("resolved_url") or req.get("url", "")),
        status_class=status_class,
        status=f"{status} {html.escape(str(entry.get('reason') or ''))}".strip(),
        timing=f"{entry.get('elapsed_ms', '?')} ms &middot; {entry.get('size_bytes', '?')} bytes",
        req_headers=html.escape(req_headers),
        req_body_block=req_body_block,
        resp_body=html.escape(str(resp_body)),
    )


def capture(entry: dict, request_name: str) -> Path:
    from playwright.sync_api import sync_playwright

    html_doc = build_card_html(entry)
    stamp = Path(request_name).stem
    tmp_html = EVIDENCE_DIR / f"_tmp_{_slug(request_name)}.html"
    tmp_html.write_text(html_doc, encoding="utf-8")
    out_path = EVIDENCE_DIR / f"{_slug(request_name)}.png"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 900, "height": 800})
            page.goto(tmp_html.resolve().as_uri())
            page.screenshot(path=str(out_path), full_page=True)
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)
    return out_path


def list_runs() -> list[dict]:
    if not QA_RUNS_DIR.exists():
        return []
    out = []
    for run_dir in sorted(QA_RUNS_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        tasks_dir = run_dir / "tasks"
        tasks = [t.name for t in sorted(tasks_dir.iterdir())] if tasks_dir.exists() else []
        out.append({"run": run_dir.name, "tasks": tasks})
    return out


def copy_into_run(evidence_path: Path, run: str, task: str, label: str) -> Path:
    target_dir = QA_RUNS_DIR / run / "tasks" / task / "screenshots"
    target_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(target_dir.glob("[0-9][0-9]-*.png"))
    next_n = (int(existing[-1].name[:2]) + 1) if existing else 1
    target = target_dir / f"{next_n:02d}-{_slug(label)}.png"
    shutil.copy(evidence_path, target)
    return target
