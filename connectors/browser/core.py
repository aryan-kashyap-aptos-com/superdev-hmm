"""Shared browser plumbing for the browser connector.

Used by run.py (the commands), panel.py (the runner sidebar) and player.py (the scenario runner).
Holds: the list of allowed sites, starting and attaching to Chrome, finding elements (also inside frames),
reading an element's state (visible, hidden, disabled, covered...), waiting until a page has really finished,
recording network calls, scrolling, and screenshots that include the whole page.
"""
import contextlib
import datetime
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)

QA = HERE.parent.parent / "qa-tester"
PROFILE = QA / ".browser-profile"
PORT = int(os.environ.get("QA_BROWSER_PORT", "9333"))
CDP = f"http://127.0.0.1:{PORT}"
PANEL_MARK = "#qa-runner"
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


# ---------------------------------------------------------------- the test run in use, and its Login section

LOGIN_FIELDS = {"site address": "site", "sign-in page": "signin", "username": "user", "password": "password"}


def active_run():
    """The test run in use: the one given with --run (QA_RUN), else the one named in qa-tester/runs/ACTIVE.
    Only a run folder that has a plan.md counts. None when there is no such run."""
    names = [os.environ.get("QA_RUN", "")]
    pointer = QA / "runs" / "ACTIVE"
    if pointer.exists():
        names.append(pointer.read_text(encoding="utf-8").strip())
    return next((n for n in names if n and (QA / "runs" / n / "plan.md").exists()), None)


def run_login(run=None):
    """The Login section of the run's plan.md: site, signin, user, password. Placeholders and "none" count as empty.
    The password is registered so redact() hides it in every output."""
    run = run or active_run()
    if not run:
        return {}
    text = (QA / "runs" / run / "plan.md").read_text(encoding="utf-8")
    m = re.search(r"^##\s+Login\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    info = {"run": run}
    for line in (m.group(1).splitlines() if m else []):
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() in LOGIN_FIELDS:
            value = "|".join(cells[1:]).strip().strip("`").strip()   # a password may itself contain "|"
            if value and not re.fullmatch(r"<.*>", value) and value.lower() not in ("none", "-", "n/a", "same as site"):
                info[LOGIN_FIELDS[cells[0].lower()]] = value
    if info.get("password"):
        os.environ["QA_RUN_PASSWORD"] = info["password"]
    return info


def _as_url(address):
    """A bare address becomes https://; a full address is kept as given."""
    return address if re.match(r"https?://", address or "") else (f"https://{address}" if address else "")


def run_site(info=None):
    """The site named in the run's plan, as a site row. None if the plan names no site."""
    info = run_login() if info is None else info
    url = _as_url(info.get("site"))
    if not url:
        return None
    return {"name": f"run {info['run']}", "url": url, "host": urlsplit(url).hostname, "settings": [],
            "login": info.get("signin", ""), "from_run": True}


# ---------------------------------------------------------------- allowed sites

def sites():
    """Allowed sites: the one in the active run's plan.md, plus any rows in qa-tester/environments.md and the
    private environments.local.md (optional, for sites used again and again)."""
    paths = [p for p in (QA / "environments.md", QA / "environments.local.md") if p.exists()]
    from_run = run_site()
    rows = [from_run] if from_run else []
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and re.match(r"https?://", cells[1]):
                notes = cells[4] if len(cells) > 4 else ""
                login_page = re.search(r"login:\s*`?([^\s`;,]+)", notes, re.I)
                rows.append({"name": cells[0], "url": cells[1], "host": urlsplit(cells[1]).hostname,
                             "settings": re.findall(r"`([A-Z0-9_]+)`", cells[3]),
                             "login": login_page.group(1) if login_page else ""})
    if not rows:
        raise c.ConnectorError("No site to test.", "Fill in \"Site address\" in the Login section of the active "
                               "run's plan.md (python qa-tester/test-run.py new \"<topic>\" --site <address>), "
                               "or add a row to qa-tester/environments.local.md.")
    return rows


def site(name=None):
    """A site by name; without a name, the active run's site (or else the first listed one)."""
    rows = sites()
    found = next((s for s in rows if not name or s["name"] == name), None)
    if not found:
        raise c.ConnectorError(f"Site '{name or '(first)'}' was not found.",
                               "Run `python connectors/browser/run.py status` to see the active run and the allowed sites.")
    return found


def allowed_hosts():
    hosts = set()
    for s in sites():
        hosts.add(s["host"])
        if re.match(r"https?://", s.get("login") or ""):
            hosts.add(urlsplit(s["login"]).hostname)
    return hosts


def check_allowed(url):
    host = urlsplit(url).hostname
    if host not in allowed_hosts():
        raise c.ConnectorError(f"'{host}' is not an allowed site.",
                               "Only the site in the active run's plan.md (Login section) and sites in "
                               "qa-tester/environments(.local).md can be opened. Ask the user before adding one.")


def absolute(url, home):
    """A full address, or a path resolved against the site's address (so scenario files hold no host names)."""
    return url if re.match(r"https?://", url) else urljoin(home["url"], url)


# ---------------------------------------------------------------- the Chrome process

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


def launch(url, devtools=False):
    """Start a visible Chrome with its own profile. It stays open after this program ends."""
    PROFILE.mkdir(parents=True, exist_ok=True)
    cmd = [find_chrome(), f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}", "--no-first-run",
           "--no-default-browser-check", "--new-window", "--window-size=1500,1000", "--window-position=420,0"]
    if devtools:
        cmd.append("--auto-open-devtools-for-tabs")
    cmd.append(url)
    flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0   # detached, own process group
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
    for _ in range(40):
        if alive():
            return
        time.sleep(0.5)
    raise c.ConnectorError("The browser did not start.", f"Check that port {PORT} is free, or set QA_BROWSER_PORT in .env.")


def is_panel(pg):
    return pg.url.endswith(PANEL_MARK)


def app_page(context):
    """The page under test: the newest tab that is not DevTools and not the runner panel."""
    pages = [pg for pg in context.pages if not pg.url.startswith("devtools://") and not is_panel(pg)]
    return pages[-1] if pages else context.new_page()


@contextlib.contextmanager
def session():
    """Attach to the open browser. Yields (browser, page). Chrome stays open afterwards."""
    if not alive():
        raise c.ConnectorError("No browser is open.", "Run: python connectors/browser/run.py start")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise c.ConnectorError("The playwright package is not installed.", "Run: pip install -r requirements.txt") from None
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        page = app_page(browser.contexts[0])
        page.bring_to_front()
        page.on("dialog", lambda d: d.dismiss())
        yield browser, page


def with_page(fn):
    with session() as (_, page):
        return fn(page)


# ---------------------------------------------------------------- finding elements

ENGINE = re.compile(r"^(css|text|role|xpath|id|data-testid|internal:[a-z-]+)=", re.I)
CUSTOM = re.compile(r"^(label|placeholder|testid|alt|title)=(.+)$", re.S)
CSS_LIKE = re.compile(r"^([#.\[]|//|[a-z][a-z0-9-]*[#.\[:>])")


def _makers(target):
    """Ways to find `target`, best first. See GUIDE.md, "How to name an element"."""
    m = CUSTOM.match(target)
    if m:
        kind, val = m.group(1), m.group(2).strip().strip('"')
        return [lambda f: {"label": f.get_by_label, "placeholder": f.get_by_placeholder, "testid": f.get_by_test_id,
                           "alt": f.get_by_alt_text, "title": f.get_by_title}[kind](val)]
    if ENGINE.match(target) or CSS_LIKE.match(target):
        return [lambda f: f.locator(target)]
    return [lambda f: f.get_by_role("button", name=target), lambda f: f.get_by_role("link", name=target),
            lambda f: f.get_by_label(target), lambda f: f.get_by_placeholder(target), lambda f: f.get_by_text(target)]


def locate(page, target):
    """All matches of `target`, searching the page and every frame inside it. May match nothing (count 0)."""
    makers = _makers(target)
    for make in makers:
        for frame in page.frames:
            try:
                loc = make(frame)
                if loc.count():
                    return loc
            except Exception:
                continue
    return makers[0](page.main_frame)


def find(page, make):
    """First match of make(frame) in the page or any frame inside it."""
    for frame in page.frames:
        loc = make(frame)
        if loc.count() > 0:
            return loc.first
    return make(page.main_frame).first


STATE_JS = r"""el => {
  const cs = getComputedStyle(el), r = el.getBoundingClientRect();
  let hiddenWhy = '';
  if (cs.display === 'none') hiddenWhy = 'display: none';
  else if (cs.visibility === 'hidden' || cs.visibility === 'collapse') hiddenWhy = 'visibility: hidden';
  else if (parseFloat(cs.opacity) === 0) hiddenWhy = 'opacity: 0';
  else if (r.width === 0 || r.height === 0) hiddenWhy = 'zero size (or a parent is hidden)';
  const inView = r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;
  let covered = '';
  if (!hiddenWhy && inView) {
    const x = Math.min(Math.max(r.left + r.width / 2, 0), innerWidth - 1), y = Math.min(Math.max(r.top + r.height / 2, 0), innerHeight - 1);
    const top = document.elementFromPoint(x, y);
    if (top && top !== el && !el.contains(top) && !top.contains(el) && top.id !== '__qa_cursor')
      covered = top.tagName.toLowerCase() + (top.id ? '#' + top.id : '') +
                (typeof top.className === 'string' && top.className.trim() ? '.' + top.className.trim().split(/\s+/)[0] : '');
  }
  return {tag: el.tagName.toLowerCase(), type: (el.getAttribute('type') || '').toLowerCase(), hiddenWhy, inView, covered,
          disabledAttr: !!el.disabled, ariaDisabled: !!el.closest('[aria-disabled="true"]'),
          fieldsetDisabled: !!el.closest('fieldset[disabled]'), readonly: !!el.readOnly, required: !!el.required,
          ariaHidden: !!el.closest('[aria-hidden="true"]'),
          text: (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 120)};
}"""


def element_state(loc):
    """Everything a tester asks about one element: exists, visible or hidden (and why), enabled or disabled,
    checked, editable, in view, covered by something else, clickable, its text and value."""
    n = loc.count()
    if n == 0:
        return {"exists": False, "count": 0}
    el = loc.first
    info = el.evaluate(STATE_JS)
    s = {"exists": True, "count": n, "visible": el.is_visible(), "enabled": el.is_enabled(), **info}
    for key, fn in (("checked", el.is_checked), ("editable", el.is_editable)):
        try:
            s[key] = fn()
        except Exception:
            s[key] = None
    if info["tag"] in ("input", "textarea", "select"):
        try:
            v = el.input_value()
            s["value"] = "***" if info["type"] == "password" else v[:120]
        except Exception:
            pass
    s["clickable"] = bool(s["visible"] and s["enabled"] and not info["covered"])
    return s


def describe_state(s):
    """One plain line, for example: 'visible, disabled (aria-disabled), in view'."""
    if not s.get("exists"):
        return "not on the page"
    parts = ["visible" if s["visible"] else f"hidden ({s.get('hiddenWhy') or 'not rendered'})"]
    if s["enabled"]:
        parts.append("enabled")
    else:
        why = "disabled attribute" if s.get("disabledAttr") else "aria-disabled" if s.get("ariaDisabled") else \
              "inside a disabled fieldset" if s.get("fieldsetDisabled") else "disabled"
        parts.append(f"disabled ({why})")
    if s.get("checked") is not None:
        parts.append("checked" if s["checked"] else "not checked")
    if s.get("readonly"):
        parts.append("read-only")
    if s["visible"]:
        parts.append("in view" if s.get("inView") else "out of view (scroll needed)")
    if s.get("covered"):
        parts.append(f"covered by {s['covered']}")
    if s["count"] > 1:
        parts.append(f"{s['count']} matches, first one used")
    return ", ".join(parts)


ELEMENTS_JS = r"""() => {
  const sel = 'a[href],button,input,select,textarea,summary,[role=button],[role=link],[role=checkbox],[role=radio],[role=tab],[role=menuitem],[role=switch],[role=combobox],[onclick]';
  const out = [];
  for (const el of document.querySelectorAll(sel)) {
    if (el.type === 'hidden') continue;
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    const visible = cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) !== 0 && r.width > 0 && r.height > 0;
    const disabled = !!el.disabled || !!el.closest('[aria-disabled="true"]') || !!el.closest('fieldset[disabled]');
    const tag = el.tagName.toLowerCase(), type = (el.type || '').toLowerCase();
    const own = el.getAttribute('aria-label') || (el.labels && el.labels[0] && el.labels[0].innerText) || '';
    let label;
    if (tag === 'select') {
      const opt = el.selectedOptions && el.selectedOptions[0];
      label = (own ? own + ': ' : '') + (opt ? opt.text : '') + ` (${el.options.length} options)`;
    } else if (type === 'image') label = own || el.alt || el.title || el.value || el.name || '';
    else label = own || el.innerText || el.value || el.placeholder || el.title || el.alt || el.name || el.id || '';
    const role = el.getAttribute('role') || ({a: 'link', button: 'button', select: 'dropdown', textarea: 'textbox', summary: 'button'}[tag] ||
                 (tag === 'input' ? ({checkbox: 'checkbox', radio: 'radio', submit: 'button', button: 'button', image: 'button', reset: 'button',
                                      file: 'file picker', range: 'slider', date: 'date', number: 'number'}[type] || 'textbox') : tag));
    out.push({role, name: label.trim().replace(/\s+/g, ' ').slice(0, 60), visible, disabled,
              checked: (el.type === 'checkbox' || el.type === 'radio') ? el.checked : null,
              inView: r.bottom > 0 && r.top < innerHeight, password: el.type === 'password'});
  }
  return out;
}"""


def list_elements(page):
    rows = []
    for i, frame in enumerate(page.frames):
        try:
            for e in frame.evaluate(ELEMENTS_JS):
                e["frame"] = i
                rows.append(e)
        except Exception:
            continue
    return rows


# ---------------------------------------------------------------- watching it live

CURSOR_JS = """() => {
  if (document.getElementById('__qa_cursor')) return;
  const d = document.createElement('div');
  d.id = '__qa_cursor';
  d.style.cssText = 'position:fixed;z-index:2147483647;width:20px;height:20px;border-radius:50%;background:rgba(255,0,0,.55);' +
    'border:2px solid #fff;box-shadow:0 0 6px rgba(0,0,0,.6);pointer-events:none;left:20px;top:20px;transform:translate(-50%,-50%)';
  document.documentElement.appendChild(d);
  document.addEventListener('mousemove', e => { d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
}"""


HIGHLIGHT_JS = """el => {
  const r = el.getBoundingClientRect(), d = document.createElement('div');
  d.className = '__qa_hl';
  d.style.cssText = `position:fixed;z-index:2147483646;pointer-events:none;left:${r.left - 4}px;top:${r.top - 4}px;` +
    `width:${r.width + 8}px;height:${r.height + 8}px;border:3px solid #ff2d95;border-radius:4px;` +
    'box-shadow:0 0 0 4000px rgba(0,0,0,.08);transition:opacity .4s';
  document.documentElement.appendChild(d);
  setTimeout(() => { d.style.opacity = '0'; setTimeout(() => d.remove(), 450); }, 1300);
}"""
OVERLAYS_JS = """hide => {
  for (const el of document.querySelectorAll('.__qa_hl')) el.remove();
  const d = document.getElementById('__qa_cursor'); if (d) d.style.display = hide ? 'none' : '';
}"""


def show(locator, page=None):
    """Make a step watchable: scroll to the target, glide a red dot to it, and outline it for a moment."""
    try:
        if page is not None:
            page.evaluate(CURSOR_JS)
            locator.scroll_into_view_if_needed(timeout=5000)
            box = locator.bounding_box()
            if box:
                page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=35)
        locator.evaluate(HIGHLIGHT_JS)
    except Exception:
        pass
    time.sleep(0.5)


def overlays(page, hide):
    """Remove the outline boxes and hide (or bring back) the red dot, in the page and its frames."""
    for frame in page.frames:
        try:
            frame.evaluate(OVERLAYS_JS, hide)
        except Exception:
            pass


def type_into(page, locator, value):
    """Click the field, clear it, and type one character at a time so the user sees it happen.
    Then make sure the field holds exactly that value (pages that re-render while you type can drop characters).
    Returns True when the field holds the value."""
    show(locator, page)
    locator.click()
    locator.fill("")
    locator.press_sequentially(value, delay=TYPE_DELAY_MS)
    time.sleep(0.3)
    try:
        if locator.input_value() != value:
            locator.fill(value)
            time.sleep(0.2)
        return locator.input_value() == value
    except Exception:
        return True   # not a form field (for example a contenteditable area): nothing to compare


def redact(text):
    """Hide secrets: the run's password and the value of any setting whose name ends in PASSWORD, TOKEN, SECRET
    or KEY are never printed."""
    if "QA_RUN_PASSWORD" not in os.environ:
        try:
            run_login()
        except Exception:
            pass
    for key, value in os.environ.items():
        if value and len(value) >= 4 and re.search(r"(PASSWORD|TOKEN|SECRET|_KEY)$", key):
            text = text.replace(value, "***")
    return text


# ---------------------------------------------------------------- network: what the page asked for

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

    def since(self, index):
        return self.rows[index:]


def is_bad(r):
    return bool(r["failed"]) or (r["status"] or 0) >= 400


def safe_url(url, home_host):
    """Path plus the names of the query parameters, never their values (they can hold tokens)."""
    u = urlsplit(url)
    keys = ",".join(k for k, _ in parse_qsl(u.query, keep_blank_values=True))
    where = u.path if u.hostname == home_host else f"{u.hostname}{u.path}"
    return where + (f"?{{{keys}}}" if keys else "")


def net_rows_for_panel(rows, home_host):
    return [{"m": r["method"], "s": r["status"] or (0 if r["failed"] else None), "t": r["type"], "ms": r["ms"],
             "u": safe_url(r["url"], home_host), "f": r["failed"]} for r in rows]


def net_summary(net, page, a, label):
    """Print the calls of the current step; with --run, also save them as JSON next to the screenshots."""
    home = urlsplit(page.url).hostname
    rows = net.current()
    interesting = ("document", "xhr", "fetch", "websocket", "eventsource", "other")
    shown = [r for r in rows if getattr(a, "all_net", False) or r["type"] in interesting]
    bad = [r for r in rows if is_bad(r)]
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
    """Wait until the page has really finished: no request in flight, no spinner, and the page stops changing.
    Returns (milliseconds waited, finished?)."""
    t0, last, stable_since = time.time(), None, time.time()
    while (time.time() - t0) * 1000 < max_ms:
        page.wait_for_timeout(300)
        try:
            sig = page.evaluate("() => [document.body ? document.body.innerText.length : 0, document.querySelectorAll('svg,canvas,img,tr').length]")
            busy = page.locator(BUSY).count()
        except Exception:
            continue
        if (net and net.inflight()) or busy or sig != last:
            last, stable_since = sig, time.time()
            continue
        if (time.time() - stable_since) * 1000 >= quiet_ms:
            return int((time.time() - t0) * 1000), True
    return int((time.time() - t0) * 1000), False


# ---------------------------------------------------------------- scrolling

SCROLL_JS = r"""([where, px, smooth]) => {
  const doc = document.scrollingElement || document.documentElement;
  let el = doc;
  if (doc.scrollHeight <= innerHeight + 20) {          // the page itself does not scroll: use the biggest inner scroller
    let best = null, area = 0;
    for (const x of document.querySelectorAll('body *')) {
      const oy = getComputedStyle(x).overflowY;
      if (!/(auto|scroll)/.test(oy) || x.scrollHeight <= x.clientHeight + 20) continue;
      const a = x.clientWidth * x.clientHeight;
      if (a > area) { best = x; area = a; }
    }
    if (best) el = best;
  }
  const view = el === doc ? innerHeight : el.clientHeight;
  const max = Math.max(0, el.scrollHeight - view);
  const step = px || Math.round(view * 0.8);
  let to = el.scrollTop;
  if (where === 'top') to = 0; else if (where === 'bottom') to = max;
  else if (where === 'down') to = Math.min(max, el.scrollTop + step); else if (where === 'up') to = Math.max(0, el.scrollTop - step);
  el.scrollTo({top: to, behavior: smooth ? 'smooth' : 'instant'});
  return {from: Math.round(el.scrollTop), to: Math.round(to), max: Math.round(max), view: Math.round(view), inner: el !== doc};
}"""


def scroll(page, where="down", pixels=None, smooth=True):
    """Scroll the page (or its main inner scroll area). Returns where it ended and how far it can go."""
    info = page.evaluate(SCROLL_JS, [where, pixels, smooth])
    page.wait_for_timeout(700 if smooth else 150)
    return info


def scroll_through(page, net=None, max_steps=30):
    """Scroll to the bottom in steps (so content that loads on scroll appears), then back to the top."""
    steps = 0
    while steps < max_steps:
        info = scroll(page, "down", smooth=False)
        page.wait_for_timeout(250)
        if net is not None and net.inflight():
            settle(page, net, 5000, 600)
        steps += 1
        if info["to"] >= info["max"]:
            break
    scroll(page, "top", smooth=False)
    return steps


def capture(page, path, full=True, net=None):
    """Save a screenshot. full=True scrolls through the page first and captures all of it.
    If only an inner area scrolls, saves one picture per screen of that area (name-part1.png, ...). Returns the paths."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    overlays(page, True)
    try:
        if not full:
            page.screenshot(path=str(path))
            return [path]
        probe = page.evaluate(SCROLL_JS, ["top", None, False])
        if not probe["inner"]:
            scroll_through(page, net)
            page.screenshot(path=str(path), full_page=True)
            return [path]
        parts, paths = min(10, max(1, math.ceil((probe["max"] + probe["view"]) / probe["view"]))), []
        for i in range(parts):
            p = path.with_name(f"{path.stem}-part{i + 1}{path.suffix}")
            page.wait_for_timeout(300)
            page.screenshot(path=str(p))
            paths.append(p)
            scroll(page, "down", smooth=False)
        scroll(page, "top", smooth=False)
        return paths
    finally:
        overlays(page, False)


# ---------------------------------------------------------------- run folders

def task_folder(run, task, kind):
    """qa-tester/runs/<run>/tasks/<task>/<kind>, or qa-tester/runs/<run>/<kind> when no task is given."""
    base = QA / "runs" / run
    return (base / "tasks" / task / kind) if task else (base / kind)


def next_step_file(run, label, ext, task=None):
    folder = task_folder(run, task, "network" if ext == "json" else "screenshots")
    folder.mkdir(parents=True, exist_ok=True)
    n = len(list(folder.glob(f"*.{ext}"))) + 1
    return folder / f"{n:02d}-{re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')[:40]}.{ext}"


def step_shot(page, a, label, net=None):
    """With --run: save a numbered screenshot of the whole page (or only the visible part with --viewport)."""
    if getattr(a, "run", None):
        paths = capture(page, next_step_file(a.run, label, "png", getattr(a, "task", None)),
                        full=not getattr(a, "viewport", False), net=net)
        for p in paths:
            print(f"Screenshot: {p}")


def stamp():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


# ---------------------------------------------------------------- logging in

def credentials(home):
    """Username and password for `home`: from the Login section of the active run's plan.md, when that run's site
    is this same site; else from two settings named in the site's environments row (older, reusable sites).
    Raises a clear error when neither is filled in."""
    info = run_login()
    run_url = _as_url(info.get("site"))
    same_site = home.get("from_run") or (run_url and urlsplit(run_url).hostname == home["host"])
    if same_site and info.get("user") and info.get("password"):
        return info["user"], info["password"]
    if len(home.get("settings", [])) >= 2 and all(os.environ.get(k) for k in home["settings"][:2]):
        return os.environ[home["settings"][0]], os.environ[home["settings"][1]]
    where = f"qa-tester/runs/{info['run']}/plan.md" if info.get("run") else "a run's plan.md (create one: qa-tester/test-run.py new \"<topic>\" --site " + home["url"] + ")"
    raise c.ConnectorError(f"No username and password for {home['name']}.",
                           f"Ask the user to fill Username and Password in the Login section of {where}.")


def login(page, home, net):
    """Sign in with the run's login. Returns (result word, message). Never prints the password."""
    user, password = credentials(home)

    def form():
        return next((f for f in page.frames if f.locator("input[type=password]").count() > 0), None)

    frame = form()
    if frame is None:
        start = absolute(home["login"], home) if home.get("login") else home["url"]
        resp = page.goto(start, wait_until="domcontentloaded", timeout=60000)
        settle(page, net, 15000)
        frame = form()
        if frame is None:
            where = safe_url(page.url, urlsplit(page.url).hostname)
            if resp and resp.status >= 400:
                return "Could not verify", (f"No sign-in form: {where} answered HTTP {resp.status}. "
                                            "Name the sign-in page in the site's Notes column, for example: login: login.aspx")
            if home.get("login") and "login" in page.url.lower():
                return "Could not verify", f"The sign-in page {where} has no password box."
            return "Verified", f"Already signed in (the sign-in page sent us to {where})."
    settle(page, net, 10000)   # let the sign-in form finish drawing before typing
    who = frame.locator("input[type=email]:visible, input[type=text]:visible, input:not([type]):visible").first
    if not type_into(page, who, user):
        return "Could not verify", "The username box did not keep the full value, so Sign in was not pressed (protects the account)."
    if not type_into(page, frame.locator("input[type=password]:visible").first, password):
        return "Could not verify", "The password box did not keep the full value, so Sign in was not pressed (protects the account)."
    button = frame.get_by_role("button", name=re.compile(r"sign in|log ?in|continue|submit", re.I)).first
    show(button, page)
    button.click()
    for _ in range(60):   # wait up to 30 s for "Processing request" to finish
        page.wait_for_timeout(500)
        try:
            if page.locator("[role=alert]").count() > 0 or form() is None:
                break
            if frame.locator("input[type=password]").first.is_enabled():
                page.wait_for_timeout(1000)   # the form came back: sign-in was refused
                break
        except Exception:
            break
    settle(page, net, 15000)
    check_allowed(page.url)
    if form() is not None:
        alert = ""
        try:
            alert = page.locator("[role=alert]").first.inner_text(timeout=1000).strip()
        except Exception:
            for f in page.frames:
                try:
                    if f.locator("[role=alert]").count():
                        alert = f.locator("[role=alert]").first.inner_text(timeout=1000).strip()
                        break
                except Exception:
                    continue
        return "Issue found", "Sign-in refused" + (f": {alert}" if alert else " (the password box is still showing).")
    return "Verified", f"Signed in. Now on: {page.title()}"
