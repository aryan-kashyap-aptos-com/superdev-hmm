"""A tiny background helper so the runner panel's own buttons work live, with no CLI command needed:
Desktop/iPhone/Android/Tablet, "Report", and "Re-run". `start` launches it; `stop` ends it. It does
nothing else: every real test command still connects and disconnects on its own, exactly as before.

It keeps one CDP connection open for as long as Chrome is open (a device resize needs that: see core.mobile)
and just polls the page for `window.__qa_pending_device`, `window.__qa_report_requested`, and
`window.__qa_rerun_requested`, which a click in the panel sets. Polling plain variables works from many
short-lived connections at once; a CDP-exposed function bound by one connection was tried first and turned
out not to reliably call back across separate connect_over_cdp() sessions.
"""
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

sys.dont_write_bytecode = True  # see the same line in run.py: avoids stale-pyc risk in a cloud-synced folder

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402
import panel as panel_mod  # noqa: E402
import report as report_mod  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

POLL_JS = """() => {
  const d = window.__qa_pending_device; window.__qa_pending_device = undefined;
  const r = !!window.__qa_report_requested; window.__qa_report_requested = false;
  const rr = !!window.__qa_rerun_requested; window.__qa_rerun_requested = false;
  return {device: d || null, report: r, rerun: rr};
}"""

RUN_SCRIPT = core.HERE / "run.py"


def handle_device(browser, page, cdp, panel, spec):
    try:
        d = core.mobile(browser, page, spec, cdp=cdp)
        panel.collapse(d is not None)
        panel.device(spec if d else "desktop")
        panel.log("Verified", f"mobile {spec}" if d else "mobile off",
                  f"{d['width']}x{d['height']}" if d else "back to desktop size")
    except Exception as e:
        try:
            panel.log("Issue found", f"mobile {spec}", str(e))
        except Exception:
            pass


def handle_rerun(panel):
    argv = core.load_last_play()
    if not argv:
        panel.log("Issue found", "re-run", "Nothing has been run yet in this browser session.")
        return
    argv = [a for a in argv if a != "--write"]   # a panel click is not the user's explicit --write approval
    try:
        flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0
        subprocess.Popen([sys.executable, str(RUN_SCRIPT), *argv],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
        panel.log("Verified", "re-run", "Started: play " + " ".join(argv[1:]))
    except Exception as e:
        panel.log("Issue found", "re-run", str(e))


def handle_report(panel):
    run = core.last_touched_run() or core.active_run()
    if not run:
        panel.log("Issue found", "view report", "No active run - nothing recorded to report yet.")
        return
    try:
        path, events, _, build_id, _ = report_mod.build(run)
        webbrowser.open(path.resolve().as_uri())
        panel.log("Verified", "view report", f"build {build_id}, {len(events)} recorded event(s): {path}")
    except Exception as e:
        panel.log("Issue found", "view report", str(e))


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
                flags = page.evaluate(POLL_JS)
            except Exception:
                continue
            panel = panel_mod.Panel.existing(page)
            if flags.get("device"):
                handle_device(browser, page, cdp, panel, flags["device"])
            if flags.get("report"):
                handle_report(panel)
            if flags.get("rerun"):
                handle_rerun(panel)


if __name__ == "__main__":
    main()
