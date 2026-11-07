"""Browser engine: test a website in one visible Chrome window, with a Cypress-style runner panel
docked inside it (not a second window).

Start and look around
    python qa-tester/browser/run.py start [url] [--devtools] [--no-panel]   open Chrome, panel docked right
    python qa-tester/browser/run.py status | stop | panel
    python qa-tester/browser/run.py mobile iphone|android|tablet|WIDTHxHEIGHT|off   switch the live page's viewport
    python qa-tester/browser/run.py goto <url>          open a page and wait until it has really finished
    python qa-tester/browser/run.py snapshot            the page as text (headings, labels, buttons, tables)
    python qa-tester/browser/run.py elements            every button, link and field, with visible/hidden/disabled
    python qa-tester/browser/run.py state "<target>"    everything about one element (visible, disabled, covered, ...)
    python qa-tester/browser/run.py scroll down|up|top|bottom | --to "<target>"
    python qa-tester/browser/run.py screenshot [--viewport]   the whole page by default (it scrolls through it first)

Act and check (one step at a time)
    login | click "<target>" | fill "<target>" "<value>" | select "<target>" "<option>" | press <Key> | hover "<target>"
    expect <check> ["<target>"] [--value V] [--not]       for example: expect disabled "Export"

Run a whole scenario (test cases, live in the panel, results saved)
    python qa-tester/browser/run.py play <scenario.json> --run <run> [--task <task>]

Network and storage
    watch [--seconds 30]    record the calls while the user clicks by hand
    cookies                 cookies and browser storage, values hidden
    crawl [--max 30]        follow links read-only and record every page

Review afterwards (once the browser, or the whole demo, is done)
    python qa-tester/browser/run.py report [--run NAME] [--open]
        Every ad hoc command, scenario step, and crawled page is appended, in order, with a run-wide
        sequential id, to qa-tester/runs/NAME/events.jsonl as it happens - the panel only shows what is
        running right now and loses it (network calls included) when the browser closes; this does not.
        `report` turns that into one standalone qa-tester/runs/NAME/report.html: summary counts, every
        recorded step in order with its result, timing, screenshot and network calls, filterable by result.
        Open the file directly - no server, no Chrome, no Playwright needed.

Options for goto/click/fill/select/press/login/scroll: --run NAME --task TASK (save a full-page screenshot and the
network calls into qa-tester/runs/NAME/tasks/TASK/), --viewport (only the visible part), --all-net, --max-wait MS.
How to name an element ("<target>"): see GUIDE.md.

No .env file is needed. The site and login come from the Login section of the active test run's plan.md
(qa-tester/test-run.py new / use), or from qa-tester/environments(.local).md for a site used again and again.
Only those sites can be opened.

The runner panel is a docked overlay inside the one Chrome window, not a window of its own: a header button
(and `mobile` mode automatically) collapses it to a small floating circle so it never covers what you are
testing; tap the circle to bring it back.
"""
import argparse
import datetime
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

sys.dont_write_bytecode = True  # this folder lives in a cloud-synced Downloads dir where mtimes can lag a
# save, which fools Python's pyc cache into serving stale compiled modules (bit us twice on report.py) -
# recompiling from source every run is cheap at this project's size, so just never cache.

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402
import panel as panel_mod  # noqa: E402
import player  # noqa: E402
import record  # noqa: E402
import report as report_mod  # noqa: E402
from core import c  # noqa: E402


# ---------------------------------------------------------------- helpers for single commands

class Step:
    """Wraps one hand-run command: records network and console, waits for the page, logs to the panel, saves
    evidence, and appends a durable event (record.py) so it shows up in `report` later - including the
    network calls it made, which the live panel only ever shows, never saves, on its own."""

    def __init__(self, page, a, label):
        self.page, self.a, self.label, self.t0 = page, a, label, time.time()
        self.net, self.console = core.Net(page), []
        page.on("console", lambda m: self.console.append(m.text[:200]) if m.type == "error" else None)
        self.panel = panel_mod.Panel.existing(page)
        self.panel.activity("Investigating: " + label.replace("-", ": ", 1))

    def finish(self, result, text, msg="", wait=True):
        if wait:
            ms, finished = core.settle(self.page, self.net, self.a.max_wait)
            print(f"Ready after {ms} ms" + ("" if finished else f"  (STILL LOADING after {self.a.max_wait} ms)"))
        core.check_allowed(self.page.url)
        if self.console:
            print(f"Console errors: {len(self.console)}")
            for m in self.console[:5]:
                print(f"  - {m}")
        core.net_summary(self.net, self.page, self.a, self.label)
        shots = core.step_shot(self.page, self.a, self.label, self.net)
        self.panel.log(result, text, msg)
        self.panel.done(f"Idle - last: {text} ({result})")
        rows = self.net.current()
        panel_rows = core.net_rows_for_panel(rows, urlsplit(self.page.url).hostname)
        self.panel.net(panel_rows)
        if any(r["type"] in ("document", "xhr", "fetch") for r in rows):
            self.panel.flash_network(self.page)
        run = getattr(self.a, "run", None) or core.active_run()
        record.record(run, getattr(self.a, "task", None), "command", text, result, msg,
                      ms=int((time.time() - self.t0) * 1000), net=panel_rows,
                      screenshot=[record.rel_to_run(run, p) for p in shots] if run else None)


def target_of(page, target):
    loc = core.locate(page, target)
    if loc.count() == 0:
        raise c.ConnectorError(f'"{target}" was not found on the page (also searched inside frames).',
                               "Run `elements` or `snapshot` to see what is there, then name it another way (GUIDE.md).")
    return loc.first


# ---------------------------------------------------------------- start, stop, status

def cmd_start(a):
    url = a.url or core.site()["url"]
    core.check_allowed(url)
    if core.alive():
        print(f"Browser already open on port {core.PORT}.")
    else:
        core.launch(url, devtools=a.devtools)
        print(f"Opened a visible browser window on {url}." + (" DevTools is open in each tab." if a.devtools else ""))
    if not a.no_panel:
        with core.session() as (_, page):
            ok = panel_mod.Panel.open(page).ok
        print("Runner panel docked on the right." if ok else "Could not open the runner panel; tests still work.")
        core.bridge_start()
        print("The panel's Desktop/iPhone/Android/Tablet buttons are live." if core.bridge_alive() else
              "Could not start the panel's device buttons; the `mobile` command still works.")


def cmd_panel(a):
    with core.session() as (_, page):
        ok = panel_mod.Panel.open(page).ok
    print("Runner panel docked on the right." if ok else "Could not open the runner panel.")


def cmd_mobile(a):
    with core.session() as (browser, page):
        core.check_allowed(page.url)
        d = core.mobile(browser, page, a.device)
        p = panel_mod.Panel.existing(page)
        if d is None:
            print("Back to desktop size.")
            p.collapse(False)
            p.device("desktop")
            p.log("Verified", "mobile off", "back to desktop size")
            record.record(core.active_run(), None, "command", "mobile off", "Verified", "back to desktop size")
        else:
            print(f"Window resized to {d['width']}x{d['height']}.")
            p.collapse(True)
            p.device(a.device)
            msg = f"{d['width']}x{d['height']}, panel collapsed to a circle"
            p.log("Verified", f"mobile {a.device}", msg)
            record.record(core.active_run(), None, "command", f"mobile {a.device}", "Verified", msg)


def cmd_status(a):
    print(f"Browser open: {'yes' if core.alive() else 'no'} (port {core.PORT})")
    print(f"Panel device buttons live: {'yes' if core.bridge_alive() else 'no'}")
    run = core.active_run()
    if run:
        info = core.run_login(run)
        have = "username and password are filled in" if info.get("user") and info.get("password") else \
               "username or password is still a placeholder" if info.get("site") else "no Login section filled in yet"
        print(f"Active run: {run}  ({have})")
    else:
        print("Active run: none. Create one: python qa-tester/test-run.py new \"<topic>\" --site <address>")
    for s in core.sites():
        tag = "from the active run's plan.md" if s.get("from_run") else "from environments(.local).md"
        print(f"Allowed site: {s['name']}  {s['url']}  ({tag})")


def cmd_stop(a):
    core.bridge_stop()
    if not core.alive():
        print("No browser is open.")
        return
    try:
        core.with_page(lambda page: page.context.new_cdp_session(page).send("Browser.close"))
    except Exception:
        pass
    for _ in range(20):
        if not core.alive():
            break
        time.sleep(0.5)
    print("Closed the browser. The saved login session stays in qa-tester/.browser-profile (private).")


# ---------------------------------------------------------------- looking

def cmd_goto(a):
    core.check_allowed(a.url)

    def go(page):
        s = Step(page, a, "goto-" + (urlsplit(a.url).path.split("/")[-1] or "home"))
        resp = page.goto(a.url, wait_until="domcontentloaded", timeout=60000)
        status = resp.status if resp else None
        print(f"Title: {page.title()}\nURL: {page.url}\nStatus: {status}")
        s.finish("Issue found" if status and status >= 400 else "Verified", f"open {a.url}", f"HTTP {status}")
    core.with_page(go)


def cmd_snapshot(a):
    def snap(page):
        core.check_allowed(page.url)
        out = [f"URL: {page.url}", f"Title: {page.title()}", ""]
        for i, frame in enumerate(page.frames):
            if i:
                out.append(f"--- frame {i}: {frame.url[:120]}")
            out.append(frame.locator("body").aria_snapshot())
        return "\n".join(out)
    c.show_text(core.redact(core.with_page(snap)), "snapshot")


def cmd_elements(a):
    def look(page):
        core.check_allowed(page.url)
        rows = core.list_elements(page)
        if a.filter:
            rows = [r for r in rows if a.filter.lower() in r["name"].lower() or a.filter.lower() in r["role"]]
        if a.hidden:
            rows = [r for r in rows if not r["visible"]]
        if a.disabled:
            rows = [r for r in rows if r["disabled"]]
        print(f"{len(rows)} element(s). Frame 0 is the page itself; higher numbers are frames inside it.")
        c.show_table([[r["frame"], r["role"], r["name"] or "(no name)", "visible" if r["visible"] else "HIDDEN",
                       "DISABLED" if r["disabled"] else "enabled", "" if r["checked"] is None else ("checked" if r["checked"] else "not checked"),
                       "yes" if r["inView"] else "no"] for r in rows],
                     ["frame", "role", "name", "shown", "state", "checked", "in view"], "elements")
    core.with_page(look)


def cmd_state(a):
    def look(page):
        core.check_allowed(page.url)
        loc = core.locate(page, a.target)
        s = core.element_state(loc)
        print(f'"{a.target}": {core.describe_state(s)}')
        if s["exists"]:
            core.show(loc.first, page)
            keys = ["count", "tag", "type", "visible", "hiddenWhy", "enabled", "disabledAttr", "ariaDisabled", "fieldsetDisabled",
                    "checked", "editable", "readonly", "required", "inView", "covered", "clickable", "ariaHidden", "text", "value"]
            c.show_table([[k, s.get(k, "")] for k in keys if k in s], ["property", "value"], "state")
        word = "Verified" if s["exists"] else "Issue found"
        panel_mod.Panel.existing(page).log(word, f'state of "{a.target}"', core.describe_state(s))
        record.record(getattr(a, "run", None) or core.active_run(), getattr(a, "task", None), "command",
                      f'state of "{a.target}"', word, core.describe_state(s))
    core.with_page(look)


def cmd_scroll(a):
    def go(page):
        core.check_allowed(page.url)
        s = Step(page, a, "scroll-" + (a.to or a.where))
        if a.to:
            core.show(target_of(page, a.to), page)
            print(f'Scrolled to "{a.to}".')
        else:
            info = core.scroll(page, a.where, a.pixels)
            more = "end of the page" if info["to"] >= info["max"] else f"{info['max'] - info['to']} px more below"
            print(f"Scrolled {a.where}: now at {info['to']} of {info['max']} px ({more})" + (" in the page's inner scroll area" if info["inner"] else ""))
        s.finish("Verified", f"scroll {'to ' + a.to if a.to else a.where}", wait=False)
    core.with_page(go)


def cmd_screenshot(a):
    folder = core.task_folder(a.run or "adhoc", a.task, "screenshots")
    name = re.sub(r"[^a-z0-9-]+", "-", (a.name or datetime.datetime.now().strftime("%H%M%S")).lower())

    def shot(page):
        core.check_allowed(page.url)
        for p in core.capture(page, folder / f"{name}.png", full=not a.viewport):
            print(f"Saved {p}")
    core.with_page(shot)


# ---------------------------------------------------------------- acting

def cmd_click(a):
    if (core.RISKY.search(a.text)) and not a.write:
        c.require_write(a, f"click '{a.text}'")

    def click(page):
        core.check_allowed(page.url)
        s = Step(page, a, "click-" + a.text)
        el = core.find(page, lambda f: f.get_by_role(a.role, name=a.text)) if a.role else target_of(page, a.text)
        st = core.element_state(core.locate(page, a.text)) if not a.role else None
        if st and st["exists"] and not st["enabled"]:
            print(f'Note: "{a.text}" is disabled ({core.describe_state(st)}). Clicking it should do nothing.')
        core.show(el, page)
        el.click(timeout=15000)
        print(f"Clicked '{a.text}'.")
        s.finish("Verified", f'click "{a.text}"')
        print(f"Now at: {page.url}  ({page.title()})")
    core.with_page(click)


def cmd_fill(a):
    def fill(page):
        core.check_allowed(page.url)
        s = Step(page, a, "fill-" + a.field)
        value, secret = player.secret_value(a.value)
        core.type_into(page, target_of(page, a.field), value)
        print(f"Filled '{a.field}'" + (" with a hidden value." if secret else "."))
        s.finish("Verified", f'type into "{a.field}"', wait=False)
    core.with_page(fill)


def cmd_select(a):
    def select(page):
        core.check_allowed(page.url)
        s = Step(page, a, "select-" + a.field)
        el = target_of(page, a.field)
        core.show(el, page)
        try:
            el.select_option(label=a.option, timeout=10000)
        except Exception:
            el.select_option(value=a.option, timeout=10000)
        print(f"Chose '{a.option}' in '{a.field}'.")
        s.finish("Verified", f'choose "{a.option}" in "{a.field}"')
    core.with_page(select)


def cmd_press(a):
    def press(page):
        core.check_allowed(page.url)
        s = Step(page, a, "press-" + a.key)
        page.keyboard.press(a.key)
        print(f"Pressed {a.key}.")
        s.finish("Verified", f"press {a.key}")
    core.with_page(press)


def cmd_hover(a):
    def hover(page):
        core.check_allowed(page.url)
        s = Step(page, a, "hover-" + a.target)
        el = target_of(page, a.target)
        core.show(el, page)
        el.hover(timeout=10000)
        print(f"Pointing at '{a.target}'.")
        s.finish("Verified", f'point at "{a.target}"', wait=False)
    core.with_page(hover)


def cmd_expect(a):
    step = {"expect": a.check, "target": a.target, "value": a.value, "name": a.name, "status": a.status, "not": a.negate}
    step = {k: v for k, v in step.items() if v not in (None, False)}
    if a.check not in player.CHECKS:
        raise c.ConnectorError(f"Unknown check '{a.check}'.", "Use one of: " + ", ".join(sorted(player.CHECKS)))
    if a.check in ("no-console-errors", "no-failed-requests", "request"):
        raise c.ConnectorError("Network and console checks need to watch a page load.",
                               "Use them inside a scenario (play), or read the network list that goto/click print.")
    problems = player.validate({"cases": [{"id": "X", "title": "x", "steps": [step]}]})
    if problems:
        raise c.ConnectorError(problems[0].replace("case X, step 1: ", ""))

    def run(page):
        core.check_allowed(page.url)
        word, msg = player.check(page, step, {"net": None, "console": [], "net_mark": 0, "console_mark": 0}, a.timeout)
        if a.target:
            loc = core.locate(page, a.target)
            if loc.count():
                core.show(loc.first, page)
        print(f"{word}: {player.describe(step)}" + (f"\n  {msg}" if msg else ""))
        panel_mod.Panel.existing(page).log(word, player.describe(step), msg if word != "Verified" else "")
        record.record(core.active_run(), None, "command", player.describe(step), word, msg)
        return word
    word = core.with_page(run)
    sys.exit(0 if word == "Verified" else 1)


def cmd_login(a):
    home = core.site(a.site)

    def login(page):
        core.check_allowed(page.url)
        s = Step(page, a, "login")
        word, msg = core.login(page, home, s.net)
        print(msg)
        s.finish(word, "sign in", msg, wait=False)
    core.with_page(login)


def cmd_play(a):
    core.save_last_play(sys.argv[1:])
    cases = player.run(a.scenario, a)
    sys.exit(0 if all(k["result"] == "Verified" for k in cases) else 1)


# ---------------------------------------------------------------- network and storage

def cmd_watch(a):
    """Record what the page asks for while the user clicks around by hand: the Network tab, as text."""
    def watch(page):
        s = Step(page, a, "watch")
        print(f"Watching the network for {a.seconds} s. Use the browser window now...")
        s.panel.tab("network")
        page.wait_for_timeout(a.seconds * 1000)
        print(f"Page now: {page.url}  ({page.title()})")
        s.finish("Verified", f"watched the network for {a.seconds} s", wait=False)
    core.with_page(watch)


def cmd_cookies(a):
    """List the cookies and browser storage. Values are never printed: only names, flags, lifetime, and size."""
    def look(page):
        core.check_allowed(page.url)
        now, rows, findings = time.time(), [], []
        hosts = {s["host"] for s in core.sites()}
        for ck in page.context.cookies():
            exp = ck.get("expires", -1)
            secs = 0 if exp in (-1, None) else max(0, exp - now)
            life = "session" if exp in (-1, None) else (f"{int(secs / 86400)} d" if secs >= 86400 else f"{int(secs / 3600)} h")
            same = ck.get("sameSite", "None")
            rows.append([ck["name"], ck["domain"], ck["path"], life, "yes" if ck["httpOnly"] else "NO",
                         "yes" if ck["secure"] else "NO", same, len(ck["value"])])
            if ck["domain"].lstrip(".") in hosts and re.search(r"auth|sess|token|sid|login", ck["name"], re.I):
                if not ck["httpOnly"]:
                    findings.append(f"'{ck['name']}' looks like a session/auth cookie but page scripts can read it (no HttpOnly)")
                if not ck["secure"]:
                    findings.append(f"'{ck['name']}' looks like a session/auth cookie but is not marked Secure")
                if same == "None":
                    findings.append(f"'{ck['name']}' has SameSite=None (sent on cross-site requests)")
                if life.endswith(" d") and int(life.split()[0]) > 30:
                    findings.append(f"'{ck['name']}' lives {life}")
        c.show_table(rows, ["name", "domain", "path", "lifetime", "httpOnly", "secure", "sameSite", "size"], "cookies")
        store = page.evaluate("""() => {
          const out = [];
          for (const [kind, s] of [['localStorage', window.localStorage], ['sessionStorage', window.sessionStorage]]) {
            for (let i = 0; i < s.length; i++) {
              const k = s.key(i), v = s.getItem(k) || '';
              out.push({store: kind, key: k, size: v.length, looks_like_jwt: /^eyJ[\\w-]+\\.[\\w-]+\\./.test(v)});
            }
          }
          return out;
        }""")
        print("\nBrowser storage (names and sizes only):")
        if store:
            c.show_table([[s["store"], s["key"], s["size"], s["looks_like_jwt"]] for s in store], ["store", "key", "size", "looks_like_jwt"], "storage")
        else:
            print("  (empty)")
        findings += [f"{s['store']} key '{s['key']}' holds what looks like a token (readable by any script on the page)" for s in store if s["looks_like_jwt"]]
        print("\nThings worth a look:" if findings else "\nNothing suspicious by the simple checks.")
        for f in findings:
            print(f"  - {f}")
    core.with_page(look)


SKIP_URL = re.compile(r"log(out|off)|sign-?out|delete|remove|download|export|\.(pdf|csv|xlsx?|zip|docx?)(\?|$)|^javascript:|^mailto:", re.I)
PROBE_JS = """() => ({
  headings: [...document.querySelectorAll('h1,h2,h3')].slice(0, 5).map(h => h.innerText.trim()).filter(Boolean),
  inputs: [...document.querySelectorAll('input:not([type=hidden]),select,textarea')].slice(0, 10)
            .map(i => i.getAttribute('aria-label') || i.placeholder || i.name || i.id || i.type),
  buttons: [...document.querySelectorAll('button,input[type=submit],input[type=button]')].slice(0, 8)
            .map(b => (b.innerText || b.value || '').trim()).filter(Boolean),
  tables: [...document.querySelectorAll('table')].slice(0, 3)
            .map(t => [...t.querySelectorAll('th')].slice(0, 8).map(h => h.innerText.trim()).filter(Boolean)).filter(h => h.length),
  libs: [...document.scripts].map(s => s.src).filter(s => /fusioncharts|highcharts|chart|jquery|angular|react|vue|bootstrap/i.test(s))
            .map(s => s.split('/').pop().split('?')[0]),
  highcharts: (typeof Highcharts !== 'undefined' && Highcharts.version) || null,
  fusioncharts: (typeof FusionCharts !== 'undefined' && FusionCharts.version && FusionCharts.version.join('.')) || null,
  textLength: document.body ? document.body.innerText.length : 0,
  links: [...document.querySelectorAll('a[href]')].map(a => ({h: a.href, t: (a.innerText || a.title || '').trim().slice(0, 60)}))
})"""


def cmd_crawl(a):
    """Visit pages by following links only (read-only). Wait for each page, capture all of it, record what it loads."""
    home = core.site(a.site)
    run_name = a.run or "crawl-" + core.stamp()
    folder = core.QA / "runs" / run_name / "tasks" / a.task if a.task else core.QA / "runs" / run_name
    (folder / "pages").mkdir(parents=True, exist_ok=True)
    results = []

    def crawl(page):
        net, console = core.Net(page), []
        page.on("console", lambda m: console.append(m.text[:160]) if m.type == "error" else None)
        panel = panel_mod.Panel.existing(page)
        scope = (urlsplit(a.scope or home["url"]).path.rstrip("/") or "") + "/"
        queue, seen = list(a.start or [page.url]), set()
        while queue and len(results) < a.max:
            url = queue.pop(0).split("#")[0]
            if url.lower() in seen or SKIP_URL.search(url):
                continue
            seen.add(url.lower())
            console.clear()
            net.reset()
            row = {"url": url, "title": "", "status": None, "error": ""}
            try:
                core.check_allowed(url)
                resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
                ready_ms, finished = core.settle(page, net, a.max_wait)
                row.update(status=resp.status if resp else None, title=page.title(), ready_ms=ready_ms, finished=finished)
                if re.search(r"login", page.url, re.I) and not re.search(r"login", url, re.I):
                    row["error"] = "sent back to login (session ended)"
                    results.append(row)
                    break
                info = page.evaluate(PROBE_JS)
                reqs = net.current()
                row.update(info=info, console=list(console),
                           failed=[f"{r['method']} {r['status'] or r['failed']} {core.safe_url(r['url'], home['host'])}" for r in reqs if core.is_bad(r)],
                           requests=len(reqs),
                           xhr=[f"{r['method']} {r['status']} {r['ms']}ms {core.safe_url(r['url'], home['host'])}" for r in reqs if r["type"] in ("xhr", "fetch")])
                if info["textLength"] < 20:
                    row["error"] = "page looks blank"
                name = f"{len(results) + 1:03d}-{re.sub(r'[^a-z0-9]+', '-', urlsplit(page.url).path.lower()).strip('-')[-40:]}.png"
                shot_paths = core.capture(page, folder / "pages" / name, full=not a.viewport, net=net)
                row["shots"] = [p.name for p in shot_paths]
                panel_rows = core.net_rows_for_panel(reqs, home["host"])
                panel.net(panel_rows)
                word = "Issue found" if row["error"] or row["failed"] else "Verified"
                detail = row["error"] or (f"{len(row['failed'])} failed call(s)" if row["failed"] else "")
                panel.log(word, f"crawl: {row['title'][:60]}", detail)
                record.record(run_name, a.task, "crawl", f"crawl: {row['title'][:60] or url}", word, detail,
                              ms=row.get("ready_ms"), net=panel_rows,
                              screenshot=[record.rel_to_run(run_name, p) for p in shot_paths])
                for link in info["links"]:
                    h = link["h"].split("#")[0]
                    u = urlsplit(h)
                    if u.hostname == home["host"] and u.path.startswith(scope) and h.lower() not in seen \
                            and not SKIP_URL.search(h) and not core.RISKY.search(link["t"]) and (not a.match or re.search(a.match, h, re.I)):
                        queue.append(h)
            except c.ConnectorError as e:
                row["error"] = str(e)
            except Exception as e:   # one bad page must not stop the walk
                row["error"] = type(e).__name__ + ": " + str(e).splitlines()[0][:150]
            results.append(row)
            note = "" if row.get("finished", True) else "  (still loading at the limit)"
            print(f"[{len(results):02d}] {row['status'] or '---'} {row['title'][:42] or row['error'][:50]:42} {row.get('ready_ms', 0) / 1000:5.1f}s "
                  f"{row.get('requests', 0):3} req  {urlsplit(url).path}{note}")
            page.wait_for_timeout(a.pause)
    core.with_page(crawl)
    write_crawl_report(folder, run_name, home, results)


def cmd_report(a):
    run = a.run or core.last_touched_run() or core.active_run()
    if not run:
        raise c.ConnectorError("No run given and no active run.", "Pass --run NAME, or set one active with "
                               "qa-tester/test-run.py use.")
    path, events, counts, build_id, built_at = report_mod.build(run)
    print(f"Report: {path}")
    print(f"Build {build_id} · generated {built_at} - if a tab already open on this file shows a different "
          "build id, it's stale: reload it.")
    print(f"{len(events)} recorded event(s).")
    for w in report_mod.RESULTS:
        if counts.get(w):
            print(f"  {counts[w]} {w}")
    if a.open:
        import webbrowser
        webbrowser.open(path.resolve().as_uri())


def write_crawl_report(folder, run_name, home, results):
    def problem(r):
        return r["error"] or r.get("console") or r.get("failed") or not r.get("finished", True)
    out = [f"# Crawl: {run_name}", "", f"Site: {home['name']}", f"Date: {datetime.date.today().isoformat()}",
           f"Pages visited: {len(results)}. With a problem: {sum(1 for r in results if problem(r))}.", "",
           "| # | Page | Title | Status | Ready (s) | Requests | XHR | Console errors | Failed | Charts/libs | Screenshot |",
           "|---|------|-------|--------|-----------|----------|-----|----------------|--------|-------------|------------|"]
    for i, r in enumerate(results, 1):
        info, u = r.get("info", {}), urlsplit(r["url"])
        libs = ", ".join(filter(None, [f"Highcharts {info['highcharts']}" if info.get("highcharts") else "",
                                       f"FusionCharts {info['fusioncharts']}" if info.get("fusioncharts") else "",
                                       *sorted(set(info.get("libs", [])))]))
        out.append(f"| {i} | {u.path.split('/')[-1]}{('?' + u.query) if u.query else ''} | {r['title'] or r['error']} | {r['status'] or ''} | "
                   f"{r.get('ready_ms', 0) / 1000:.1f}{'' if r.get('finished', True) else '+'} | {r.get('requests', '')} | {len(r.get('xhr', []))} | "
                   f"{len(r.get('console', []))} | {len(r.get('failed', []))} | {libs} | {', '.join(r.get('shots', []))} |")
    out += ["", "## Problems", ""]
    for r in results:
        if problem(r):
            out.append(f"- {r['url']}")
            if r["error"]:
                out.append(f"  - error: {r['error']}")
            if not r.get("finished", True):
                out.append("  - still loading when the wait limit was reached")
            out += [f"  - console: {m}" for m in r.get("console", [])[:3]] + [f"  - request: {m}" for m in r.get("failed", [])[:3]]
    out += ["", "## What each page has", ""]
    for r in results:
        if r["error"] and "info" not in r:
            continue
        info = r.get("info", {})
        out += [f"### {r['title']}  ({urlsplit(r['url']).path.split('/')[-1]})",
                f"- Headings: {'; '.join(info.get('headings', [])) or '-'}",
                f"- Fields: {', '.join(info.get('inputs', [])) or '-'}",
                f"- Buttons: {', '.join(info.get('buttons', [])) or '-'}"]
        out += [f"- Table columns: {', '.join(t)}" for t in info.get("tables", [])]
        out += [f"- Data call: {x}" for x in r.get("xhr", [])[:6]] + [""]
    text = core.redact("\n".join(out)) + "\n"
    (folder / "crawl-report.md").write_text(text, encoding="utf-8")
    sites_dir = core.QA / "sites"
    sites_dir.mkdir(exist_ok=True)
    (sites_dir / f"{home['name']}.md").write_text(text.replace(f"# Crawl: {run_name}", f"# Site map: {home['name']} (from crawl {run_name})"), encoding="utf-8")
    print(f"\nReport: {folder / 'crawl-report.md'}\nSite map: {sites_dir / (home['name'] + '.md')}")


# ---------------------------------------------------------------- command line

def main():
    p = argparse.ArgumentParser(description="Test a website in a visible Chrome window with a runner panel.",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n", 2)[2])
    sub = p.add_subparsers(dest="cmd", required=True, metavar="command")
    step = argparse.ArgumentParser(add_help=False)
    step.add_argument("--run", help="save a full-page screenshot and the network calls under qa-tester/runs/RUN/")
    step.add_argument("--task", help="inside the run, use the task folder tasks/TASK/")
    step.add_argument("--viewport", action="store_true", help="screenshot only the visible part, not the whole page")
    step.add_argument("--all-net", action="store_true", help="also list images, styles and fonts")
    step.add_argument("--max-wait", type=int, default=20000, help="ms to wait for a slow page (default 20000)")

    def add(name, fn, help_, parents=()):
        sp = sub.add_parser(name, help=help_, parents=list(parents))
        sp.set_defaults(fn=fn)
        return sp

    s = add("start", cmd_start, "open Chrome and the runner panel")
    s.add_argument("url", nargs="?")
    s.add_argument("--devtools", action="store_true", help="open Chrome's DevTools in every tab (its Network tab shows all calls)")
    s.add_argument("--no-panel", action="store_true", help="do not open the runner panel")
    add("status", cmd_status, "is the browser open; which sites are allowed")
    add("stop", cmd_stop, "quit the browser")
    add("panel", cmd_panel, "make sure the runner panel is docked on the right")
    m = add("mobile", cmd_mobile, "switch the live page to a phone/tablet viewport, or back to desktop")
    m.add_argument("device", nargs="?", default="iphone", help="iphone, android, tablet, WIDTHxHEIGHT, or off (default: iphone)")
    g = add("goto", cmd_goto, "open a page and wait until it has finished", [step])
    g.add_argument("url")
    add("snapshot", cmd_snapshot, "the page as text")
    e = add("elements", cmd_elements, "every button, link and field with its state")
    e.add_argument("--filter", help="only names or roles containing this text")
    e.add_argument("--hidden", action="store_true", help="only hidden ones")
    e.add_argument("--disabled", action="store_true", help="only disabled ones")
    st = add("state", cmd_state, "everything about one element")
    st.add_argument("target")
    sc = add("scroll", cmd_scroll, "scroll the page", [step])
    sc.add_argument("where", nargs="?", default="down", choices=["down", "up", "top", "bottom"])
    sc.add_argument("--to", help="scroll until this element is in view")
    sc.add_argument("--pixels", type=int, help="how far for down/up (default: most of a screen)")
    sh = add("screenshot", cmd_screenshot, "save a screenshot (whole page by default)")
    sh.add_argument("--run")
    sh.add_argument("--task")
    sh.add_argument("--name")
    sh.add_argument("--viewport", action="store_true", help="only the visible part")
    k = add("click", cmd_click, "click an element", [step])
    k.add_argument("text", metavar="target")
    k.add_argument("--role", help="button, link, tab, ... (narrows the search)")
    k.add_argument("--write", action="store_true", help="allow clicks that may change data (needs the user's OK)")
    f = add("fill", cmd_fill, "type into a field ($password, $user: the run's login; never shown)", [step])
    f.add_argument("field", metavar="target")
    f.add_argument("value")
    se = add("select", cmd_select, "choose an option in a dropdown", [step])
    se.add_argument("field", metavar="target")
    se.add_argument("option")
    pr = add("press", cmd_press, "press a key, for example Enter or Escape", [step])
    pr.add_argument("key")
    hv = add("hover", cmd_hover, "point at an element (opens hover menus)", [step])
    hv.add_argument("target")
    x = add("expect", cmd_expect, "check one thing, retrying until it holds; exit code 1 if not")
    x.add_argument("check", help="visible, hidden, enabled, disabled, checked, unchecked, editable, readonly, exists, absent, "
                                 "in-view, clickable, covered, text, text-equals, value, count, attribute, url, title, page-text")
    x.add_argument("target", nargs="?")
    x.add_argument("--value")
    x.add_argument("--name", help="attribute name, for the attribute check")
    x.add_argument("--status")
    x.add_argument("--not", dest="negate", action="store_true", help="expect the opposite")
    x.add_argument("--timeout", type=int, default=5000, help="ms to keep retrying (default 5000)")
    lg = add("login", cmd_login, "sign in with the active run's Login section", [step])
    lg.add_argument("--site")
    pl = add("play", cmd_play, "run a scenario file live in the runner panel")
    pl.add_argument("scenario")
    pl.add_argument("--run", help="run folder name under qa-tester/runs/")
    pl.add_argument("--task", help="task folder inside the run")
    pl.add_argument("--site", help="site name, if the scenario does not give one")
    pl.add_argument("--slow", type=int, default=600, help="ms pause after each step so it can be followed (default 600)")
    pl.add_argument("--timeout", type=int, default=5000, help="ms a check keeps retrying (default 5000)")
    pl.add_argument("--max-wait", type=int, default=20000, help="ms to wait for a slow page (default 20000)")
    pl.add_argument("--no-network-flash", action="store_true", help="do not flash the panel's Network tab after steps")
    pl.add_argument("--write", action="store_true", help="allow steps marked \"write\": true (needs the user's OK)")
    w = add("watch", cmd_watch, "record network calls while the user clicks", [step])
    w.add_argument("--seconds", type=int, default=30)
    add("cookies", cmd_cookies, "cookies and storage, values hidden")
    cr = add("crawl", cmd_crawl, "follow links read-only and record every page")
    cr.add_argument("--site")
    cr.add_argument("--run")
    cr.add_argument("--task")
    cr.add_argument("--scope", help="only follow links under this address")
    cr.add_argument("--start", action="append", help="page to start from; repeat to give several")
    cr.add_argument("--match", help="only follow links whose address matches this pattern")
    cr.add_argument("--max", type=int, default=30)
    cr.add_argument("--max-wait", type=int, default=25000)
    cr.add_argument("--pause", type=int, default=800, help="ms between pages so the user can follow")
    cr.add_argument("--viewport", action="store_true", help="capture only the visible part of each page")
    rp = add("report", cmd_report, "build a standalone report.html of everything recorded for a run")
    rp.add_argument("--run", help="defaults to the active run")
    rp.add_argument("--open", action="store_true", help="open it in the default browser once built")
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    c.run(main)
