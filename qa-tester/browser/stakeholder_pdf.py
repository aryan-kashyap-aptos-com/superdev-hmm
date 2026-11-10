"""The stakeholder summary PDF: three A4 pages a product owner can read in ten seconds.

Page 1  verdict, five KPI tiles, "What we checked" (or "What failed" first, when something did)
Page 2  test-case table (grouped by task) and a page-performance table with bars
Page 3  evidence screenshots and run details

Every NUMBER comes from the run's recorded events (see facts()). The WORDS (title, what the result means,
the "What we checked" boxes, plain-English case titles, screenshot captions) come from an optional
`stakeholder.json` in the run folder, written by whoever ran the test. Wherever that file says [[calls]],
[[ready_min]] and so on, the number is filled in from the events, so text and numbers cannot drift apart.
Without the file, a plain factual summary is generated from the plan and the results.

stakeholder.json (all keys optional):
{
  "title": "Swagger UI (Handlebars) docs page",          one line, about 40 characters
  "short": "Swagger UI Handlebars",                       footer name
  "tasks": {"01": "Swagger UI page", "02": "API definition"},
  "summary": "2-3 plain sentences on what was tested and what it means. May use [[placeholders]].",
  "boxes": [{"heading": "The page loads", "bullets": ["...", "..."]}, ...],   3 boxes, 2-4 bullets each
  "cases": {"01:C1": {"title": "plain title", "expect": "the expected result, specifically"}, ...},   key = task number:case id
  "perf": {"case": "01:C1", "labels": {"/swagger.json": "API definition"}},
  "sources": "Where the expected results come from (file names).",
  "evidence": [{"case": "01:C1", "caption": "<b>What it shows</b>, short detail (C1)"}, ...]   4 to 6
}
Placeholders: cases cases_ok steps checks checks_ok calls failed loads ready_min ready_max slowest_ms
first_load_calls first_load_ok first_load_redirects console_checks net_checks docs_min docs_max
"""
import json
import re
from pathlib import Path

import core

FONT = 'Inter,"Segoe UI",Arial,sans-serif'
MONO = '"JetBrains Mono",Consolas,"Courier New",monospace'
PILL = {"Verified": ("#11693a", "#eaf7ef", "#bfe6cd"), "Issue found": ("#a12a2a", "#fdeeee", "#f1b9b9"),
        "Could not verify": ("#8a5a00", "#fff8e8", "#f1d9a0"), "Not tested": ("#6b7485", "#f3f5f9", "#e3e7ee")}

CSS = """
*{box-sizing:border-box}
body{margin:0;font:9.3pt/1.5 %(font)s;color:#1d2433;background:#fff}
.page{break-after:page;page-break-after:always}
.page:last-child{break-after:auto;page-break-after:auto}
.eyebrow{font-size:7.5pt;letter-spacing:.16em;text-transform:uppercase;color:#6b7485;font-weight:600}
h1{font-size:20pt;line-height:1.2;margin:5px 0 4px;font-weight:700;letter-spacing:-.01em}
.meta{color:#6b7485;font-size:8.8pt}
h2{font-size:12.5pt;margin:20px 0 9px;padding-bottom:5px;border-bottom:1px solid #e3e7ee;font-weight:700}
.banner{margin-top:16px;border-radius:6px;padding:13px 16px 13px 20px;border-left:5px solid}
.banner h3{margin:0 0 5px;font-size:13pt}
.banner p{margin:0;font-size:9.5pt;line-height:1.55}
.ok{background:#eaf7ef;border-color:#1f9d55}.ok h3{color:#11693a}
.warn{background:#fff8e8;border-color:#e0a82e}.warn h3{color:#8a5a00}
.bad{background:#fdeeee;border-color:#dc3a3f}.bad h3{color:#a12a2a}
.kpis{display:flex;gap:10px;margin-top:14px}
.kpi{flex:1;border:1px solid #e3e7ee;border-radius:5px;padding:10px 12px;background:#fafbfd}
.kpi b{display:block;font-size:17pt;line-height:1.15;font-weight:700}
.kpi span{display:block;margin-top:3px;font-size:7.3pt;letter-spacing:.07em;text-transform:uppercase;color:#6b7485}
.g{color:#1f9d55}.a{color:#c27a0a}.r{color:#dc3a3f}
.boxes{display:flex;gap:10px;align-items:stretch}
.box{flex:1;border:1px solid #e3e7ee;border-radius:5px;padding:11px 13px;background:#fff}
.box h4{margin:0 0 6px;font-size:9.6pt}
.box ul{margin:0;padding-left:15px}.box li{margin:0 0 5px}
.fail{border-left:4px solid #dc3a3f;background:#fdeeee;border-radius:5px;padding:10px 14px;margin-bottom:10px}
code,.mono{font-family:%(mono)s;font-size:8.2pt}
table{border-collapse:collapse;width:100%%}
.cases th{font-size:7.3pt;letter-spacing:.07em;text-transform:uppercase;color:#6b7485;text-align:left;padding:5px 8px;border-bottom:1px solid #d5dae4}
.cases td{padding:5px 8px;border-bottom:1px solid #eef0f5;vertical-align:top}
.cases tr.grp td{background:#f3f5f9;font-weight:700;font-size:8.6pt;padding:6px 8px}
.cases td.id{color:#6b7485;width:6%%;font-family:%(mono)s;font-size:8pt}
.cases td.n{white-space:nowrap;text-align:left}
.t{font-weight:700}
.x{color:#6b7485;font-size:8.3pt;margin-top:1px}
.tag{display:inline-block;margin-left:6px;font-size:7pt;font-weight:600;color:#3b4fb8;background:#eef1ff;border-radius:3px;padding:0 5px;vertical-align:1px;white-space:nowrap}
.pill{display:inline-block;font-size:7.8pt;font-weight:700;border:1px solid;border-radius:999px;padding:1px 9px;white-space:nowrap}
.note{color:#6b7485;font-size:8.2pt;margin-top:9px}
.perf td{padding:4px 8px;border-bottom:1px solid #eef0f5;vertical-align:middle}
.perf th{font-size:7.3pt;letter-spacing:.07em;text-transform:uppercase;color:#6b7485;text-align:left;padding:5px 8px;border-bottom:1px solid #d5dae4}
.perf td:nth-child(2){white-space:nowrap}
.perf .mono{font-size:7.6pt}
.bar{height:7px;border-radius:4px;background:#5b8def;min-width:3px}
.ev{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.ev figure{margin:0}
.ev img{display:block;width:100%%;border:1px solid #e3e7ee;border-radius:5px}
.ev figcaption{font-size:8.3pt;margin-top:4px;color:#3a4357}
.run td{padding:8px 10px;border-bottom:1px solid #eef0f5;vertical-align:top;font-size:9.2pt}
.run td:first-child{width:24%%;color:#1d2433}
tr,figure,.box,.fail{break-inside:avoid;page-break-inside:avoid}
""" % {"font": FONT, "mono": MONO}


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt_ms(ms):
    ms = ms or 0
    return f"{ms / 1000:.1f} s" if ms >= 1000 else f"{int(ms)} ms"


def _task_no(task):
    m = re.match(r"^(\d+)-", task or "")
    return m.group(1) if m else ""


def _task_name(task):
    name = re.sub(r"^\d+-", "", task or "").replace("-", " ")
    return name[:1].upper() + name[1:] if name else "General"


def _plan_table(run):
    """{case id: (what, expected, source)} from the plan's "What we will check" table."""
    try:
        text = (core.QA / "runs" / run / "plan.md").read_text(encoding="utf-8")
    except OSError:
        return {}
    out = {}
    for line in text.splitlines():
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.match(r"^C\d+[a-z]?$", cells[0]):
            out[cells[0]] = (cells[1], cells[2], cells[3])
    return out


def _plan_field(run, label):
    try:
        text = (core.QA / "runs" / run / "plan.md").read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"^" + re.escape(label) + r":\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def _bad_call(r):
    s = r.get("s")
    return bool(r.get("f")) or (isinstance(s, int) and s >= 400)


def load_text(run):
    p = core.QA / "runs" / run / "stakeholder.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def facts(events, cases):
    """Every number the PDF shows, computed from the recorded events."""
    steps = [s for c in cases for s in c["steps"]]
    calls = [r for e in events for r in (e.get("net") or [])]
    loads = [s for s in steps if (s.get("text") or "").startswith("open ") and s.get("net")]
    ready, docs, doc_is_slowest = [], [], True
    for s in loads:
        m = re.search(r"ready in ([\d.]+)\s*s", s.get("msg") or "")
        if m:
            ready.append(float(m.group(1)))
        net = s["net"]
        slowest = max(net, key=lambda r: r.get("ms") or 0)
        doc = [r for r in net if (r.get("t") == "document" and (r.get("s") or 0) == 200)]
        if doc:
            docs.append(doc[0].get("ms") or 0)
            if slowest is not doc[0] and (slowest.get("ms") or 0) > (doc[0].get("ms") or 0):
                doc_is_slowest = False
    first = loads[0]["net"] if loads else []
    f = {
        "cases": len(cases), "cases_ok": sum(1 for c in cases if c["result"] == "Verified"),
        "steps": len(steps), "checks": len(events), "checks_ok": sum(1 for e in events if e.get("result") == "Verified"),
        "calls": len(calls), "failed": sum(1 for r in calls if _bad_call(r)), "loads": len(loads),
        "ready_min": f"{min(ready):.1f}" if ready else "", "ready_max": f"{max(ready):.1f}" if ready else "",
        "slowest_ms": max((r.get("ms") or 0 for r in calls), default=0),
        "first_load_calls": len(first), "first_load_ok": sum(1 for r in first if r.get("s") == 200),
        "first_load_redirects": sum(1 for r in first if isinstance(r.get("s"), int) and 300 <= r["s"] < 400),
        "console_checks": sum(1 for s in steps if re.search(r"console", s.get("text") or "", re.I)),
        "net_checks": sum(1 for s in steps if re.search(r"failed network", s.get("text") or "", re.I)),
        "docs_min": min(docs) if docs else "", "docs_max": max(docs) if docs else "",
        "_ready": ready, "_doc_is_slowest": doc_is_slowest,
        "_console_bad": sum(1 for s in steps if re.search(r"console", s.get("text") or "", re.I) and s.get("result") != "Verified"),
    }
    return f


def reconcile(run, events, cases, f, plan):
    """Plain-language notes about anything that does not line up. Printed by the report command, never
    written into the PDF: they are for the person presenting it."""
    notes = []
    if f["steps"] != f["checks"]:
        notes.append(f"The headline counts {f['checks']} checks, but the cases hold {f['steps']} steps. "
                     f"The other {f['checks'] - f['steps']} are the {f['cases']} case-level result rows. "
                     "The PDF uses the headline number.")
    ids = {}
    for c in cases:
        ids.setdefault(c["id"], []).append(_task_no(c["task"]))
    for cid, tasks in ids.items():
        if len(tasks) > 1:
            notes.append(f"Case ID {cid} is used {len(tasks)} times (tasks {', '.join(tasks)}). Kept as written.")
    for c in cases:
        if c["id"] not in plan:
            notes.append(f"Case {c['id']} is not in the plan's check table (shown as 'added during run').")
        if c["result"] != "Verified":
            notes.append(f"Case {c['id']} is '{c['result']}', not Verified.")
    if f["first_load_calls"] and f["first_load_ok"] != f["first_load_calls"]:
        notes.append(f"The first page load made {f['first_load_calls']} calls: {f['first_load_ok']} answered 200 and "
                     f"{f['first_load_redirects']} redirected (3xx). Text must not say all of them were 200.")
    return notes


def _fill(text, f):
    return re.sub(r"\[\[(\w+)\]\]", lambda m: str(f.get(m.group(1), m.group(0))), text or "")


def _pill(word):
    fg, bg, bd = PILL.get(word, PILL["Not tested"])
    return f'<span class="pill" style="color:{fg};background:{bg};border-color:{bd}">{_esc(word)}</span>'


def build_html(run, meta, events, cases, counts, title_fallback, file_name):
    plan = _plan_table(run)
    f = facts(events, cases)
    txt = load_text(run)
    ticket = meta.get("ticket") or ""
    title = txt.get("title") or title_fallback
    short = txt.get("short") or title
    task_names = txt.get("tasks") or {}
    case_text = txt.get("cases") or {}
    n_cases, n_ok = f["cases"], f["cases_ok"]
    issues = [c for c in cases if c["result"] == "Issue found"]
    unverified = [c for c in cases if c["result"] in ("Could not verify", "Not tested")]

    # --- page 1
    if not issues and not unverified:
        cls, head = "ok", f"&#10004; All {n_cases} test cases passed. No issues found."
    elif issues:
        cls, head = "warn", f"{len(issues)} of {n_cases} test cases found issues."
    else:
        cls, head = "warn", f"{len(unverified)} of {n_cases} test cases could not be verified."
    if txt.get("summary"):
        summary = _fill(txt["summary"], f)
    else:
        summary = (f"{n_ok} of {n_cases} test cases passed on {re.sub(r'^https?://', '', meta.get('site') or '').rstrip('/')}. "
                   f"{f['calls']} network calls were recorded and {f['failed']} failed.")
    ready_tile = (f"&lt; {int(float(f['ready_max'])) + 1} s" if f["ready_max"] and float(f["ready_max"]) < 10 else
                  (f"{f['ready_max']} s" if f["ready_max"] else _fmt_ms(sum(s.get('ms') or 0 for c in cases for s in c['steps']))))
    ready_label = "Until page is ready" if f["ready_max"] else "Time in checks"
    err_total = f["failed"] + f["_console_bad"]

    def kpi(val, label, cls_=""):
        return f'<div class="kpi"><b class="{cls_}">{val}</b><span>{label}</span></div>'

    kpis = (kpi(f"{n_ok} / {n_cases}", "Test cases", "g" if n_ok == n_cases else "a")
            + kpi(f"{f['checks_ok']} / {f['checks']}", "Checks", "g" if f["checks_ok"] == f["checks"] else "a")
            + kpi(len(issues), "Issues", "g" if not issues else "r")
            + kpi(err_total, "Failed calls or errors", "g" if not err_total else "r")
            + kpi(ready_tile, ready_label, "g"))

    fail_html = ""
    for c in issues + unverified:
        bad = next((s for s in c["steps"] if s.get("result") not in ("Verified", "Not tested")), {})
        ex = plan.get(c["id"], ("", "", ""))[1]
        fail_html += (f'<div class="fail"><b>{_esc(c["id"])} · {_esc(c["title"])}</b> {_pill(c["result"])}<br>'
                      f'<span class="x">Expected:</span> {_esc(ex or "see the plan")}<br>'
                      f'<span class="x">Happened:</span> {_esc(bad.get("msg") or bad.get("text") or "")}<br>'
                      f'<span class="x">Evidence:</span> <code>{_esc(", ".join(c.get("screenshot") or []) or "no screenshot")}</code></div>')
    fail_block = f"<h2>What failed</h2>{fail_html}" if fail_html else ""

    boxes = txt.get("boxes")
    if not boxes:  # no written text: one box per task, listing what each case checks, from the plan
        boxes = []
        for tno in dict.fromkeys(_task_no(c["task"]) for c in cases):
            items = [(plan.get(c["id"], ("", "", ""))[0] or c["title"]) for c in cases if _task_no(c["task"]) == tno]
            boxes.append({"heading": task_names.get(tno) or _task_name(next(c["task"] for c in cases if _task_no(c["task"]) == tno)),
                          "bullets": items[:4]})
    boxes_html = "".join(f'<div class="box"><h4>{_esc(b["heading"])}</h4><ul>'
                         + "".join(f"<li>{_esc(_fill(x, f))}</li>" for x in b["bullets"]) + "</ul></div>" for b in boxes[:3])

    sess_pos = f"{meta.get('session_pos', '')} of {meta.get('n_sessions', '')}" if meta.get("n_sessions") else ""
    started, finished = meta.get("started", ""), meta.get("finished", "")
    window = f"{started[:10]}, {started[11:16]}&ndash;{finished[11:16]}" if started and finished else ""
    meta_line = " &middot; ".join(x for x in [
        f"Run {_esc(meta['rid'])}" if meta.get("rid") else "",
        f"session {_esc(meta.get('session', ''))}" + (f" ({sess_pos})" if sess_pos else ""),
        f"{_esc(_plan_field(run, 'Environment'))}, local runner ({_esc(meta.get('host', ''))})" if _plan_field(run, "Environment") else "",
        window] if x)

    page1 = f"""<section class="page">
<div class="eyebrow">Quality report{(' &middot; ' + _esc(ticket)) if ticket else ''}</div>
<h1>{_esc(title)}</h1><div class="meta">{meta_line}</div>
<div class="banner {cls}"><h3>{head}</h3><p>{_esc(summary)}</p></div>
<div class="kpis">{kpis}</div>
{fail_block}
<h2>What we checked</h2><div class="boxes">{boxes_html}</div>
</section>"""

    # --- page 2
    rows, last_task = "", None
    by_task = {}
    for c in cases:
        by_task.setdefault(c["task"], []).append(c)
    for task, cs in by_task.items():
        tno = _task_no(task)
        ok = sum(1 for c in cs if c["result"] == "Verified")
        rows += f'<tr class="grp"><td colspan="5">{_esc(tno)} &middot; {_esc(task_names.get(tno) or _task_name(task))} ({ok} of {len(cs)} passed)</td></tr>'
        for c in cs:
            ct = case_text.get(f"{tno}:{c['id']}", {})
            p = plan.get(c["id"])
            t = ct.get("title") or (p[0] if p else c["title"])
            x = ct.get("expect") or (p[1] if p else "")
            tag = "" if p else '<span class="tag">added during run</span>'
            verified = sum(1 for s in c["steps"] if s.get("result") == "Verified")
            ms = sum(s.get("ms") or 0 for s in c["steps"])
            rows += (f'<tr><td class="id">{_esc(c["id"])}</td><td><div class="t">{_esc(t)}{tag}</div>'
                     f'<div class="x">{_esc(x)}</div></td><td class="n">{verified}/{len(c["steps"])}</td>'
                     f'<td class="n">{_fmt_ms(ms)}</td><td>{_pill(c["result"])}</td></tr>')
    sources = _esc(txt.get("sources") or "")
    sources_html = f'<div class="note">{sources}</div>' if sources else ""

    perf_key = (txt.get("perf") or {}).get("case")
    labels = (txt.get("perf") or {}).get("labels") or {}
    perf_step = None
    for c in cases:
        if perf_key and f"{_task_no(c['task'])}:{c['id']}" != perf_key:
            continue
        perf_step = next((s for s in c["steps"] if (s.get("text") or "").startswith("open ") and s.get("net")), None)
        if perf_step:
            perf_case = c
            break
    perf_html = ""
    if perf_step:
        net = perf_step["net"]
        top = max((r.get("ms") or 0 for r in net), default=1) or 1
        prow = ""
        for r in net:
            kind = labels.get(r.get("u"), "redirect" if isinstance(r.get("s"), int) and 300 <= r["s"] < 400 else r.get("t", ""))
            w = max(1, round(100 * (r.get("ms") or 0) / top))
            prow += (f'<tr><td class="mono">{_esc(r.get("u", ""))}</td><td>{_esc(kind)}</td><td>{r.get("s") if r.get("s") is not None else "---"}</td>'
                     f'<td style="white-space:nowrap">{r.get("ms") or 0} ms</td><td style="width:34%"><div class="bar" style="width:{w}%"></div></td></tr>')
        foot = (f"These timings are from the first page load ({_esc(perf_case['id'])}). ")
        if f["loads"] > 1 and f["ready_min"]:
            foot += f"Over {f['loads']} loads, the page was ready in {f['ready_min']}&ndash;{f['ready_max']} s"
            if f["_doc_is_slowest"] and f["docs_min"] != "":
                foot += f", and the HTML document was always the slowest call ({f['docs_min']}&ndash;{f['docs_max']} ms)."
            else:
                foot += "."
        perf_html = (f'<h2>Page performance</h2><table class="perf"><tr><th>Resource</th><th>Type</th><th>Status</th><th>Time</th><th></th></tr>{prow}</table>'
                     f'<div class="note">{foot}</div>')

    page2 = f"""<section class="page"><h2 style="margin-top:0">Test cases</h2>
<table class="cases"><tr><th>ID</th><th>What it checks</th><th>Steps</th><th>Time</th><th>Result</th></tr>{rows}</table>
{sources_html}{perf_html}</section>"""

    # --- page 3
    ev = txt.get("evidence") or []
    if not ev:  # no captions written: the first case of each task, final state
        ev = [{"case": f"{_task_no(cs[0]['task'])}:{cs[0]['id']}", "caption": f"<b>{_esc(cs[0]['title'])}</b> ({_esc(cs[0]['id'])})"}
              for cs in by_task.values()][:6]
    figs = ""
    for item in ev[:6]:
        key = item.get("case", "")
        c = next((c for c in cases if f"{_task_no(c['task'])}:{c['id']}" == key), None)
        shots = (c or {}).get("screenshot") or []
        if not shots:
            continue
        figs += f'<figure><img src="{_esc(shots[-1])}"><figcaption>{item.get("caption", "")}</figcaption></figure>'
    ev_html = f'<h2 style="margin-top:0">Evidence</h2><div class="ev">{figs}</div>' if figs else '<h2 style="margin-top:0">Evidence</h2><div class="note">No screenshots were recorded.</div>'

    total_ms = sum(s.get("ms") or 0 for c in cases for s in c["steps"])
    site = re.sub(r"^https?://", "", meta.get("site") or "").rstrip("/")
    env = _plan_field(run, "Environment")
    rd = [("Ticket", _esc(ticket) or "&ndash;"),
          ("Run", f"{_esc(run)}" + (f" &middot; ID {_esc(meta['rid'])}" if meta.get("rid") else "") + f" &middot; session {_esc(meta.get('session', ''))}" + (f" ({sess_pos})" if sess_pos else "")),
          ("Site / environment", " &middot; ".join(x for x in [_esc(site), _esc(env), f"{_esc(meta.get('host', ''))} local runner"] if x)),
          ("Execution window", f"{_esc(started[11:])} &rarr; {_esc(finished[11:])} ({_fmt_ms(total_ms)} spent in checks)"),
          ("Report source", f"Generated from the automated quality report, built {_esc(meta.get('generated', ''))} &middot; build {_esc(meta.get('build', ''))}")]
    run_html = '<h2>Run details</h2><table class="run">' + "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rd) + "</table>"
    page3 = f'<section class="page">{ev_html}{run_html}</section>'

    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{_esc((ticket + " · " if ticket else "") + short)} · QA summary</title>'
            f"<style>{CSS}</style></head><body>{page1}{page2}{page3}</body></html>"), f


def footer(ticket, short):
    left = f"{_esc(ticket)} &middot; " if ticket else ""
    return ('<div style="font:8px Inter,Segoe UI,Arial,sans-serif;width:100%;display:flex;justify-content:space-between;'
            'padding:0 15mm;color:#6b7485"><span>' + left + _esc(short) + ' &middot; QA summary</span>'
            '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')
