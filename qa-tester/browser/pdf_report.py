"""The PDF report's page: a complete, standalone record of one session, written as plain static HTML that
report.py renders to PDF. Everything the HTML report knows is here too: who and what was tested (ticket, run,
session, site, environment, build, times), the result counts, every case with every step (result, what was
checked, what was seen, how long it took), the network calls each step made, the screenshots, and a network
summary with failed calls. No scripts, light theme only - a document to hand to someone.
"""
import re

import core

RESULT_COLOR = {"Verified": "#1e9b55", "Issue found": "#dc3a3f", "Could not verify": "#c27a0a", "Not tested": "#8e8e93"}
MAX_CALLS_SHOWN = 14

CSS = """
*{box-sizing:border-box}
body{margin:0;font:12.5px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#1d1d1f;background:#fff}
.wrap{padding:4mm 1mm}
.eyebrow{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#8e8e93;font-weight:600}
.tk{display:inline-block;font:600 11px ui-monospace,Menlo,Consolas,monospace;border:1px solid #c7c7cc;border-radius:6px;padding:2px 8px;margin-right:8px;color:#1d1d1f}
h1{font-size:26px;font-weight:700;letter-spacing:-.02em;margin:8px 0 4px}
h2{font-size:15px;margin:26px 0 8px;font-weight:700}
.sub{color:#6e6e73;font-size:12px}
table{border-collapse:collapse;width:100%}
.id td{padding:4px 10px 4px 0;vertical-align:top;font-size:12px}
.id td:first-child{color:#8e8e93;width:23%;text-transform:uppercase;font-size:10px;letter-spacing:.05em;padding-top:6px}
.id code{font:11.5px ui-monospace,Menlo,Consolas,monospace;word-break:break-all}
.summary{display:flex;gap:10px;margin:16px 0 4px}
.box{flex:1;border:1px solid #e5e5e7;border-radius:10px;padding:10px 14px}
.box b{display:block;font-size:22px;font-weight:700;letter-spacing:-.02em}
.box span{font-size:10px;color:#8e8e93;text-transform:uppercase;letter-spacing:.05em}
.grid th{text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:#8e8e93;padding:5px 8px;border-bottom:1px solid #e5e5e7}
.grid td{padding:5px 8px;border-bottom:1px solid #f0f0f1;font-size:11.5px;vertical-align:top}
.num{text-align:right;white-space:nowrap}
.suite{margin-top:20px}
.suite-h{font-size:14px;font-weight:700;margin-bottom:8px}
.sno{font:10.5px ui-monospace,Menlo,Consolas,monospace;color:#8e8e93;border:1px solid #d6d6d8;border-radius:5px;padding:1px 5px;margin-right:8px}
.case{border:1px solid #e5e5e7;border-left-width:4px;border-radius:9px;padding:11px 14px;margin-bottom:12px}
.case-h{display:flex;align-items:center;gap:9px}
.cid{font:11px ui-monospace,Menlo,Consolas,monospace;color:#8e8e93}
.ct{font-weight:600;font-size:13px;flex:1}
.badge{font-size:10px;font-weight:600;border:1px solid;border-radius:999px;padding:1px 8px;white-space:nowrap}
.csub{font-size:11px;color:#8e8e93;margin:3px 0 8px}
.steps td{padding:5px 6px;border-top:1px solid #f0f0f1;vertical-align:top;font-size:11.5px}
.steps td.n{width:4%;color:#8e8e93}
.steps td.r{width:15%}
.steps td.ms{width:9%;text-align:right;color:#8e8e93;white-space:nowrap}
.steps code{font:11px ui-monospace,Menlo,Consolas,monospace;background:#f5f5f7;padding:1px 5px;border-radius:4px}
.msg{color:#48484a;margin-top:3px;font-size:11px}
.saw{color:#dc3a3f}
.calls{margin-top:5px;font:10px/1.45 ui-monospace,Menlo,Consolas,monospace;color:#6e6e73}
.calls .bad{color:#dc3a3f}
.shots{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.shot{display:block;max-width:300px;max-height:190px;object-fit:cover;object-position:top;border:1px solid #e5e5e7;border-radius:7px}
.lbl{font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;color:#8e8e93;margin:10px 0 4px}
.case,.steps tr{page-break-inside:avoid;break-inside:avoid}
h2,.suite-h,.lbl{page-break-after:avoid;break-after:avoid}
h2{page-break-before:auto}
.plan{font-size:11px;color:#48484a;background:#f7f7f8;border-radius:7px;padding:6px 10px;margin:0 0 8px;line-height:1.55}
.plan b{color:#8e8e93;font-weight:600;font-size:9.5px;letter-spacing:.06em;text-transform:uppercase;margin-right:6px}
.legend{font-size:11px;color:#6e6e73}
.legend i{display:inline-block;width:8px;height:8px;border-radius:50%;margin:0 4px 0 12px}
.none{color:#8e8e93;font-style:italic}
"""


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _color(word):
    return RESULT_COLOR.get(word, "#8e8e93")


def _badge(word):
    c = _color(word)
    return f'<span class="badge" style="color:{c};border-color:{c}55;background:{c}14">{_esc(word)}</span>'


def _dur(ms):
    if ms is None:
        return ""
    return f"{ms / 1000:.1f} s" if ms >= 1000 else f"{int(ms)} ms"


def _plan_field(run, label):
    try:
        text = (core.QA / "runs" / run / "plan.md").read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"^" + re.escape(label) + r":\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def _plan_checks(run):
    """The plan's "What we will check" table as {case id: (what, how it should work, where it comes from)},
    so each case in the PDF says what it was meant to prove and where "expected" came from."""
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


def _is_bad_call(r):
    s = r.get("s")
    return bool(r.get("f")) or (isinstance(s, int) and s >= 400)


def _calls_html(net):
    if not net:
        return ""
    bad = [r for r in net if _is_bad_call(r)]
    head = f'{len(net)} network call(s), {len(bad)} failed'
    rows = []
    for r in net[:MAX_CALLS_SHOWN]:
        cls = ' class="bad"' if _is_bad_call(r) else ""
        status = r.get("s") if r.get("s") is not None else "---"
        rows.append(f'<div{cls}>{_esc(r.get("m", ""))} {status} {_esc(r.get("t", ""))} {r.get("ms") or 0} ms {_esc(r.get("u", ""))}'
                    + (f' FAILED: {_esc(r["f"])}' if r.get("f") else "") + "</div>")
    more = f'<div>+ {len(net) - MAX_CALLS_SHOWN} more call(s)</div>' if len(net) > MAX_CALLS_SHOWN else ""
    return f'<div class="calls"><b>{head}</b>{"".join(rows)}{more}</div>'


def _imgs(paths):
    paths = paths if isinstance(paths, list) else ([paths] if paths else [])
    return "".join(f'<img class="shot" src="{_esc(p)}">' for p in paths)


def _step_row(i, s):
    msg = s.get("msg") or ""
    ex = re.match(r"^Expected:\s*(.*?)\.?\s*Saw:\s*(.*)$", msg, re.S)
    if ex:
        detail = f'<div class="msg"><b>Expected</b> {_esc(ex.group(1))}<br><b>Saw</b> <span class="saw">{_esc(ex.group(2))}</span></div>'
    elif msg:
        detail = f'<div class="msg">{_esc(msg)}</div>'
    else:
        detail = ""
    shots = _imgs(s.get("screenshot"))
    shots = f'<div class="shots">{shots}</div>' if shots else ""
    return (f'<tr><td class="n">{i}</td><td class="r">{_badge(s.get("result"))}</td>'
            f'<td><code>{_esc(s.get("text", ""))}</code>{detail}{_calls_html(s.get("net"))}{shots}</td>'
            f'<td class="ms">{_dur(s.get("ms"))}</td></tr>')


def _case_html(c, plan):
    steps = c["steps"]
    p = plan.get(c["id"])
    if p:
        plan_html = (f'<div class="plan"><b>What it checks</b> {_esc(p[0])}<br><b>Expected</b> {_esc(p[1])}'
                     f'<br><b>Source of expected</b> {_esc(p[2])}</div>')
    else:
        plan_html = '<div class="plan none">Not in the plan\'s check table (added during the run).</div>'
    task_label = f'Task {_esc(_suite_no(c["task"]))} &middot; {_esc(_suite_name(c["task"]))}'
    verified = sum(1 for s in steps if s.get("result") == "Verified")
    total_ms = sum(s.get("ms") or 0 for s in steps)
    started = steps[0].get("ts", "") if steps else ""
    rows = "".join(_step_row(i, s) for i, s in enumerate(steps, 1))
    table = f'<table class="steps">{rows}</table>' if rows else '<div class="none">No steps recorded.</div>'
    final = _imgs(c.get("screenshot"))
    final = f'<div class="lbl">Final state</div><div class="shots">{final}</div>' if final else ""
    return (f'<div class="case" style="border-left-color:{_color(c["result"])}">'
            f'<div class="case-h"><span class="cid">{_esc(c["id"])}</span><span class="ct">{_esc(c["title"])}</span>{_badge(c["result"])}</div>'
            f'<div class="csub">{task_label} &middot; {verified} of {len(steps)} steps verified &middot; {_dur(total_ms)}'
            + (f' &middot; started {_esc(started)}' if started else "") + f'</div>{plan_html}{table}{final}</div>')


def _suite_name(task):
    name = re.sub(r"^\d+-", "", task or "").replace("-", " ")
    return name[:1].upper() + name[1:] if name else "General"


def _suite_no(task):
    m = re.match(r"^(\d+)-", task or "")
    return m.group(1) if m else ""


def build_html(run, meta, events, cases, counts, total, title, file_name, n_sessions):
    rate = round(100 * counts.get("Verified", 0) / total) if total else 0
    ticket = meta.get("ticket") or ""
    site = re.sub(r"^https?://", "", meta.get("site") or "").rstrip("/")
    env = _plan_field(run, "Environment")
    source = _plan_field(run, "Source")
    started, finished = meta.get("started", ""), meta.get("finished", "")
    case_ms = sum((s.get("ms") or 0) for c in cases for s in c["steps"])
    plan = _plan_checks(run)

    ident = [
        ("Ticket", f"<code>{_esc(ticket)}</code>" if ticket else '<span class="none">none</span>'),
        ("Source", _esc(source) if source and source != ticket else ""),
        ("Run", f"<code>{_esc(run)}</code>"),
        ("Run ID", f"<code>{_esc(meta.get('rid', ''))}</code>" if meta.get("rid") else ""),
        ("Session", f"<code>{_esc(meta.get('session', ''))}</code>" + (f" &middot; one of {n_sessions} in this run" if n_sessions > 1 else "")),
        ("Site tested", _esc(site)),
        ("Environment", _esc(env)),
        ("Run on", _esc(f"{meta.get('host', '')} ({meta.get('runner', '')} runner)")),
        ("Started / finished", f"{_esc(started)} &rarr; {_esc(finished)}"),
        ("Time in checks", _dur(case_ms)),
        ("Report built", f"{_esc(meta.get('generated', ''))} &middot; build <code>{_esc(meta.get('build', ''))}</code>"),
        ("File", f"<code>{_esc(file_name)}</code>"),
    ]
    ident_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in ident if v)

    boxes = (f'<div class="box"><b>{rate}%</b><span>Pass rate</span></div>'
             + "".join(f'<div class="box"><b style="color:{_color(w)}">{counts.get(w, 0)}</b><span>{w}</span></div>'
                       for w in ("Verified", "Issue found", "Could not verify", "Not tested")))

    suites, seen = [], []
    for c in cases:
        if c["task"] not in seen:
            seen.append(c["task"])
            suites.append({"task": c["task"], "cases": []})
        next(s for s in suites if s["task"] == c["task"])["cases"].append(c)

    task_rows = ""
    for s in suites:
        ok = sum(1 for c in s["cases"] if c["result"] == "Verified")
        bad = sum(1 for c in s["cases"] if c["result"] == "Issue found")
        mid = sum(1 for c in s["cases"] if c["result"] == "Could not verify")
        nt = sum(1 for c in s["cases"] if c["result"] == "Not tested")
        task_rows += (f'<tr><td>{_esc(_suite_no(s["task"]))}</td><td>{_esc(_suite_name(s["task"]))}</td>'
                      f'<td class="num">{len(s["cases"])}</td><td class="num">{ok}</td><td class="num">{bad}</td>'
                      f'<td class="num">{mid}</td><td class="num">{nt}</td></tr>')
    by_task = (f'<table class="grid"><tr><th>#</th><th>Task</th><th class="num">Cases</th><th class="num">Verified</th>'
               f'<th class="num">Issue found</th><th class="num">Could not verify</th><th class="num">Not tested</th></tr>{task_rows}</table>')

    suite_blocks = "".join(
        f'<div class="suite"><div class="suite-h">'
        + (f'<span class="sno">{_esc(_suite_no(s["task"]))}</span>' if _suite_no(s["task"]) else "")
        + f'{_esc(_suite_name(s["task"]))}</div>{"".join(_case_html(c, plan) for c in s["cases"])}</div>'
        for s in suites)

    # network summary across the whole session
    calls = [r for e in events for r in (e.get("net") or [])]
    failed = [r for r in calls if _is_bad_call(r)]
    xhr = [r for r in calls if r.get("t") in ("xhr", "fetch")]
    slow = sorted(calls, key=lambda r: r.get("ms") or 0, reverse=True)[:6]
    slow_rows = "".join(f'<tr><td>{_esc(r.get("m", ""))}</td><td class="num">{r.get("s") if r.get("s") is not None else "---"}</td>'
                        f'<td>{_esc(r.get("t", ""))}</td><td class="num">{r.get("ms") or 0} ms</td><td>{_esc(r.get("u", ""))}</td></tr>' for r in slow)
    failed_html = ('<div class="none">None. No call failed or answered 400 or more.</div>' if not failed else
                   '<table class="grid">' + "".join(f'<tr><td>{_esc(r.get("m", ""))}</td><td class="num">{r.get("s")}</td>'
                                                  f'<td>{_esc(r.get("u", ""))}</td><td>{_esc(r.get("f") or "")}</td></tr>' for r in failed[:30]) + "</table>")
    checks = [s for c in cases for s in c["steps"]
              if re.search(r"console|failed network", s.get("text", ""), re.I)]
    check_rows = "".join(f'<tr><td>{_esc(s.get("text", ""))}</td><td>{_badge(s.get("result"))}</td><td>{_esc(s.get("msg") or "")}</td></tr>' for s in checks)
    checks_html = (f'<table class="grid"><tr><th>Check</th><th>Result</th><th>Detail</th></tr>{check_rows}</table>'
                   if check_rows else '<div class="none">No console or failed-call checks were part of this session.</div>')

    legend = ('<div class="legend">Result words:' + "".join(
        f'<i style="background:{_color(w)}"></i>{w}' for w in ("Verified", "Issue found", "Could not verify", "Not tested"))
        + ". Verified means the check held and has evidence. Not tested means an earlier step in the case did not succeed.</div>")

    doc_title = f"{ticket + ' · ' if ticket else ''}{title} · session {meta.get('session', '')}"
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{_esc(doc_title)}</title>
<style>{CSS}</style></head><body><div class="wrap">
<div class="eyebrow">Quality report</div>
<h1>{('<span class="tk">' + _esc(ticket) + '</span>') if ticket else ''}{_esc(title)}</h1>
<div class="sub">{len(cases)} test cases &middot; {total} checks &middot; session {_esc(meta.get('session', ''))}</div>
<h2>Identity</h2><table class="id">{ident_rows}</table>
<h2>Result</h2><div class="summary">{boxes}</div>{legend}
<h2>By task</h2>{by_task}
<h2>Test cases</h2>{suite_blocks}
<h2>Network summary</h2>
<div class="sub">{len(calls)} call(s) recorded &middot; {len(xhr)} XHR/fetch &middot; {len(failed)} failed</div>
<div class="lbl">Slowest calls</div>
<table class="grid"><tr><th>Method</th><th class="num">Status</th><th>Type</th><th class="num">Time</th><th>Path</th></tr>{slow_rows}</table>
<div class="lbl">Failed calls</div>{failed_html}
<h2>Console and failed-call checks</h2>{checks_html}
</div></body></html>"""
