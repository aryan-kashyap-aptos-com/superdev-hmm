"""Builds one standalone report.html from everything recorded during a run (see record.py): every ad hoc
command, every scenario step, every crawled page, in the order it really happened, each with a sequential
test id, its own observation, timing, a screenshot where one was taken, and the network calls it made.

Open the file directly (no server, no Chrome, no Playwright needed) any time after the run is over - that
is the point of it: a reviewable record of the whole session, for yourself later or for showing someone else.

The page itself (layout, charts, filtering, the steps/network tabs, PDF export) lives in report_template.html
as a static asset - this module's only job is to compute the run's data (events, counts, a short-lived build
id, the run's own fixed id from plan.md) and substitute it into that template's placeholders. Keeping the
template a plain .html file (not an f-string) means its own CSS/JS braces never fight with Python's.
"""
import json
import platform
import re
import uuid
from datetime import datetime
from pathlib import Path

import core
import record

RESULTS = ["Verified", "Issue found", "Could not verify", "Not tested"]
STATUS_COLOR = {"Verified": "#1e9b55", "Issue found": "#dc3a3f", "Could not verify": "#c27a0a", "Not tested": "#8e8e93"}
_TS_FMT = "%Y-%m-%d %H:%M:%S"
_TEMPLATE_PATH = Path(__file__).resolve().parent / "report_template.html"


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _safe_json(data):
    """json.dumps, with "</" escaped so a recorded message or URL containing "</script" can never break out
    of the page's own <script> block."""
    return json.dumps(data).replace("</", "<\\/")


_OS_FAMILY = {"Windows": "windows", "Darwin": "mac", "Linux": "linux"}


def _host_label():
    """A friendly "this machine" string for the report header, plus a normalized OS family the template uses
    to pick an icon - matched on platform.system(), not on this label text, so Linux/macOS/other all get
    their own icon instead of silently falling into the Windows-or-generic choice this used to be."""
    system = platform.system()
    family = _OS_FAMILY.get(system, "other")
    if family == "windows":
        label = f"Windows {platform.release()}"
    elif family == "mac":
        ver = platform.mac_ver()[0]
        label = f"macOS {ver}" if ver else "macOS"
    elif family == "linux":
        label = f"Linux {platform.release().split('-')[0]}" if platform.release() else "Linux"
    else:
        label = system or "Unknown OS"
    return label, family


def _display_title(run):
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", run)
    words = name.replace("-", " ").replace("_", " ").split()
    return " ".join(w.upper() if w.lower() == "qa" else w.capitalize() for w in words) or run


def build(run, out_path=None):
    events = record.read_events(run)
    if not events:
        raise core.c.ConnectorError(
            f"No recorded events for run '{run}' yet.",
            "Events are written by ad hoc commands, `play`, and `crawl` while this run is active (--run "
            f"{run}, or make it the active run with qa-tester/test-run.py use).")
    for e in events:
        e.setdefault("task", "")
    counts = {}
    for e in events:
        if e.get("result"):
            counts[e["result"]] = counts.get(e["result"], 0) + 1
    site = None
    try:
        site = (core.run_login(run) or {}).get("site")
    except Exception:
        pass
    if not site:
        # An auto-named session run (e.g. `scenario-<timestamp>`, from `play` with no --run) has no plan.md
        # of its own, so run_login finds nothing - fall back to whichever site was actually allowed when it
        # ran (the active run's, or environments.md's), rather than leaving the report's Site field blank.
        try:
            site = core.site().get("url")
        except Exception:
            pass
    out_path = Path(out_path) if out_path else core.QA / "runs" / run / "report.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    build_id = uuid.uuid4().hex[:6]
    built_at = datetime.now().strftime(_TS_FMT)
    rid = core.run_id(run)
    host_label, os_family = _host_label()
    meta = {
        "run": run, "site": site or "", "started": events[0]["ts"], "finished": events[-1]["ts"],
        "host": host_label, "os": os_family, "runner": "local", "build": build_id, "generated": built_at,
    }
    if rid:
        meta["rid"] = rid
    out_path.write_text(_html(run, meta, events, build_id, built_at, rid), encoding="utf-8")
    try:
        build_pdf(run, meta, events, counts, out_path.with_name("report.pdf"))
    except Exception as e:
        print(f"(Could not build report.pdf: {e})")
    return out_path, events, counts, build_id, built_at


def _html(run, meta, events, build_id, built_at, rid):
    built_dt = datetime.strptime(built_at, _TS_FMT)
    built_short = f"{built_dt.day} {built_dt.strftime('%b %Y, %H:%M')}"
    run_id_sidebar = f'Run <span title="A fixed id for this run itself, from plan.md. Stays the same across every rebuild of this report.">{rid}</span><br>' if rid else ""
    run_id_foot = f"Run {rid} &middot; " if rid else ""

    page = _TEMPLATE_PATH.read_text(encoding="utf-8")
    subs = {
        "__QA_TITLE__": _esc(_display_title(run)),
        "__QA_HOST_NAME__": _esc(meta["host"]),
        "__QA_HOST_SUB__": f"{meta['runner'].capitalize()} runner",
        "__QA_RUN_NAME__": _esc(run),
        "__QA_RUN_ID_LINE__": run_id_sidebar,
        "__QA_RUN_ID_FOOT__": run_id_foot,
        "__QA_BUILD_ID__": build_id,
        "__QA_BUILT_SHORT__": built_short,
        "__QA_BUILT_FULL__": built_at,
        "__QA_EVENTS_JSON__": _safe_json(events),
        "__QA_META_JSON__": _safe_json(meta),
    }
    for token, value in subs.items():
        page = page.replace(token, value)
    return page


def _suite_name(task):
    name = re.sub(r"^\d+-", "", task or "").replace("-", " ")
    return name[:1].upper() + name[1:] if name else "General"


def _suite_no(task):
    m = re.match(r"^(\d+)-", task or "")
    return m.group(1) if m else None


def _group_cases(events):
    """One entry per test case, holding only its LAST attempt (a case can run more than once if the same
    scenario is replayed into a run) - the PDF is a point-in-time deliverable to hand someone, not an
    attempt-history browser, so only the final attempt is worth printing. Ad hoc/session commands are left
    out entirely: they're debugging trail, not something you'd hand to someone else."""
    order, by_key, steps_by_key = [], {}, {}
    for e in events:
        if e.get("kind") == "step" and e.get("case_id"):
            k = (e.get("task") or "", e["case_id"])
            steps_by_key.setdefault(k, []).append(e)
        elif e.get("kind") == "case":
            k = (e.get("task") or "", e["case_id"])
            if k not in by_key:
                order.append(k)
            shots = e.get("screenshot") or []
            by_key[k] = {"task": k[0], "id": e["case_id"], "title": e["text"], "result": e["result"],
                         "steps": steps_by_key.get(k, []), "screenshot": shots if isinstance(shots, list) else [shots]}
            steps_by_key[k] = []
    return [by_key[k] for k in order if k in by_key]


def _pdf_html(run, meta, cases, counts, total):
    rate = round(100 * counts.get("Verified", 0) / total) if total else 0
    suites, seen = [], []
    for c in cases:
        if c["task"] not in seen:
            seen.append(c["task"])
            suites.append({"task": c["task"], "cases": []})
        next(s for s in suites if s["task"] == c["task"])["cases"].append(c)

    def badge(result):
        color = STATUS_COLOR.get(result, "#8e8e93")
        return f'<span class="badge" style="color:{color};border-color:{color}33;background:{color}14">{_esc(result)}</span>'

    def step_html(s):
        color = STATUS_COLOR.get(s.get("result"), "#8e8e93")
        msg = s.get("msg") or ""
        ex = re.match(r"^Expected:\s*(.*?)\.?\s*Saw:\s*(.*)$", msg, re.S)
        if ex:
            msg_html = f'<div class="smsg"><b>Expected</b> {_esc(ex.group(1))}<br><b>Saw</b> <span class="saw">{_esc(ex.group(2))}</span></div>'
        elif msg:
            msg_html = f'<div class="smsg">{_esc(msg)}</div>'
        else:
            msg_html = ""
        shots = s.get("screenshot") or []
        shots = shots if isinstance(shots, list) else [shots]
        shots_html = "".join(f'<img class="shot" src="{_esc(p)}">' for p in shots)
        return (f'<div class="step"><span class="dot" style="background:{color}"></span>'
                f'<div class="stx"><code>{_esc(s.get("text", ""))}</code>{msg_html}{shots_html}</div></div>')

    def case_html(c):
        color = STATUS_COLOR.get(c["result"], "#8e8e93")
        steps = c["steps"]
        verified = sum(1 for s in steps if s.get("result") == "Verified")
        problem_steps = [s for s in steps if s.get("result") not in ("Verified", "Not tested")]
        body = "".join(step_html(s) for s in problem_steps) if problem_steps else ""
        shots = c.get("screenshot") or []
        shots_html = "".join(f'<img class="shot final-img" src="{_esc(p)}">' for p in shots)
        final_shot = (f'<div class="final"><div class="final-lbl">Final state</div>{shots_html}</div>') if shots else ""
        return (f'<div class="case" style="border-left-color:{color}">'
                f'<div class="case-h"><span class="cid">{_esc(c["id"])}</span>'
                f'<span class="ct">{_esc(c["title"])}</span>{badge(c["result"])}</div>'
                f'<div class="csub">{verified} of {len(steps)} steps passed</div>'
                f'{body}{final_shot}</div>')

    def suite_html(s):
        no = _suite_no(s["task"])
        no_html = f'<span class="sno">{no}</span>' if no else ""
        return (f'<div class="suite"><div class="suite-h">{no_html}'
                f'<span class="snm">{_esc(_suite_name(s["task"]))}</span></div>'
                f'{"".join(case_html(c) for c in s["cases"])}</div>')

    suite_blocks = "".join(suite_html(s) for s in suites)

    site_short = re.sub(r"^https?://", "", meta["site"]).rstrip("/")
    rid_line = f'Run {_esc(meta["rid"])} &middot; ' if meta.get("rid") else ""
    title = _display_title(run)

    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{_esc(title)}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font:13px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#1d1d1f;background:#fff}}
.wrap{{padding:6mm 2mm}}
.eyebrow{{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:#8e8e93;font-weight:600}}
h1{{font-size:28px;font-weight:700;letter-spacing:-.02em;margin:6px 0 8px}}
.meta{{color:#6e6e73;font-size:12px}}
.meta i{{font-style:normal;margin:0 7px;color:#c7c7cc}}
.summary{{display:flex;gap:14px;margin:20px 0 26px;align-items:stretch}}
.hero{{flex:1;border:1px solid #e5e5e7;border-radius:12px;padding:16px 20px;display:flex;align-items:center;gap:18px}}
.hero b{{font-size:34px;font-weight:700;letter-spacing:-.03em}}
.hero span{{display:block;font-size:11px;color:#8e8e93;text-transform:uppercase;letter-spacing:.06em;margin-top:2px}}
.stat{{flex:1;border:1px solid #e5e5e7;border-radius:12px;padding:12px 16px}}
.stat b{{display:block;font-size:22px;font-weight:700}}
.stat span{{font-size:11px;color:#8e8e93;text-transform:uppercase;letter-spacing:.05em}}
.suite{{margin-top:22px}}
.suite-h{{display:flex;align-items:center;gap:9px;margin-bottom:9px}}
.sno{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:10.5px;color:#8e8e93;border:1px solid #d6d6d8;border-radius:5px;padding:1px 5px}}
.snm{{font-size:14px;font-weight:700}}
.case{{border:1px solid #e5e5e7;border-left-width:4px;border-radius:9px;padding:12px 16px;margin-bottom:10px;page-break-inside:avoid;break-inside:avoid}}
.case-h{{display:flex;align-items:center;gap:9px}}
.cid{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;color:#8e8e93}}
.ct{{font-weight:600;font-size:13.5px;flex:1}}
.badge{{font-size:10.5px;font-weight:600;border:1px solid;border-radius:999px;padding:2px 9px}}
.csub{{font-size:11.5px;color:#8e8e93;margin:3px 0 0 0}}
.step{{display:flex;gap:9px;margin-top:10px;padding-top:10px;border-top:1px solid #f0f0f1}}
.dot{{width:7px;height:7px;border-radius:50%;margin-top:4px;flex:none}}
.stx code{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11.5px;background:#f5f5f7;padding:1px 5px;border-radius:4px}}
.smsg{{font-size:11.5px;color:#48484a;margin-top:4px;line-height:1.5}}
.smsg b{{color:#8e8e93;font-weight:600}}
.saw{{color:#dc3a3f}}
.shot{{display:block;max-width:260px;max-height:170px;object-fit:cover;object-position:top;border:1px solid #e5e5e7;
  border-radius:8px;margin-top:8px}}
.final{{margin-top:12px;padding-top:10px;border-top:1px solid #f0f0f1}}
.final-lbl{{font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;color:#8e8e93;margin-bottom:6px}}
.final-img{{max-width:340px;max-height:200px}}
</style></head><body><div class="wrap">
<div class="eyebrow">Quality report</div>
<h1>{_esc(title)}</h1>
<div class="meta">{_esc(site_short)}<i>&middot;</i>{_esc(meta['started'])} - {_esc(meta['finished'])}<i>&middot;</i>{len(cases)} test cases<i>&middot;</i>{total} checks</div>
<div class="summary">
<div class="hero"><b>{rate}%</b><div><span>Pass rate</span></div></div>
<div class="stat"><b style="color:{STATUS_COLOR['Verified']}">{counts.get('Verified', 0)}</b><span>Verified</span></div>
<div class="stat"><b style="color:{STATUS_COLOR['Issue found']}">{counts.get('Issue found', 0)}</b><span>Issue found</span></div>
<div class="stat"><b style="color:{STATUS_COLOR['Could not verify']}">{counts.get('Could not verify', 0)}</b><span>Could not verify</span></div>
</div>
{suite_blocks}
</div></body></html>"""


def _pdf_via_page(page, src_uri, out_path):
    page.goto(src_uri)
    page.pdf(path=str(out_path), format="A4", print_background=True,
             margin={"top": "16mm", "bottom": "14mm", "left": "14mm", "right": "14mm"},
             display_header_footer=True, header_template="<div></div>",
             footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#9a9a9a;'
                             'font-family:-apple-system,Arial,sans-serif;padding:0 14mm">'
                             '<span class="title"></span> &middot; Page <span class="pageNumber">'
                             '</span> of <span class="totalPages"></span></div>')


def build_pdf(run, meta, events, counts, out_path):
    """A standalone, purpose-built PDF - not a browser print of the interactive dashboard. Rendered from its
    own plain static template (no sidebar, no JS, light theme only - a document meant to be handed to
    someone, not a screenshot of the tool's own UI).

    Uses the real system Chrome (core.find_chrome(), the same one the rest of this tool drives), not
    Playwright's own bundled Chromium/headless-shell builds - those are a separate download this project
    never asked for (`playwright install`), and failing on that would make PDF export depend on a step
    nothing else here needs. Reuses the already-running test browser over CDP when it's open; otherwise
    launches a short-lived headless copy of system Chrome just for this render."""
    import subprocess
    import time
    import urllib.request
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    cases = _group_cases(events)
    total = len(events)
    src_path = out_path.with_name("_pdf_source.html")
    src_path.write_text(_pdf_html(run, meta, cases, counts, total), encoding="utf-8")
    src_uri = src_path.resolve().as_uri()
    try:
        with sync_playwright() as p:
            if core.alive():
                browser = p.chromium.connect_over_cdp(core.CDP)
                page = browser.new_page()
                try:
                    _pdf_via_page(page, src_uri, out_path)
                finally:
                    page.close()
            else:
                port = core.PORT + 171
                proc = subprocess.Popen(
                    [core.find_chrome(), f"--remote-debugging-port={port}", "--headless=new",
                     "--no-first-run", "--no-default-browser-check", "about:blank"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    cdp = f"http://127.0.0.1:{port}"
                    for _ in range(40):
                        try:
                            urllib.request.urlopen(cdp + "/json/version", timeout=1).read()
                            break
                        except OSError:
                            time.sleep(0.25)
                    else:
                        raise core.c.ConnectorError("The temporary PDF-rendering browser did not start.", "")
                    browser = p.chromium.connect_over_cdp(cdp)
                    page = browser.new_page()
                    _pdf_via_page(page, src_uri, out_path)
                finally:
                    proc.terminate()
    finally:
        src_path.unlink(missing_ok=True)
    return out_path
