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


def rel_to_run(run, path):
    """A screenshot path, relative to the run folder, so report.html (which lives there) can show it
    with a plain relative <img src>, however deep inside tasks/ it actually sits."""
    try:
        return str(Path(path).resolve().relative_to(_run_dir(run).resolve())).replace("\\", "/")
    except ValueError:
        return str(path)
