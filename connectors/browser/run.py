"""Visible browser for QA testing. Opens a real Chrome window you can watch, and drives it step by step.

    python connectors/browser/run.py start [url]            open Chrome (own profile, visible) on an allowed site
    python connectors/browser/run.py goto <url>             go to a page, wait until it has really finished loading
    python connectors/browser/run.py snapshot               the page as text (labels, buttons, links, tables)
    python connectors/browser/run.py screenshot [--run NAME] [--name NAME]
    python connectors/browser/run.py click "<text>" [--role button|link|...] [--write]
    python connectors/browser/run.py fill "<label or placeholder>" "<value>"
    python connectors/browser/run.py login [--site NAME]    log in with the settings named in qa-tester/environments.md
    python connectors/browser/run.py watch [--seconds 30]   record network calls while the user clicks around by hand
    python connectors/browser/run.py cookies                what the site stores: cookies and browser storage (values hidden)
    python connectors/browser/run.py crawl [--max 30]       follow links read-only, record every page
    python connectors/browser/run.py status | stop

goto, click, fill and login accept --run NAME: they then save a screenshot of the result (and the network calls)
under qa-tester/runs/NAME/, numbered in order, so a run reads like a story. They also accept --all-net (show images,
styles, fonts too) and --max-wait MS (how long to wait for slow pages, default 20000).

Only sites listed in qa-tester/environments.md can be opened. The browser stays open between commands,
so the user can watch every step and the login session is kept.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)

QA = HERE.parent.parent / "qa-tester"
PROFILE = QA / ".browser-profile"
PORT = int(os.environ.get("QA_BROWSER_PORT", "9333"))
CDP = f"http://127.0.0.1:{PORT}"
CHROME_PATHS = [
    os.environ.get("QA_CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
RISKY = re.compile(r"\b(delete|remove|cancel order|submit|save|place order|pay|confirm|approve|publish|send)\b", re.I)
BUSY = (".loading:visible, .spinner:visible, .loader:visible, .blockUI:visible, [aria-busy=true]:visible, "
        ".fa-spin:visible, #loading:visible, img[src*=loading]:visible, img[src*=spinner]:visible, [role=progressbar]:visible")
TYPE_DELAY_MS = int(os.environ.get("QA_TYPE_DELAY_MS", "90"))


# ---------- allowed sites ----------

def sites():
    """Rows of the table in qa-tester/environments.md."""
    paths = [p for p in (QA / "environments.md", QA / "environments.local.md") if p.exists()]
    if not paths:
        raise c.ConnectorError("qa-tester/environments.md is missing.", "Restore it from the repository.")
    rows = []
    for path in paths:   # the local file (private, not pushed) holds the real sites
        for line in path.read_text(encoding="utf-8").splitlines():
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and re.match(r"https?://", cells[1]):
                rows.append({"name": cells[0], "url": cells[1], "host": urlsplit(cells[1]).hostname,
                             "settings": re.findall(r"`([A-Z0-9_]+)`", cells[3])})
    return rows


def check_allowed(url):
    host = urlsplit(url).hostname
    if host not in {s["host"] for s in sites()}:
        raise c.ConnectorError(f"'{host}' is not in qa-tester/environments.md.",
                               "Only listed sites can be opened. Ask the user to add the site there.")


# ---------- browser ----------

def alive():
    try:
        urllib.request.urlopen(CDP + "/json/version", timeout=2).read()
        return True
    except OSError:
        return False


def find_chrome():
    for p in CHROME_PATHS:
        if p and Path(p).exists():
            return p
    raise c.ConnectorError("Chrome or Edge was not found.", "Set QA_CHROME_PATH in connectors/browser/.env to the browser's program file.")


def launch(url):
    PROFILE.mkdir(parents=True, exist_ok=True)
    cmd = [find_chrome(), f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
           "--no-first-run", "--no-default-browser-check", "--new-window", "--window-size=1600,1000", "--window-position=40,20", url]
    flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0   # detached, own process group
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
    for _ in range(40):
        if alive():
            return
        time.sleep(0.5)
    raise c.ConnectorError("The browser did not start.", f"Check that port {PORT} is free, or set QA_BROWSER_PORT in .env.")


def playwright_pages():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise c.ConnectorError("The playwright package is not installed.", "Run: pip install playwright")
    return sync_playwright


def with_page(fn):
    """Connect to the open browser, run fn(page), disconnect. The browser stays open."""
    if not alive():
        raise c.ConnectorError("No browser is open.", "Run: python connectors/browser/run.py start")
    sync_playwright = playwright_pages()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.url.startswith("devtools://")]
        page = pages[-1] if pages else context.new_page()
        page.bring_to_front()
        page.on("dialog", lambda d: d.dismiss())
        return fn(page)


def find(page, make):
    """First match of make(frame) in the page or any frame inside it (logins are often in an iframe)."""
    for frame in page.frames:
        loc = make(frame)
        if loc.count() > 0:
            return loc.first
    return make(page.main_frame).first


# ---------- watching it live ----------

CURSOR_JS = """() => {
  if (document.getElementById('__qa_cursor')) return;
  const d = document.createElement('div');
  d.id = '__qa_cursor';
  d.style.cssText = 'position:fixed;z-index:2147483647;width:20px;height:20px;border-radius:50%;background:rgba(255,0,0,.55);' +
    'border:2px solid #fff;box-shadow:0 0 6px rgba(0,0,0,.6);pointer-events:none;left:20px;top:20px;transform:translate(-50%,-50%)';
  document.documentElement.appendChild(d);
  document.addEventListener('mousemove', e => { d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
}"""


def show(locator, page=None):
    """Make the step watchable: scroll to the target, glide a red dot to it, and highlight it."""
    try:
        if page is not None:
            page.evaluate(CURSOR_JS)
            locator.scroll_into_view_if_needed(timeout=5000)
            box = locator.bounding_box()
            if box:
                page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=35)
        locator.highlight()
    except Exception:
        pass
    time.sleep(0.6)


def type_into(page, locator, value):
    """Click the field, clear it, and type one character at a time so the user sees it happen."""
    show(locator, page)
    locator.click()
    locator.fill("")
    locator.press_sequentially(value, delay=TYPE_DELAY_MS)
    time.sleep(0.4)


def redact(text):
    """Hide secrets: any setting whose name ends in PASSWORD, TOKEN or SECRET must never be printed."""
    for key, value in os.environ.items():
        if value and len(value) >= 4 and re.search(r"(PASSWORD|TOKEN|SECRET)$", key):
            text = text.replace(value, "***")
    return text


# ---------- network: what the page asked for ----------

class Net:
    """Records every request the page makes from now on. Never keeps bodies, headers, or query values."""

    def __init__(self, page):
        self.rows, self.by_req, self.mark = [], {}, 0
        page.on("request", self._start)
        page.on("response", self._response)
        page.on("requestfinished", self._finish)
        page.on("requestfailed", self._fail)

    def _start(self, r):
        e = {"method": r.method, "type": r.resource_type, "url": r.url, "t0": time.time(), "status": None, "ms": None,
             "failed": "", "done": False}
        self.by_req[r] = e
        self.rows.append(e)

    def _response(self, resp):
        e = self.by_req.get(resp.request)
        if e:
            e["status"] = resp.status

    def _finish(self, r):
        e = self.by_req.get(r)
        if e:
            e["ms"], e["done"] = int((time.time() - e["t0"]) * 1000), True

    def _fail(self, r):
        e = self.by_req.get(r)
        if e:
            e["ms"], e["done"] = int((time.time() - e["t0"]) * 1000), True
            e["failed"] = (r.failure or "failed")[:60]

    def inflight(self):
        return sum(1 for e in self.rows if not e["done"] and e["type"] not in ("websocket", "eventsource"))

    def reset(self):
        self.mark = len(self.rows)

    def current(self):
        return self.rows[self.mark:]


def safe_url(url, home_host):
    """Path plus the names of the query parameters, never their values (they can hold tokens)."""
    u = urlsplit(url)
    keys = ",".join(k for k, _ in parse_qsl(u.query, keep_blank_values=True))
    where = u.path if u.hostname == home_host else f"{u.hostname}{u.path}"
    return where + (f"?{{{keys}}}" if keys else "")


def task_folder(run, task, kind):
    """runs/<run>/tasks/<task>/<kind>, or runs/<run>/<kind> when no task is given."""
    base = QA / "runs" / run
    return (base / "tasks" / task / kind) if task else (base / kind)


def next_step_file(run, label, ext, task=None):
    folder = task_folder(run, task, "network" if ext == "json" else "screenshots")
    folder.mkdir(parents=True, exist_ok=True)
    n = len(list(folder.glob(f"*.{ext}"))) + 1
    return folder / f"{n:02d}-{re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')[:40]}.{ext}"


def net_summary(net, page, a, label):
    home = urlsplit(page.url).hostname
    rows = net.current()
    interesting = ("document", "xhr", "fetch", "websocket", "eventsource", "other")
    shown = [r for r in rows if getattr(a, "all_net", False) or r["type"] in interesting]
    bad = [r for r in rows if r["failed"] or (r["status"] or 0) >= 400]
    xhr = sum(1 for r in rows if r["type"] in ("xhr", "fetch"))
    slowest = max((r["ms"] or 0 for r in rows), default=0)
    print(f"Network: {len(rows)} requests, {xhr} XHR/fetch, {len(bad)} failed, slowest {slowest} ms")
    for r in shown[:15]:
        print(f"  {r['method']:4} {r['status'] or '---':>3} {r['type']:9} {r['ms'] or 0:>5} ms  {safe_url(r['url'], home)}"
              + (f"  FAILED: {r['failed']}" if r["failed"] else ""))
    if len(shown) > 15:
        print(f"  ... {len(shown) - 15} more (use --run to save all of them)")
    if getattr(a, "run", None):
        path = next_step_file(a.run, label, "json", getattr(a, "task", None))
        path.write_text(json.dumps([{"method": r["method"], "status": r["status"], "type": r["type"], "ms": r["ms"],
                                     "url": safe_url(r["url"], home), "failed": r["failed"]} for r in rows], indent=1), encoding="utf-8")


def settle(page, net, max_ms=20000, quiet_ms=1200):
    """Wait until the page has really finished: no request in flight, no spinner, and the page stops changing."""
    t0, last, stable_since = time.time(), None, time.time()
    while (time.time() - t0) * 1000 < max_ms:
        page.wait_for_timeout(300)
        try:
            sig = page.evaluate("() => [document.body ? document.body.innerText.length : 0, document.querySelectorAll('svg,canvas,img,tr').length]")
            busy = page.locator(BUSY).count()
        except Exception:
            continue
        if net.inflight() or busy or sig != last:
            last, stable_since = sig, time.time()
            continue
        if (time.time() - stable_since) * 1000 >= quiet_ms:
            return int((time.time() - t0) * 1000), True
    return int((time.time() - t0) * 1000), False


def step_shot(page, a, label):
    if getattr(a, "run", None):
        path = next_step_file(a.run, label, "png", getattr(a, "task", None))
        page.screenshot(path=str(path))
        print(f"Screenshot: {path}")


# ---------- commands ----------

def cmd_start(a):
    url = a.url or (sites()[0]["url"] if sites() else None)
    if not url:
        raise c.ConnectorError("No site is listed in qa-tester/environments.md.", "Ask the user for the site to test, and add it there.")
    check_allowed(url)
    if alive():
        print(f"Browser already open on port {PORT}.")
        return
    launch(url)
    print(f"Opened a visible browser window on {url}. The user can watch it.")


def cmd_status(a):
    print(f"Browser open: {'yes' if alive() else 'no'} (port {PORT})")
    for s in sites():
        print(f"Allowed site: {s['name']}  {s['url']}  (login settings: {', '.join(s['settings']) or 'none'})")


def cmd_stop(a):
    if not alive():
        print("No browser is open.")
        return
    try:
        with_page(lambda page: page.context.new_cdp_session(page).send("Browser.close"))   # really quits Chrome
    except Exception:
        pass
    for _ in range(20):
        if not alive():
            break
        time.sleep(0.5)
    print("Closed the browser. The saved login session stays in qa-tester/.browser-profile (private).")


def cmd_goto(a):
    check_allowed(a.url)

    def go(page):
        net, console = Net(page), []
        page.on("console", lambda m: console.append(m.text[:200]) if m.type == "error" else None)
        t0 = time.time()
        resp = page.goto(a.url, wait_until="domcontentloaded", timeout=60000)
        status = resp.status if resp else None
        ready_ms, finished = settle(page, net, a.max_wait)
        check_allowed(page.url)
        print(f"Title: {page.title()}\nURL: {page.url}\nStatus: {status}")
        print(f"Ready after {int((time.time() - t0) * 1000)} ms" + ("" if finished else f"  (STILL LOADING after {a.max_wait} ms; the page may be slow or stuck)"))
        print(f"Console errors: {len(console)}")
        for m in console[:5]:
            print(f"  - {m}")
        net_summary(net, page, a, "goto-" + (urlsplit(page.url).path.split("/")[-1] or "home"))
        step_shot(page, a, "page-" + (urlsplit(page.url).path.split("/")[-1] or "home"))
    with_page(go)


def cmd_snapshot(a):
    def snap(page):
        check_allowed(page.url)
        out = [f"URL: {page.url}", f"Title: {page.title()}", ""]
        for i, frame in enumerate(page.frames):
            if i:
                out.append(f"--- frame {i}: {frame.url[:120]}")
            out.append(frame.locator("body").aria_snapshot())
        return "\n".join(out)
    c.show_text(redact(with_page(snap)), "snapshot")


def cmd_screenshot(a):
    folder = task_folder(a.run or "adhoc", a.task, "screenshots")
    folder.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^a-z0-9-]+", "-", (a.name or datetime.datetime.now().strftime("%H%M%S")).lower())
    path = folder / f"{name}.png"

    def shot(page):
        check_allowed(page.url)
        page.screenshot(path=str(path), full_page=a.full)
    with_page(shot)
    print(f"Saved {path}")


def cmd_click(a):
    if RISKY.search(a.text) and not a.write:
        c.require_write(a, f"click '{a.text}'")

    def click(page):
        check_allowed(page.url)
        net = Net(page)
        loc = find(page, lambda f: f.get_by_role(a.role, name=a.text) if a.role else f.get_by_text(a.text))
        show(loc, page)
        loc.click(timeout=15000)
        ready_ms, finished = settle(page, net, a.max_wait)
        check_allowed(page.url)
        print(f"Clicked '{a.text}'. Now at: {page.url}  ({page.title()})")
        print(f"Ready after {ready_ms} ms" + ("" if finished else "  (STILL LOADING)"))
        net_summary(net, page, a, "click-" + a.text)
        step_shot(page, a, "after-click-" + a.text)
    with_page(click)


def cmd_fill(a):
    def fill(page):
        check_allowed(page.url)
        net = Net(page)
        loc = find(page, lambda f: f.get_by_label(a.field))
        if loc.count() == 0:
            loc = find(page, lambda f: f.get_by_placeholder(a.field))
        type_into(page, loc, a.value)
        print(f"Filled '{a.field}'.")
        settle(page, net, min(a.max_wait, 5000))
        net_summary(net, page, a, "fill-" + a.field)
        step_shot(page, a, "after-fill-" + a.field)
    with_page(fill)


def cmd_login(a):
    rows = sites()
    site = next((s for s in rows if not a.site or s["name"] == a.site), None)
    if not site or len(site["settings"]) < 2:
        raise c.ConnectorError("No site with two login settings (user, password) in qa-tester/environments.md.",
                               "Add them to the row, for example `QA_POD_DEV_USER`, `QA_POD_DEV_PASSWORD`.")
    user, password = c.need(site["settings"][0], site["settings"][1])

    def login(page):
        check_allowed(page.url)
        if "login" not in page.url.lower():
            page.goto(site["url"].rstrip("/") + "/login.aspx", wait_until="load", timeout=60000)
        net = Net(page)
        page.wait_for_timeout(1500)
        frame = next((f for f in page.frames if f.locator("input[type=password]").count() > 0), None)
        if frame is None:
            print(f"Already logged in: {page.url}  ({page.title()}). Use the site's own sign-out to test a fresh login.")
            step_shot(page, a, "already-logged-in")
            return
        who = frame.locator("input[type=text], input[type=email]").first
        pw = frame.locator("input[type=password]").first
        type_into(page, who, user)
        type_into(page, pw, password)
        button = frame.get_by_role("button", name=re.compile(r"sign in|log in|login", re.I)).first
        show(button, page)
        button.click()
        for _ in range(60):   # wait up to 30 s for the site to finish "Processing request"
            page.wait_for_timeout(500)
            if page.locator("[role=alert]").count() > 0:
                break
            try:
                if not any(f.locator("input[type=password]").count() > 0 for f in page.frames):
                    break
                if frame.locator("input[type=password]").first.is_enabled():
                    page.wait_for_timeout(1000)   # the form came back: login was refused
                    break
            except Exception:
                break
        settle(page, net, 15000)
        check_allowed(page.url)
        still = any(f.locator("input[type=password]").count() > 0 for f in page.frames)
        print(f"After login: {page.url}  ({page.title()})")
        print("Login FAILED: the password box is still showing." if still else "Login OK.")
        net_summary(net, page, a, "login")
        step_shot(page, a, "after-login")
    with_page(login)


def cmd_watch(a):
    """Record what the page asks for while the user clicks around by hand: the 'network tab', as text."""
    def watch(page):
        net, console = Net(page), []
        page.on("console", lambda m: console.append(m.text[:200]) if m.type == "error" else None)
        print(f"Watching the network for {a.seconds} s. Use the browser window now...")
        page.wait_for_timeout(a.seconds * 1000)
        print(f"Page now: {page.url}  ({page.title()})")
        print(f"Console errors: {len(console)}")
        for m in console[:5]:
            print(f"  - {m}")
        net_summary(net, page, a, "watch")
    with_page(watch)


def cmd_cookies(a):
    """List the cookies and browser storage. Values are never printed: only names, flags, lifetime, and size."""
    def look(page):
        check_allowed(page.url)
        now = time.time()
        cookies = page.context.cookies()
        rows, findings = [], []
        for ck in cookies:
            exp = ck.get("expires", -1)
            secs = 0 if exp in (-1, None) else max(0, exp - now)
            life = "session" if exp in (-1, None) else (f"{int(secs / 86400)} d" if secs >= 86400 else f"{int(secs / 3600)} h")
            same = ck.get("sameSite", "None")
            rows.append({"name": ck["name"], "domain": ck["domain"], "path": ck["path"], "lifetime": life,
                         "httpOnly": "yes" if ck["httpOnly"] else "NO", "secure": "yes" if ck["secure"] else "NO",
                         "sameSite": same, "size": len(ck["value"])})
            if ck["domain"].lstrip(".") in {s["host"] for s in sites()} and re.search(r"auth|sess|token|sid|login", ck["name"], re.I):
                if not ck["httpOnly"]:
                    findings.append(f"'{ck['name']}' looks like a session/auth cookie but is readable by page scripts (no HttpOnly)")
                if not ck["secure"]:
                    findings.append(f"'{ck['name']}' looks like a session/auth cookie but is not marked Secure")
                if same == "None":
                    findings.append(f"'{ck['name']}' has SameSite=None (sent on cross-site requests)")
                if life.endswith(" d") and int(life.split()[0]) > 30:
                    findings.append(f"'{ck['name']}' lives {life}")
        cols = ["name", "domain", "path", "lifetime", "httpOnly", "secure", "sameSite", "size"]
        c.show_table([[r[k] for k in cols] for r in rows], cols, "cookies")
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
        for s in store:
            if s["looks_like_jwt"]:
                findings.append(f"{s['store']} key '{s['key']}' holds what looks like a token (readable by any script on the page)")
        print("\nThings worth a look:" if findings else "\nNothing suspicious by the simple checks.")
        for f in findings:
            print(f"  - {f}")
    with_page(look)


SKIP_URL = re.compile(r"log(out|off)|sign-?out|delete|remove|download|export|\.(pdf|csv|xlsx?|zip|docx?)(\?|$)|^javascript:|^mailto:", re.I)
PROBE_JS = """() => ({
  headings: [...document.querySelectorAll('h1,h2,h3')].slice(0, 5).map(h => h.innerText.trim()).filter(Boolean),
  forms: document.forms.length,
  inputs: [...document.querySelectorAll('input:not([type=hidden]),select,textarea')].slice(0, 10)
            .map(i => i.getAttribute('aria-label') || i.placeholder || i.name || i.id || i.type),
  buttons: [...document.querySelectorAll('button,input[type=submit],input[type=button]')].slice(0, 8)
            .map(b => (b.innerText || b.value || '').trim()).filter(Boolean),
  tables: [...document.querySelectorAll('table')].slice(0, 3)
            .map(t => [...t.querySelectorAll('th')].slice(0, 8).map(h => h.innerText.trim()).filter(Boolean)).filter(h => h.length),
  libs: [...document.scripts].map(s => s.src).filter(s => /fusioncharts|highcharts|jquery|angular|react|vue|bootstrap/i.test(s))
            .map(s => s.split('/').pop().split('?')[0]),
  highcharts: (typeof Highcharts !== 'undefined' && Highcharts.version) || null,
  fusioncharts: (typeof FusionCharts !== 'undefined' && FusionCharts.version && FusionCharts.version.join('.')) || null,
  charts: document.querySelectorAll('svg, canvas').length,
  textLength: document.body ? document.body.innerText.length : 0,
  links: [...document.querySelectorAll('a[href]')].map(a => ({h: a.href, t: (a.innerText || a.title || '').trim().slice(0, 60)}))
})"""


def cmd_crawl(a):
    """Visit pages by following links only (read-only). Wait for each page to really finish, then record it."""
    site = next((s for s in sites() if not a.site or s["name"] == a.site), None)
    if not site:
        raise c.ConnectorError("Site not found in qa-tester/environments.md.", "Use `status` to list the allowed sites.")
    run_name = a.run or "crawl-" + datetime.datetime.now().strftime("%Y%m%d-%H%M")
    folder = QA / "runs" / run_name / "tasks" / a.task if a.task else QA / "runs" / run_name
    (folder / "pages").mkdir(parents=True, exist_ok=True)
    results = []

    def crawl(page):
        net, console = Net(page), []
        page.on("console", lambda m: console.append(m.text[:160]) if m.type == "error" else None)
        scope = (urlsplit(a.scope or site["url"]).path.rstrip("/") or "") + "/"
        queue, seen = list(a.start or [page.url]), set()
        while queue and len(results) < a.max:
            url = queue.pop(0).split("#")[0]
            key = url.lower()
            if key in seen or SKIP_URL.search(url):
                continue
            seen.add(key)
            console.clear()
            net.reset()
            row = {"url": url, "title": "", "status": None, "error": ""}
            try:
                check_allowed(url)
                t0 = time.time()
                resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
                ready_ms, finished = settle(page, net, a.max_wait)
                row.update(status=resp.status if resp else None, title=page.title(), ready_ms=ready_ms, finished=finished)
                if re.search(r"login", page.url, re.I) and not re.search(r"login", url, re.I):
                    row["error"] = "sent back to login (session ended)"
                    results.append(row)
                    break
                info = page.evaluate(PROBE_JS)
                home = urlsplit(site["url"]).hostname
                reqs = net.current()
                row.update(info=info, console=list(console),
                           failed=[f"{r['method']} {r['status'] or r['failed']} {safe_url(r['url'], home)}" for r in reqs if r["failed"] or (r["status"] or 0) >= 400],
                           requests=len(reqs),
                           xhr=[f"{r['method']} {r['status']} {r['ms']}ms {safe_url(r['url'], home)}" for r in reqs if r["type"] in ("xhr", "fetch")])
                if info["textLength"] < 20:
                    row["error"] = "page looks blank"
                shot = folder / "pages" / f"{len(results) + 1:03d}-{re.sub(r'[^a-z0-9]+', '-', urlsplit(page.url).path.lower()).strip('-')[-40:]}.png"
                page.screenshot(path=str(shot))
                row["shot"] = shot.name
                for link in info["links"]:
                    h = link["h"].split("#")[0]
                    u = urlsplit(h)
                    if u.hostname == home and u.path.startswith(scope) and h.lower() not in seen \
                            and not SKIP_URL.search(h) and not RISKY.search(link["t"]) and (not a.match or re.search(a.match, h, re.I)):
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
    with_page(crawl)
    write_crawl_report(folder, run_name, site, results)


def write_crawl_report(folder, run_name, site, results):
    def problem(r):
        return r["error"] or r.get("console") or r.get("failed") or not r.get("finished", True)
    out = [f"# Crawl: {run_name}", "", f"Site: {site['name']} ({site['url']})", f"Date: {datetime.date.today().isoformat()}",
           f"Pages visited: {len(results)}. With a problem: {sum(1 for r in results if problem(r))}.", "",
           "| # | Page | Title | Status | Ready (s) | Requests | XHR | Console errors | Failed | Charts/libs | Screenshot |",
           "|---|------|-------|--------|-----------|----------|-----|----------------|--------|-------------|------------|"]
    for i, r in enumerate(results, 1):
        info = r.get("info", {})
        u = urlsplit(r["url"])
        libs = ", ".join(filter(None, [f"Highcharts {info['highcharts']}" if info.get("highcharts") else "",
                                       f"FusionCharts {info['fusioncharts']}" if info.get("fusioncharts") else "",
                                       *sorted(set(info.get("libs", [])))]))
        out.append(f"| {i} | {u.path.split('/')[-1]}{('?' + u.query) if u.query else ''} | {r['title'] or r['error']} | {r['status'] or ''} | "
                   f"{r.get('ready_ms', 0) / 1000:.1f}{'' if r.get('finished', True) else '+'} | {r.get('requests', '')} | {len(r.get('xhr', []))} | "
                   f"{len(r.get('console', []))} | {len(r.get('failed', []))} | {libs} | {r.get('shot', '')} |")
    out += ["", "## Problems", ""]
    for r in results:
        if problem(r):
            out.append(f"- {r['url']}")
            if r["error"]:
                out.append(f"  - error: {r['error']}")
            if not r.get("finished", True):
                out.append("  - still loading when the wait limit was reached")
            for m in r.get("console", [])[:3]:
                out.append(f"  - console: {m}")
            for m in r.get("failed", [])[:3]:
                out.append(f"  - request: {m}")
    out += ["", "## What each page has", ""]
    for r in results:
        if r["error"] and "info" not in r:
            continue
        info = r.get("info", {})
        out.append(f"### {r['title']}  ({urlsplit(r['url']).path.split('/')[-1]})")
        out.append(f"- Headings: {'; '.join(info.get('headings', [])) or '-'}")
        out.append(f"- Fields: {', '.join(info.get('inputs', [])) or '-'}")
        out.append(f"- Buttons: {', '.join(info.get('buttons', [])) or '-'}")
        for t in info.get("tables", []):
            out.append(f"- Table columns: {', '.join(t)}")
        for x in r.get("xhr", [])[:6]:
            out.append(f"- Data call: {x}")
        out.append("")
    text = redact("\n".join(out)) + "\n"
    (folder / "crawl-report.md").write_text(text, encoding="utf-8")
    sites_dir = QA / "sites"
    sites_dir.mkdir(exist_ok=True)
    (sites_dir / f"{site['name']}.md").write_text(text.replace(f"# Crawl: {run_name}", f"# Site map: {site['name']} (from crawl {run_name})"), encoding="utf-8")
    print(f"\nReport: {folder / 'crawl-report.md'}\nSite map: {sites_dir / (site['name'] + '.md')}")


def main():
    p = argparse.ArgumentParser(description="Visible browser for QA testing.")
    sub = p.add_subparsers(dest="cmd", required=True)
    step = argparse.ArgumentParser(add_help=False)
    step.add_argument("--run", help="save a screenshot and the network calls under qa-tester/runs/NAME/")
    step.add_argument("--task", help="put them in the subfolder tasks/TASK/ of the run (one folder per task)")
    step.add_argument("--all-net", action="store_true", help="also show images, styles and fonts")
    step.add_argument("--max-wait", type=int, default=20000, help="ms to wait for a slow page to finish (default 20000)")
    s = sub.add_parser("start"); s.add_argument("url", nargs="?"); s.set_defaults(fn=cmd_start)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("stop").set_defaults(fn=cmd_stop)
    g = sub.add_parser("goto", parents=[step]); g.add_argument("url"); g.set_defaults(fn=cmd_goto)
    sub.add_parser("snapshot").set_defaults(fn=cmd_snapshot)
    sh = sub.add_parser("screenshot"); sh.add_argument("--run"); sh.add_argument("--task"); sh.add_argument("--name"); sh.add_argument("--full", action="store_true"); sh.set_defaults(fn=cmd_screenshot)
    k = sub.add_parser("click", parents=[step]); k.add_argument("text"); k.add_argument("--role"); k.add_argument("--write", action="store_true"); k.set_defaults(fn=cmd_click)
    f = sub.add_parser("fill", parents=[step]); f.add_argument("field"); f.add_argument("value"); f.set_defaults(fn=cmd_fill)
    lg = sub.add_parser("login", parents=[step]); lg.add_argument("--site"); lg.set_defaults(fn=cmd_login)
    w = sub.add_parser("watch", parents=[step]); w.add_argument("--seconds", type=int, default=30); w.set_defaults(fn=cmd_watch)
    sub.add_parser("cookies").set_defaults(fn=cmd_cookies)
    cr = sub.add_parser("crawl", help="follow links read-only and record every page")
    cr.add_argument("--site"); cr.add_argument("--run"); cr.add_argument("--task"); cr.add_argument("--scope", help="only follow links under this address")
    cr.add_argument("--start", action="append", help="page to start from; repeat to give several")
    cr.add_argument("--match", help="only follow links whose address matches this pattern (regular expression)")
    cr.add_argument("--max", type=int, default=30); cr.add_argument("--max-wait", type=int, default=25000)
    cr.add_argument("--pause", type=int, default=800, help="ms to pause between pages so the user can follow")
    cr.set_defaults(fn=cmd_crawl)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    c.run(lambda: main())
