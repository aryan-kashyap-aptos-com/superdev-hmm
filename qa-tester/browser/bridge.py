"""A tiny background helper so the runner panel's own device buttons (Desktop/iPhone/Android/Tablet) work
live, with no CLI command needed. `start` launches it; `stop` ends it. It does nothing else: every real
test command still connects and disconnects on its own, exactly as before.

It keeps one CDP connection open for as long as Chrome is open (a device resize needs that: see core.mobile)
and just polls the page for `window.__qa_pending_device`, which a click in the panel sets. Polling a plain
variable works from many short-lived connections at once; a CDP-exposed function bound by one connection was
tried first and turned out not to reliably call back across separate connect_over_cdp() sessions.
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402
import panel as panel_mod  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

POLL_JS = """() => { const v = window.__qa_pending_device; window.__qa_pending_device = undefined; return v || null; }"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(core.CDP)
        context = browser.contexts[0]
        current_page, cdp = None, None
        while core.alive():
            time.sleep(0.4)
            try:
                page = core.app_page(context)
                if page != current_page:
                    current_page, cdp = page, page.context.new_cdp_session(page)
                spec = page.evaluate(POLL_JS)
            except Exception:
                continue
            if not spec:
                continue
            try:
                d = core.mobile(browser, page, spec, cdp=cdp)
                panel = panel_mod.Panel.existing(page)
                panel.collapse(d is not None)
                panel.device(spec if d else "desktop")
                panel.log("Verified", f"mobile {spec}" if d else "mobile off",
                          f"{d['width']}x{d['height']}" if d else "back to desktop size")
            except Exception as e:
                try:
                    panel_mod.Panel.existing(page).log("Issue found", f"mobile {spec}", str(e))
                except Exception:
                    pass


if __name__ == "__main__":
    main()
