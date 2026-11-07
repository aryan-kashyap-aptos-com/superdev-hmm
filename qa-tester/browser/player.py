"""Run a scenario file: test cases made of steps, shown live in the runner panel, with results saved as files.

A scenario is a JSON file (template: qa-tester/templates/scenario.json):

    {"name": "...", "site": "<name from environments>", "cases": [
       {"id": "C1", "title": "...", "tags": ["smoke"], "steps": [
          {"do": "goto", "url": "/path/page"},
          {"do": "click", "target": "Sign in"},
          {"expect": "disabled", "target": "role=button[name='Export']"},
          {"expect": "no-failed-requests"}]}]}

Each step is either an action ("do") or a check ("expect"). Checks retry until they hold or the timeout ends,
like Cypress. A case stops at its first step that is not Verified; its remaining steps are "Not tested".
"tags" is optional (a list of short labels, e.g. ["smoke", "checkout"]) - `report` shows them as chips and
lets you filter by one, the same idea as Cucumber's @tags.
"""
import datetime
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

import core
import record
from core import c
from panel import Panel

ACTIONS = {"goto", "click", "fill", "select", "check", "uncheck", "press", "hover", "scroll", "wait", "screenshot",
           "login", "reload", "back"}
CHECKS = {"visible", "hidden", "enabled", "disabled", "checked", "unchecked", "editable", "readonly", "exists", "absent",
          "in-view", "clickable", "covered", "text", "text-equals", "value", "count", "attribute",
          "url", "title", "page-text", "no-console-errors", "no-failed-requests", "request"}
NEED_TARGET = {"click", "fill", "select", "check", "uncheck", "hover", "visible", "hidden", "enabled", "disabled", "checked",
               "unchecked", "editable", "readonly", "exists", "absent", "in-view", "clickable", "covered", "text",
               "text-equals", "value", "count", "attribute"}
NEED_VALUE = {"fill", "select", "press", "text", "text-equals", "value", "count", "url", "title", "page-text", "request"}
RESULTS = ["Verified", "Issue found", "Could not verify", "Not tested"]


# ---------------------------------------------------------------- reading the file

def validate(data):
    """Plain-language problems with a scenario, or an empty list."""
    errors = []
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list) or not data["cases"]:
        return ["The file needs a non-empty \"cases\" list."]
    seen = set()
    for ci, case in enumerate(data["cases"], 1):
        where = f"case {ci}"
        if not isinstance(case, dict):
            errors.append(f"{where}: must be an object")
            continue
        cid = case.get("id") or f"C{ci}"
        where = f"case {cid}"
        if cid in seen:
            errors.append(f"{where}: the id is used twice")
        seen.add(cid)
        if not case.get("title"):
            errors.append(f"{where}: needs a \"title\"")
        steps = case.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"{where}: needs a non-empty \"steps\" list")
            continue
        for si, step in enumerate(steps, 1):
            at = f"{where}, step {si}"
            if not isinstance(step, dict):
                errors.append(f"{at}: must be an object")
                continue
            kind = step.get("do") or step.get("expect")
            if bool(step.get("do")) == bool(step.get("expect")):
                errors.append(f"{at}: give exactly one of \"do\" or \"expect\"")
                continue
            if step.get("do") and kind not in ACTIONS:
                errors.append(f"{at}: unknown action \"{kind}\" (use one of: {', '.join(sorted(ACTIONS))})")
            if step.get("expect") and kind not in CHECKS:
                errors.append(f"{at}: unknown check \"{kind}\" (use one of: {', '.join(sorted(CHECKS))})")
            if kind in NEED_TARGET and not step.get("target"):
                errors.append(f"{at}: \"{kind}\" needs a \"target\"")
            if kind in NEED_VALUE and step.get("value") in (None, ""):
                errors.append(f"{at}: \"{kind}\" needs a \"value\"")
            if kind == "goto" and not step.get("url"):
                errors.append(f"{at}: \"goto\" needs a \"url\"")
            if kind == "attribute" and not step.get("name"):
                errors.append(f"{at}: \"attribute\" needs a \"name\"")
            if kind == "fill" and re.search(r"pass|pwd|secret|token", str(step.get("target", "")), re.I) \
                    and not str(step.get("value", "")).startswith("$"):
                errors.append(f"{at}: write \"value\": \"$password\" (it reads the run's Login section), never the password itself")
    return errors


def load(path):
    p = Path(path)
    if not p.exists():
        raise c.ConnectorError(f"Scenario file not found: {p}", "Copy qa-tester/templates/scenario.json and fill it in.")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise c.ConnectorError(f"{p.name} is not valid JSON: {e}", "Check commas, quotes and brackets.") from None
    errors = validate(data)
    if errors:
        raise c.ConnectorError("The scenario has problems:\n  - " + "\n  - ".join(errors), "Fix the file. Template: qa-tester/templates/scenario.json")
    for i, case in enumerate(data["cases"], 1):
        case.setdefault("id", f"C{i}")
    return data


# ---------------------------------------------------------------- words for people

SECRET_WORDS = {"password": "the run's password", "user": "the run's username"}


def fill_phrase(v):
    """What 'fill' types, in words: a literal value stays as given; '$password'/'$user' name the run's
    login (never the value itself); any other '$NAME' names the setting."""
    v = str(v)
    if not v.startswith("$"):
        return repr(v)
    name = v[1:]
    return SECRET_WORDS.get(name, f"the value of {name}")


def describe(step):
    """The line shown in the panel and the results, for example: '"Export" is disabled'."""
    if step.get("note"):
        return step["note"]
    k, t, v = step.get("do") or step.get("expect"), step.get("target", ""), step.get("value", "")
    neg = "not " if step.get("not") else ""
    if step.get("do"):
        return {"goto": f"open {step.get('url', '')}", "click": f'click "{t}"',
                "fill": f'type {fill_phrase(v)} into "{t}"',
                "select": f'choose "{v}" in "{t}"', "check": f'tick "{t}"', "uncheck": f'untick "{t}"',
                "press": f'press {v}' + (f' in "{t}"' if t else ""), "hover": f'point at "{t}"',
                "scroll": f'scroll to "{t}"' if t else f"scroll {step.get('to', 'down')}",
                "wait": f'wait until "{t}" is {step.get("for", "visible")}' if t else f"wait {v or 1000} ms",
                "screenshot": f"screenshot {step.get('name', '')}".strip(), "login": "sign in",
                "reload": "reload the page", "back": "go back"}[k]
    state = {"in-view": "in view (no scrolling needed)", "covered": "covered by another element",
             "exists": "on the page", "absent": "not on the page"}.get(k, k)
    if k == "text":
        return f'"{t}" {"does not contain" if neg else "contains"} "{v}"'
    if k == "text-equals":
        return f'"{t}" {"is not" if neg else "is exactly"} "{v}"'
    if k == "value":
        return f'"{t}" has {neg}the value "{v}"'
    if k == "count":
        return f'"{t}" appears {v} time(s)' + (" (inverted)" if neg else "")
    if k == "attribute":
        return f'"{t}" has {neg}{step["name"]}' + (f'="{v}"' if v not in (None, "") else "")
    if k == "url":
        return f'the address {neg}contains "{v}"'
    if k == "title":
        return f'the page title {neg}contains "{v}"'
    if k == "page-text":
        return f'the page {neg}shows "{v}"'
    if k == "no-console-errors":
        return "no errors in the browser console"
    if k == "no-failed-requests":
        return "no failed network calls"
    if k == "request":
        return f'a network call to "{v}" happened' + (f" with status {step['status']}" if step.get("status") else "")
    return f'"{t}" is {neg}{state}'


def secret_value(raw):
    """'$password' or '$user' means: take the value from the Login section of the active run's plan.md.
    Any other '$NAME' falls back to an environment setting of that name. Returns (value, is_secret)."""
    raw = str(raw)
    if not raw.startswith("$"):
        return raw, False
    name = raw[1:]
    if name in ("password", "user"):
        info = core.run_login()
        if not info.get(name):
            where = f"qa-tester/runs/{info['run']}/plan.md" if info.get("run") else "the active run's plan.md"
            raise c.ConnectorError(f"The run's {name} is not filled in.", f"Fill it in the Login section of {where}.")
        return info[name], True
    if not os.environ.get(name):
        raise c.ConnectorError(f"The setting {name} is missing.", "Add it to qa-tester/browser/.env.")
    return os.environ[name], True


# ---------------------------------------------------------------- checks

def _compare_count(n, rule):
    m = re.match(r"^\s*(>=|<=|>|<|=|==)?\s*(\d+)\s*$", str(rule))
    if not m:
        raise c.ConnectorError(f"Count rule '{rule}' is not understood.", "Use a number, or >=N, <=N, >N, <N.")
    op, want = m.group(1) or "=", int(m.group(2))
    return {"=": n == want, "==": n == want, ">=": n >= want, "<=": n <= want, ">": n > want, "<": n < want}[op]


def evaluate(page, step, ctx):
    """One attempt at a check. Returns (holds?, what we saw)."""
    k, t, v = step["expect"], step.get("target"), step.get("value")
    if k in NEED_TARGET:
        loc = core.locate(page, t)
        s = core.element_state(loc)
        seen = core.describe_state(s)
        if k == "count":
            return _compare_count(s.get("count", 0), v), f"found {s.get('count', 0)}"
        if k in ("exists", "absent"):
            return (s["exists"] if k == "exists" else not s["exists"]), seen
        if not s["exists"]:
            return k == "hidden", seen
        el = loc.first
        if k == "visible":
            return s["visible"], seen
        if k == "hidden":
            return not s["visible"], seen
        if k == "enabled":
            return s["enabled"], seen
        if k == "disabled":
            return not s["enabled"], seen
        if k in ("checked", "unchecked"):
            if s.get("checked") is None:
                return False, "it is not a checkbox or radio button"
            return (s["checked"] if k == "checked" else not s["checked"]), seen
        if k == "editable":
            return bool(s.get("editable")), seen
        if k == "readonly":
            return s.get("editable") is False or bool(s.get("readonly")), seen
        if k == "in-view":
            return bool(s["visible"] and s.get("inView")), seen
        if k == "clickable":
            return s["clickable"], seen
        if k == "covered":
            return bool(s.get("covered")), seen
        if k in ("text", "text-equals"):
            text = re.sub(r"\s+", " ", el.inner_text(timeout=3000)).strip()
            ok = (str(v).lower() in text.lower()) if k == "text" else text == str(v).strip()
            return ok, f'text is "{text[:120]}"'
        if k == "value":
            val = el.input_value(timeout=3000)
            shown = "***" if s.get("type") == "password" else val[:120]
            return val == str(v), f'value is "{shown}"'
        if k == "attribute":
            got = el.get_attribute(step["name"])
            ok = got is not None if v in (None, "") else got == str(v)
            return ok, f'{step["name"]} is {"missing" if got is None else repr(got[:80])}'
    if k == "url":
        return str(v).lower() in page.url.lower(), f"address is {core.safe_url(page.url, urlsplit(page.url).hostname)}"
    if k == "title":
        title = page.title()
        return str(v).lower() in title.lower(), f'title is "{title}"'
    if k == "page-text":
        for frame in page.frames:
            try:
                if str(v).lower() in frame.locator("body").inner_text(timeout=3000).lower():
                    return True, "found on the page"
            except Exception:
                continue
        return False, "not found on the page"
    if k == "no-console-errors":
        errs = ctx["console"][ctx["console_mark"]:]
        return not errs, ("none" if not errs else f"{len(errs)} error(s), first: {errs[0][:150]}")
    if k == "no-failed-requests":
        home = urlsplit(page.url).hostname
        bad = [r for r in ctx["net"].since(ctx["net_mark"]) if core.is_bad(r)]
        return not bad, ("none" if not bad else f"{len(bad)} failed, first: {bad[0]['method']} {bad[0]['status'] or bad[0]['failed']} {core.safe_url(bad[0]['url'], home)}")
    if k == "request":
        home = urlsplit(page.url).hostname
        hits = [r for r in ctx["net"].since(ctx["net_mark"]) if str(v).lower() in core.safe_url(r["url"], home).lower()]
        if step.get("status"):
            good = [r for r in hits if str(r["status"]) == str(step["status"])]
            return bool(good), (f"{len(hits)} matching call(s); statuses: {sorted({str(r['status']) for r in hits})}" if hits else "no matching call")
        return bool(hits), (f"{len(hits)} matching call(s), last status {hits[-1]['status']}" if hits else "no matching call")
    raise c.ConnectorError(f"Unknown check '{k}'.")


def check(page, step, ctx, timeout_ms):
    """Retry a check until it holds or the time is up. Returns (result word, message)."""
    end = time.time() + timeout_ms / 1000
    while True:
        try:
            ok, seen = evaluate(page, step, ctx)
        except c.ConnectorError:
            raise
        except Exception as e:
            ok, seen = False, f"could not read it: {str(e).splitlines()[0][:150]}"
        if step.get("not"):
            ok = not ok
        if ok or time.time() >= end:
            return ("Verified", seen) if ok else ("Issue found", f"Expected: {describe(step)}. Saw: {seen}.")
        page.wait_for_timeout(250)


# ---------------------------------------------------------------- actions

def act(page, step, ctx, args):
    """Do one action. Returns (result word, message, evidence paths)."""
    k, t = step["do"], step.get("target")
    timeout = int(step.get("timeout", args.timeout))
    home, net = ctx["site"], ctx["net"]

    def target():
        loc = core.locate(page, t)
        if loc.count() == 0:
            raise LookupError(f'"{t}" was not found on the page')
        el = loc.first
        if k not in ("hover",) and not el.is_visible():
            core.show(el, page)   # scrolls it into view if it is only out of sight
            if not el.is_visible():
                raise LookupError(f'"{t}" is on the page but hidden ({core.describe_state(core.element_state(loc))})')
        return el

    if k == "goto":
        url = core.absolute(step["url"], home)
        core.check_allowed(url)
        resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
        ms, finished = core.settle(page, net, args.max_wait)
        core.check_allowed(page.url)
        status = resp.status if resp else None
        if status and status >= 400:
            return "Issue found", f"The page answered HTTP {status}.", []
        return "Verified", f"{page.title()} (HTTP {status}, ready in {ms / 1000:.1f}s{'' if finished else ', still loading'})", []
    if k == "login":
        word, msg = core.login(page, home, net)
        return word, msg, []
    if k in ("reload", "back"):
        (page.reload if k == "reload" else page.go_back)(wait_until="domcontentloaded", timeout=60000)
        core.settle(page, net, args.max_wait)
        return "Verified", page.title(), []
    if k == "click":
        if (core.RISKY.search(t) or step.get("write")) and not (step.get("write") and args.write):
            raise c.ConnectorError(f'Clicking "{t}" may change data.',
                                   'Mark the step "write": true and run play with --write, only after the user says yes.')
        el = target()
        core.show(el, page)
        el.click(timeout=timeout)
        ms, finished = core.settle(page, net, args.max_wait)
        core.check_allowed(page.url)
        return "Verified", f"now on: {page.title()}", []
    if k == "fill":
        value, _secret = secret_value(step["value"])
        core.type_into(page, target(), value)
        return "Verified", "", []
    if k == "select":
        el = target()
        core.show(el, page)
        try:
            el.select_option(label=str(step["value"]), timeout=timeout)
        except Exception:
            el.select_option(value=str(step["value"]), timeout=timeout)
        core.settle(page, net, args.max_wait)
        return "Verified", "", []
    if k in ("check", "uncheck"):
        el = target()
        core.show(el, page)
        (el.check if k == "check" else el.uncheck)(timeout=timeout)
        return "Verified", "", []
    if k == "press":
        if t:
            el = target()
            core.show(el, page)
            el.press(str(step["value"]))
        else:
            page.keyboard.press(str(step["value"]))
        core.settle(page, net, args.max_wait)
        return "Verified", "", []
    if k == "hover":
        el = target()
        core.show(el, page)
        el.hover(timeout=timeout)
        return "Verified", "", []
    if k == "scroll":
        if t:
            loc = core.locate(page, t)
            if loc.count() == 0:
                raise LookupError(f'"{t}" was not found on the page')
            core.show(loc.first, page)
            return "Verified", "", []
        info = core.scroll(page, step.get("to", "down"), step.get("pixels"))
        return "Verified", f"at {info['to']} of {info['max']} px" + (" (inner scroll area)" if info["inner"] else ""), []
    if k == "wait":
        if t:
            state = step.get("for", "visible")
            core.locate(page, t).first.wait_for(state=state, timeout=timeout)
            return "Verified", "", []
        page.wait_for_timeout(int(step.get("value") or 1000))
        return "Verified", "", []
    if k == "screenshot":
        name = f"{ctx['case_id']}-{step.get('name', 'screenshot')}"
        paths = core.capture(page, ctx["shots"] / f"{ctx['next_shot']():02d}-{re.sub(r'[^a-zA-Z0-9-]+', '-', name)}.png",
                             full=step.get("full", True), net=net)
        return "Verified", "", paths
    raise c.ConnectorError(f"Unknown action '{k}'.")


# ---------------------------------------------------------------- running a scenario

def run(path, args):
    scenario = load(path)
    home = core.site(scenario.get("site") or getattr(args, "site", None))
    run_name = args.run or f"scenario-{core.stamp()}"
    folder = core.QA / "runs" / run_name / ("tasks/" + args.task if args.task else "")
    shots = folder / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    counter = {"n": len(list(shots.glob("*.png")))}

    def next_shot():
        counter["n"] += 1
        return counter["n"]

    cases_out = []
    started = datetime.datetime.now()
    with core.session() as (_, page):
        net, console = core.Net(page), []
        page.on("console", lambda m: console.append(m.text[:200]) if m.type == "error" else None)
        panel = Panel.open(page)
        panel.plan(scenario.get("name", Path(path).stem), f"{home['name']} - {len(scenario['cases'])} test case(s)",
                   [{"id": k["id"], "title": k["title"], "steps": [describe(s) for s in k["steps"]]} for k in scenario["cases"]])
        page.wait_for_timeout(800)
        for ci, case in enumerate(scenario["cases"]):
            ctx = {"site": home, "net": net, "console": console, "net_mark": len(net.rows), "console_mark": len(console),
                   "case_id": case["id"], "shots": shots, "next_shot": next_shot}
            panel.case(ci, "running")
            panel.activity(f"Running case {ci + 1} of {len(scenario['cases'])}: {case['title']}")
            print(f"\n{case['id']}  {case['title']}")
            steps_out, stopped, evidence = [], False, []
            for si, step in enumerate(case["steps"]):
                text = describe(step)
                if stopped:
                    panel.step(ci, si, "Not tested")
                    steps_out.append({"step": text, "result": "Not tested", "detail": "an earlier step did not succeed", "ms": None})
                    print(f"   - Not tested       {text}")
                    continue
                panel.step(ci, si, "running")
                mark, t0 = len(net.rows), time.time()
                files = []
                try:
                    if step.get("do"):
                        word, msg, files = act(page, step, ctx, args)
                    else:
                        word, msg = check(page, step, ctx, int(step.get("timeout", args.timeout)))
                except LookupError as e:
                    word, msg = ("Issue found" if step.get("do") in ("click", "fill", "select", "check", "uncheck") else "Could not verify"), str(e)
                except c.ConnectorError as e:
                    word, msg = "Could not verify", f"{e}" + (f" {e.hint}" if getattr(e, "hint", "") else "")
                except Exception as e:
                    word, msg = "Could not verify", f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
                ms = int((time.time() - t0) * 1000)
                new_rows = net.since(mark)
                panel_rows = core.net_rows_for_panel(new_rows, urlsplit(page.url).hostname)
                panel.net(panel_rows)
                if word != "Verified":
                    try:
                        files += core.capture(page, shots / f"{next_shot():02d}-{case['id']}-step{si + 1}-{word.split()[0].lower()}.png", full=False)
                    except Exception:
                        pass
                    stopped = True
                msg = core.redact(msg or "")
                panel.step(ci, si, word, msg, ms)
                if any(r["type"] in ("document", "xhr", "fetch") for r in new_rows) and not args.no_network_flash:
                    panel.flash_network(page)
                rel = [str(Path(f).relative_to(core.QA / "runs" / run_name)).replace("\\", "/") for f in files]
                evidence += rel
                steps_out.append({"step": text, "result": word, "detail": msg, "ms": ms, "evidence": rel})
                record.record(run_name, args.task, "step", text, word, msg, ms=ms, net=panel_rows,
                              screenshot=rel or None, case_id=case["id"], tags=case.get("tags"))
                print(f"   {'+' if word == 'Verified' else '!'} {word:16} {text}" + (f"  -> {msg}" if msg and word != "Verified" else ""))
                page.wait_for_timeout(args.slow)
            last_target = next((s.get("target") for s in reversed(case["steps"]) if s.get("target")), None)
            if last_target:
                # A check like "visible" only asserts the element isn't hidden by CSS - it never requires
                # the element to actually be scrolled into view, so without this the final-state screenshot
                # below just shows wherever the viewport happened to be left (often the top of the page),
                # not the section the case actually verified. Scroll to it first so the screenshot matches
                # what was being checked.
                try:
                    core.locate(page, last_target).first.scroll_into_view_if_needed(timeout=3000)
                    page.wait_for_timeout(150)
                except Exception:
                    pass
            end_rel = []
            try:
                # Viewport only, never full-page: this is "what does the screen look like right now", the
                # same framing as the per-step failure screenshots above, not a scrolled-through stitch of
                # the whole page - full_page=True on a long or infinite-scroll page produces an unreadably
                # tall, narrow strip and makes capture() scroll through everything just for one thumbnail.
                end = core.capture(page, shots / f"{next_shot():02d}-{case['id']}-end.png", full=False, net=net)
                end_rel = [str(Path(f).relative_to(core.QA / "runs" / run_name)).replace("\\", "/") for f in end]
                evidence += end_rel
            except Exception:
                pass
            result = next((s["result"] for s in steps_out if s["result"] != "Verified"), "Verified")
            panel.case(ci, result)
            # The case's own screenshot is just its final-state capture (above) - never the per-step failure
            # screenshots, which are already attached to their own step events. Without this, a case that
            # passes end to end has no screenshot anywhere in the report: step screenshots are only taken
            # on failure, so "all steps passed" used to mean "zero visual evidence this ever ran."
            record.record(run_name, args.task, "case", case["title"], result,
                          f"{sum(1 for s in steps_out if s['result'] == 'Verified')}/{len(steps_out)} step(s) verified",
                          case_id=case["id"], tags=case.get("tags"), screenshot=end_rel or None)
            cases_out.append({"id": case["id"], "title": case["title"], "result": result, "steps": steps_out, "evidence": evidence})
        totals = {w: sum(1 for k in cases_out if k["result"] == w) for w in RESULTS}
        panel.done("Finished: " + ", ".join(f"{n} {w}" for w, n in totals.items() if n))
    write_results(folder, run_name, scenario, home, started, cases_out)
    return cases_out


def write_results(folder, run_name, scenario, home, started, cases_out):
    data = {"scenario": scenario.get("name"), "site": home["name"], "started": started.isoformat(timespec="seconds"),
            "finished": datetime.datetime.now().isoformat(timespec="seconds"), "cases": cases_out}
    (folder / "results.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    lines = [f"# Scenario results: {scenario.get('name', '')}", "",
             f"Site: {home['name']}. Started {data['started']}, finished {data['finished']}.",
             "Result words: Verified, Issue found, Could not verify, Not tested.", "",
             "| ID | Test case | Result | Evidence |", "|----|-----------|--------|----------|"]
    for k in cases_out:
        lines.append(f"| {k['id']} | {k['title']} | {k['result']} | {', '.join(k['evidence'][-2:])} |")
    for k in cases_out:
        lines += ["", f"## {k['id']}: {k['title']} ({k['result']})", ""]
        for i, s in enumerate(k["steps"], 1):
            detail = f": {s['detail']}" if s["detail"] else ""
            lines.append(f"{i}. {s['result']} - {s['step']}{detail}")
    (folder / "results.md").write_text(core.redact("\n".join(lines)) + "\n", encoding="utf-8")
    print(f"\nResults: {folder / 'results.md'}")
    for w in RESULTS:
        n = sum(1 for k in cases_out if k["result"] == w)
        if n:
            print(f"  {n} {w}")
