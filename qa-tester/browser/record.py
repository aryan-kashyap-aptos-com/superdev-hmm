"""Durable, append-only record of everything a run does: every ad hoc command, scenario step, and crawled
page becomes one line in qa-tester/runs/<run>/events.jsonl, with a run-wide sequential id - "Test #1",
"Test #2", in the order they really happened, across every task and every separate command invocation.

This exists because the live runner panel is not enough on its own: it shows what is running right now,
inside the one Chrome window, and loses everything (including the network calls it displayed) the moment
that window closes. This file does not. `report.py` reads it to build a standalone report you can open any
time after the browser - or the whole demo - is done.
"""
import json
import time
from pathlib import Path

import core


def _run_dir(run):
    return core.QA / "runs" / run


def _seq_file(run):
    return _run_dir(run) / ".seq"


def next_seq(run):
    f = _seq_file(run)
    n = 1
    if f.exists():
        try:
            n = int(f.read_text(encoding="utf-8").strip()) + 1
        except ValueError:
            n = 1
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(str(n), encoding="utf-8")
    return n


def record(run, task, kind, text, result=None, msg="", ms=None, net=None, screenshot=None, case_id=None, tags=None):
    """Append one event. Safe to call often and never raises: a demo must not break because logging a
    line failed. `run` may be None (nothing to attach the record to, e.g. no active run) - then it is
    simply skipped, exactly like the rest of this tool behaves without an active run."""
    if not run:
        return
    try:
        row = {"seq": next_seq(run), "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "task": task or "", "kind": kind,
               "case_id": case_id, "text": text, "result": result, "msg": core.redact(msg or ""),
               "ms": ms, "net": net or [], "screenshot": screenshot, "tags": tags or []}
        d = _run_dir(run)
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "events.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except Exception:
        pass


def read_events(run):
    p = _run_dir(run) / "events.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    out.sort(key=lambda e: e.get("seq", 0))
    return out


STATUS = {"Verified": "verified", "Issue found": "issue", "Could not verify": "cnv", "Not tested": "nt"}


def hydrate_cases(run, task=None):
    """Reconstruct a panel-shaped case/step list from the durable event log, for redisplay after the live
    panel has lost its in-browser state: a real page reload wipes the iframe, and since each CLI command is
    its own process, there is no in-memory copy left anywhere to replay it from (Panel's own replay only
    covers a reload mid-process, for example mid `play`). Reading it back from events.jsonl means the Tests
    tab recovers regardless of why the state was lost. Returns (task, cases), or (None, None) if there is
    nothing to show. Without `task`, uses whichever task the most recent step was recorded under."""
    events = read_events(run)
    steps = [e for e in events if e.get("kind") == "step" and e.get("case_id")]
    if not steps:
        return None, None
    if task is None:
        task = steps[-1].get("task")
    steps = [e for e in steps if e.get("task") == task]
    case_rows = {e["case_id"]: e for e in events if e.get("kind") == "case" and e.get("task") == task}
    order, by_case = [], {}
    for e in steps:
        cid = e["case_id"]
        if cid not in by_case:
            by_case[cid] = []
            order.append(cid)
        by_case[cid].append(e)
    cases = []
    for cid in order:
        case_steps = by_case[cid]
        case_row = case_rows.get(cid, {})
        status = STATUS.get(case_row.get("result")) or STATUS.get(case_steps[-1].get("result"), "pending")
        cases.append({"id": cid, "title": case_row.get("text") or cid, "status": status,
                      "steps": [{"text": s["text"], "status": STATUS.get(s.get("result"), "pending"),
                                 "msg": s.get("msg") or "", "ms": s.get("ms")} for s in case_steps]})
    return task, cases


def rel_to_run(run, path):
    """A screenshot path, relative to the run folder, so report.html (which lives there) can show it
    with a plain relative <img src>, however deep inside tasks/ it actually sits."""
    try:
        return str(Path(path).resolve().relative_to(_run_dir(run).resolve())).replace("\\", "/")
    except ValueError:
        return str(path)
