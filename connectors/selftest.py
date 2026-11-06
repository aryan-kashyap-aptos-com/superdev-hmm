"""Self-test for super-dev. No network, no credentials: pure checks plus a local mock server.

    python connectors/selftest.py

Exit code 0 means every check passed.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import common as c  # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else f"\n     {detail}"))
    if not ok:
        failures.append(label)


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / name / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def raises(fn, *a):
    try:
        fn(*a)
        return False
    except c.ConnectorError:
        return True


# ---------------------------------------------------------------- pure checks

def test_common():
    with tempfile.TemporaryDirectory() as d:
        Path(d, ".env").write_text('ST_A=hello   # note\nexport ST_B="x # y"\nST_C=p#ss\nST_D=file\n', encoding="utf-8")
        os.environ["ST_D"] = "env"
        c.load_env(d)
        check(".env: inline comment removed", os.environ["ST_A"] == "hello")
        check(".env: quoted value keeps #", os.environ["ST_B"] == "x # y")
        check(".env: # without space kept", os.environ["ST_C"] == "p#ss")
        check(".env: real environment wins", os.environ["ST_D"] == "env")

    check("clean() strips invisible characters", c.clean("a\u200bb\x07c") == "abc")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        c.show_table([[i, "x"] for i in range(120)], ["n", "v"], "selftest", limit=50)
    out = buf.getvalue()
    saved = [line for line in out.splitlines() if "saved to" in line]
    path = Path(saved[0].split("saved to ")[1].rstrip(")")) if saved else None
    check("big table: 50 rows shown, all 120 saved", "showing 50 of 120" in out and path and
          len(path.read_text(encoding="utf-8").splitlines()) == 121)
    if path:
        path.unlink()

    reads = ["select * from t where a = 1", "SELECT replace(name,'a','b') FROM t", "with x as (select 1) select * from x",
             "show tables", "explain select 1", "-- note\nselect 1;", "select 'drop table x' as s", "select update_time from t"]
    writes = ["update t set a=1", "delete from t", "select 1; drop table t", "insert into t values (1)",
              "with x as (select 1) delete from t", "select * into new_t from t", "exec sp_who", "call proc()",
              "select * from t for update", "truncate t", "/* x */ drop table t", "select * from t into outfile '/tmp/x'"]
    for sql in reads:
        check(f"sql read allowed: {sql!r}", not raises(c.check_read_only_sql, sql))
    for sql in writes:
        check(f"sql write blocked: {sql!r}", raises(c.check_read_only_sql, sql))

    text = c.html_to_text('<h1>Refunds</h1><p>One &amp; two.</p><ul><li>A</li></ul><table><tr><td>x</td></tr></table>'
                          '<ac:plain-text-body><![CDATA[select 1;]]></ac:plain-text-body>')
    check("html_to_text: heading, entity, list, table, code",
          all(s in text for s in ["# Refunds", "One & two.", "- A", "| x", "select 1;"]))

    md = "# Title\n\nSome **bold** and *it* with `code` and [link](http://x).\n\n- a\n- b\n\n1. one\n2. two\n\n" \
         "| K | V |\n|---|---|\n| x | 1 |\n\n```\n<raw>\n```"
    out = c.markdown_to_html(md)
    check("markdown_to_html: blocks and inline", all(s in out for s in [
        "<h1>Title</h1>", "<strong>bold</strong>", "<em>it</em>", "<code>code</code>", '<a href="http://x">link</a>',
        "<ul><li>a</li><li>b</li></ul>", "<ol><li>one</li><li>two</li></ol>", "<th>K</th>", "<td>x</td>", "<pre>&lt;raw&gt;</pre>"]),
        out)


def test_ec2_ssm():
    m = load("ec2-ssm")

    def ok(cmd, win=False):
        return not raises(m.check_read_only, cmd, win)

    for cmd in ["df -h", "tail -n 100 /var/log/syslog | grep ERROR", "systemctl status nginx", "find /var/log -name '*.gz'",
                "top -b -n 1 | head -20", "journalctl -u api --since '1 hour ago' --no-pager | tail -n 50"]:
        check(f"linux allowed: {cmd}", ok(cmd))
    for cmd in ["rm -rf /tmp/x", "cat a; rm b", "cat a && reboot", "echo x > /etc/hosts", "cat $(whoami)", "ls `id`",
                "systemctl restart nginx", "cat a || reboot", "sudo cat /etc/shadow", "ls\nreboot", "find / -delete",
                "find . -exec rm {} +", "tail a | xargs rm", "top"]:
        check(f"linux blocked: {cmd!r}", not ok(cmd))
    for cmd in ["Get-Service | Where-Object Status -eq Stopped | Select-Object -First 20",
                "Get-Process | Where-Object { $_.CPU -gt 100 } | Sort-Object CPU -Descending",
                "Get-ChildItem C:\\logs | Where-Object { $_.Name.StartsWith('app') } | Select-Object Name, Length",
                "Get-Date", "gci C:\\logs | % { $_.FullName }",
                "Get-EventLog -LogName System -EntryType Error -Newest 20", "Get-WinEvent -FilterHashtable @{LogName='System'}",
                "Test-NetConnection db01 -Port 5432", "ipconfig", "Get-Content (Get-ChildItem C:\\app\\*.log | Select-Object -First 1).FullName -Tail 50"]:
        check(f"windows allowed: {cmd}", ok(cmd, True))
    for cmd in ["Remove-Item C:\\x", "Stop-Service w3svc", "Get-Service | Stop-Service", "Get-Process; Restart-Computer",
                "Get-ChildItem | ForEach-Object { Remove-Item $_ }", "Get-Content (Remove-Item x)", "Invoke-Expression 'x'",
                "Get-Process > out.txt", "gps | % { $_.Kill() }", "[System.IO.File]::Delete('x')", "$x = Remove-Item y",
                "iex 'x'", "Get-Content \"$(Remove-Item x)\"", "Get-Process | Out-File x.txt", "sc x y", ". .\\script.ps1",
                "Get-WinEvent -FilterHashtable @{LogName=(Remove-Item x)}"]:
        check(f"windows blocked: {cmd!r}", not ok(cmd, True))


def test_db_ssh():
    m = load("db-ssh")
    os.environ.update(SSH_HOST="bastion", SSH_USER="u", SSH_KEY="C:/keys/k.ppk", SSH_PORT="2222", SSH_HOST_KEY="ssh-ed25519 AAA")
    real_which = m.shutil.which
    m.shutil.which = lambda name: "plink" if name == "plink" else None
    cmd = m._tunnel_command(5555, "db", 3306)
    check("db-ssh: .ppk key uses plink with port and host key",
          cmd[0] == "plink" and "-P" in cmd and "-hostkey" in cmd and cmd[-1] == "u@bastion" and "127.0.0.1:5555:db:3306" in cmd)
    m.shutil.which = lambda name: None
    check("db-ssh: .ppk without plink gives a clear error", raises(m._tunnel_command, 5555, "db", 3306))
    m.shutil.which = real_which
    os.environ["SSH_KEY"] = "~/.ssh/id_ed25519"
    cmd = m._tunnel_command(5555, "db", 5432)
    check("db-ssh: OpenSSH key uses ssh in batch mode", cmd[0] == "ssh" and "BatchMode=yes" in cmd and "-p" in cmd)
    for k in ("SSH_HOST", "SSH_USER", "SSH_KEY", "SSH_PORT", "SSH_HOST_KEY"):
        os.environ.pop(k, None)

    os.environ["DB_ENGINE"] = "oracle"
    check("db-ssh: unknown engine rejected", raises(m.engine))
    os.environ["DB_ENGINE"] = "mysql"
    args = argparse.Namespace(file=None, query="delete from t", write=False, limit=50)
    check("db-ssh: mysql write SQL blocked before connecting", raises(m.cmd_sql, args))
    os.environ.pop("DB_ENGINE")


def test_sumologic_time():
    m = load("sumologic")
    now = time.time() * 1000
    check("sumologic: -15m", abs(m.parse_time("-15m") - (now - 900000)) < 5000)
    check("sumologic: ISO time", m.parse_time("2026-11-01T10:00:00") ==
          int(time.mktime(time.strptime("2026-11-01T10:00:00", "%Y-%m-%dT%H:%M:%S")) * 1000))
    check("sumologic: bad time rejected", raises(m.parse_time, "yesterday"))


def test_msteams_webhook():
    m = load("msteams")
    os.environ["TEAMS_WEBHOOK_URL"] = "https://hooks.example.com/x"
    sent = []
    real = m.c.http
    m.c.http = lambda *a, **k: sent.append(k.get("body"))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        m.cmd_send(argparse.Namespace(text="hi", title="T", write=True))
    m.c.http = real
    os.environ.pop("TEAMS_WEBHOOK_URL")
    check("msteams: webhook send posts an adaptive card",
          sent and sent[0]["attachments"][0]["content"]["body"][1]["text"] == "hi")


def test_search():
    with tempfile.TemporaryDirectory() as d:
        prod = Path(d, "shop", "scenarios")
        prod.mkdir(parents=True)
        (prod / "refund-partial.md").write_text("# Scenario: Partial refund\nStatus: verified\nRefund the paid amount minus shipped lines.", encoding="utf-8")
        (prod / "login.md").write_text("# Scenario: Login\nStatus: draft\nUser signs in.", encoding="utf-8")
        Path(d, "templates").mkdir()
        Path(d, "templates", "scenario.md").write_text("# Scenario: refund template", encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "product-knowledge" / "search.py"), "refunds", "--dir", d],
                           capture_output=True, text=True, encoding="utf-8")
        out = r.stdout
        check("search: finds stemmed match with status, skips templates",
              "Partial refund" in out and "[verified]" in out and "template" not in out and "Login" not in out, out + r.stderr)


GOOD_SYSTEM = """# System: Shipping service

> Prepares and tracks every parcel.

Status: verified · Updated: 2026-11-06 · Level 1

## In plain words
The shipping service takes an order that is ready, chooses a carrier, prints a label, and follows the parcel until it arrives at the customer's door.

## Where it fits
```
Order service ──ready order──▶ Shipping service ──label──▶ Carrier
```

## How it works
1. Receive a ready order.
2. Choose a carrier.

**Example:** Maria's order of 3 items goes to the carrier with the lowest price.

## What can go wrong
| Situation | What happens |
|-----------|--------------|
| Carrier is down | The order waits and is retried |

## Evidence
- Carrier choice: `shipping/choose.py` `pick_carrier`

## Read next
- [Place an order](../journeys/place-an-order.md) — the full flow
"""

GOOD_JOURNEY = """# Journey: Place an order

> From checkout to delivery.

Status: draft · Updated: 2026-11-06

## In plain words
A customer pays at checkout, the order is checked, then the shipping service sends the parcel and the customer gets a tracking link.

## The example we follow
Maria orders 3 items for delivery to Leeds.

## The path
```
Customer ──▶ Order service ──▶ Shipping service
```

## Step by step, with the example
1. **Checkout.** Maria pays.
"""


def test_lint():
    with tempfile.TemporaryDirectory() as d:
        prod = Path(d, "shop")
        (prod / "systems").mkdir(parents=True)
        (prod / "journeys").mkdir()
        (prod / "systems" / "shipping.md").write_text(GOOD_SYSTEM, encoding="utf-8")
        (prod / "journeys" / "place-an-order.md").write_text(GOOD_JOURNEY, encoding="utf-8")
        (prod / "glossary.md").write_text("# Glossary\n", encoding="utf-8")
        (prod / "MAP.md").write_text("# Map\n\n## Coverage\n\n| Area | Kind | Target level | Page | Status |\n"
                                     "|---|---|---|---|---|\n| Shipping | system | 1 | systems/shipping.md | done |\n"
                                     "| Orders | journey | 1 | journeys/place-an-order.md | in-progress |\n", encoding="utf-8")

        def lint(extra=()):
            r = subprocess.run([sys.executable, str(ROOT / "product-knowledge" / "lint.py"), "shop", "--dir", d, *extra],
                               capture_output=True, text=True, encoding="utf-8")
            return r.returncode, r.stdout

        # the journey links nowhere yet and nothing links to the journey: only a warning
        code, out = lint()
        check("lint: a good product passes (orphan page is a warning)", code == 0 and "orphan" in out, out)

        sysfile = prod / "systems" / "shipping.md"
        sysfile.write_text(GOOD_SYSTEM.replace("../journeys/place-an-order.md", "../journeys/nope.md"), encoding="utf-8")
        code, out = lint()
        check("lint: broken link is an error", code == 1 and "broken link" in out, out)

        sysfile.write_text(GOOD_SYSTEM.replace("- Carrier choice: `shipping/choose.py` `pick_carrier`", ""), encoding="utf-8")
        code, out = lint()
        check("lint: verified page without evidence is an error", code == 1 and "Evidence section is empty" in out, out)

        sysfile.write_text(GOOD_SYSTEM.replace("## What can go wrong", "## Problems"), encoding="utf-8")
        code, out = lint()
        check("lint: missing required section is an error", code == 1 and "what can go wrong" in out, out)

        sysfile.write_text(GOOD_SYSTEM.replace("Prepares and tracks every parcel.", "<One sentence: what it is>"), encoding="utf-8")
        code, out = lint()
        check("lint: template text left in is an error", code == 1 and "template text left in" in out, out)

        sysfile.write_text(GOOD_SYSTEM.replace("The shipping service takes an order that is ready, chooses a carrier, prints a label, and follows "
                                               "the parcel until it arrives at the customer's door.", "Ships things."), encoding="utf-8")
        code, out = lint()
        check("lint: 'In plain words' that explains nothing is an error", code == 1 and "too short" in out, out)

        sysfile.write_text(GOOD_SYSTEM, encoding="utf-8")
        (prod / "MAP.md").write_text((prod / "MAP.md").read_text(encoding="utf-8").replace("systems/shipping.md", "systems/ghost.md"), encoding="utf-8")
        code, out = lint()
        check("lint: map row pointing to a missing page is an error", code == 1 and "does not exist" in out, out)
        code, _ = lint(["--strict"])
        check("lint: --strict fails on warnings too", code == 1)


# ---------------------------------------------------------------- mock server

seen = []


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, obj=None, headers=None):
        body = b"" if obj is None else json.dumps(obj).encode()
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_any(self):
        u = urlsplit(self.path)
        q = parse_qs(u.query)
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode() if n else ""
        try:
            body = json.loads(raw) if raw else {}
        except ValueError:
            body = raw
        seen.append((self.command, u.path, self.headers.get("Cookie"), body))
        p, cmd = u.path, self.command
        base = f"http://127.0.0.1:{self.server.server_port}"
        routes = {
            # Sumo Logic: search job needs the cookie from the create call
            ("POST", "/sumo/v1/search/jobs"): (202, {"id": "J1"}, {"Set-Cookie": "JSESSIONID=abc; Path=/"}),
            ("GET", "/sumo/v1/search/jobs/J1/records"): (200, {"records": [{"map": {"_sourcecategory": "prod/api", "_count": "41"}}]}),
            ("DELETE", "/sumo/v1/search/jobs/J1"): (200, {}),
            # Jira: Cloud search/jql missing -> Data Center /search
            ("GET", "/jira/rest/api/2/myself"): (200, {"displayName": "Test User"}),
            ("GET", "/jira/rest/api/2/search/jql"): (404, {"errorMessages": ["no"]}),
            ("GET", "/jira/rest/api/2/search"): (200, {"total": 1, "issues": [{"key": "PAY-1", "fields": {
                "summary": "Refund \u200bbroken", "status": {"name": "Open"}, "issuetype": {"name": "Bug"},
                "priority": {"name": "High"}, "assignee": None, "updated": "2026-10-30"}}]}),
            ("GET", "/jira/rest/api/2/issue/PAY-1"): (200, {"key": "PAY-1", "fields": {"summary": "Refund broken",
                "status": {"name": "Open"}, "issuetype": {"name": "Bug"}, "description": "Steps: cancel order"}}),
            ("GET", "/jira/rest/api/2/issue/PAY-1/comment"): (200, {"total": 1, "comments": [
                {"author": {"displayName": "QA"}, "created": "2026-10-31", "body": "Repro ok"}]}),
            # Confluence: page 55 only on the v2 API, page 66 on v1
            ("GET", "/wiki/rest/api/search"): (200, {"results": [{"content": {"id": "55"}, "title": "Refunds",
                "excerpt": "@@@hl@@@refund@@@endhl@@@ rules", "resultGlobalContainer": {"title": "Payments"}}]}),
            ("GET", "/wiki/rest/api/content/55"): (404, {}),
            ("GET", "/wiki/api/v2/pages/55"): (200, {"title": "Refunds", "spaceId": "9", "version": {"number": 3},
                "body": {"storage": {"value": "<h2>Rules</h2><p>Full refund within 30 days.</p>"}}}),
            ("GET", "/wiki/rest/api/content/66"): (200, {"title": "Old", "space": {"key": "PAY"}, "version": {"number": 7},
                "body": {"storage": {"value": "<p>old body</p>"}}}),
            ("PUT", "/wiki/rest/api/content/66"): (200, {"id": "66"}),
            ("GET", "/wiki/api/v2/spaces"): (200, {"results": [{"id": "9"}]}),
            ("POST", "/wiki/api/v2/pages"): (200, {"id": "78"}),
            # Harness
            ("GET", "/harness/ng/api/projects/proj"): (200, {"data": {"project": {"name": "Payments"}}}),
            ("POST", "/harness/pipeline/api/pipelines/execution/summary"): (200, {"data": {"content": [{
                "planExecutionId": "E1", "pipelineIdentifier": "deploy", "runSequence": 12, "status": "Failed",
                "startTs": 1761990000000, "endTs": 1761990125000, "executionTriggerInfo": {"triggeredBy": {"identifier": "alice"}}}]}}),
            ("GET", "/harness/pipeline/api/pipelines/execution/v2/E1"): (200, {"data": {"pipelineExecutionSummary": {
                "pipelineIdentifier": "deploy", "status": "Failed", "failureInfo": {"message": "Helm upgrade failed"},
                "layoutNodeMap": {"b": {"name": "Deploy", "status": "Failed", "failureInfo": {"message": "timeout"}}}}}}),
            ("POST", "/harness/pipeline/api/pipeline/execute/deploy"): (200, {"data": {"planExecution": {"uuid": "E2", "status": "RUNNING"}}}),
            # Microsoft Graph
            ("GET", "/graph/me"): (200, {"displayName": "Test User", "userPrincipalName": "t@x.com"}),
            ("GET", "/graph/me/joinedTeams"): (200, {"value": [{"id": "T1", "displayName": "Payments Team"},
                                                               {"id": "T2", "displayName": "Platform"}]}),
            ("GET", "/graph/teams/T1/channels"): (200, {"value": [{"id": "C1", "displayName": "incidents"},
                                                                  {"id": "C2", "displayName": "General"}]}),
            ("GET", "/graph/teams/T1/channels/C1/messages"): (200, {
                "value": [{"id": "M1", "messageType": "message", "createdDateTime": "2026-11-01T10:00:00Z",
                           "from": {"user": {"displayName": "Ana"}}, "body": {"content": "<p>API is <b>down</b></p>"}}],
                "@odata.nextLink": f"{base}/graph/page2"}),
            ("GET", "/graph/page2"): (200, {"value": [{"id": "M0", "messageType": "message", "createdDateTime": "2026-11-01T09:00:00Z",
                                                       "from": {"user": {"displayName": "Bo"}}, "body": {"content": "earlier"}},
                                                      {"id": "S1", "messageType": "systemEventMessage", "body": {"content": ""}}]}),
            ("POST", "/graph/teams/T1/channels/C1/messages"): (201, {"id": "M9"}),
        }
        if (cmd, p) == ("GET", "/sumo/v1/search/jobs/J1"):
            if self.headers.get("Cookie") != "JSESSIONID=abc":
                return self.reply(404, {"message": "no cookie"})
            return self.reply(200, {"state": "DONE GATHERING RESULTS", "messageCount": 3, "recordCount": 1, "pendingErrors": []})
        if (cmd, p) == ("POST", "/wiki/rest/api/content"):
            if isinstance(body, dict) and body.get("title") == "Gone v1":
                return self.reply(410, {})
            return self.reply(200, {"id": "77"})
        if (cmd, p) == ("GET", "/harness/ng/api/projects/proj") and self.headers.get("x-api-key") != "k":
            return self.reply(401, {"message": "bad key"})
        if (cmd, p) in routes:
            return self.reply(*routes[(cmd, p)])
        return self.reply(404, {"message": f"mock has no {cmd} {p}"})

    do_GET = do_POST = do_PUT = do_DELETE = handle_any


def test_connectors_against_mock():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Mock)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    env = dict(os.environ,
               SUMO_ACCESS_ID="id", SUMO_ACCESS_KEY="key", SUMO_API_URL=f"{base}/sumo",
               JIRA_URL=f"{base}/jira", JIRA_TOKEN="t", JIRA_EMAIL="",
               CONFLUENCE_URL=f"{base}/wiki", CONFLUENCE_TOKEN="t", CONFLUENCE_EMAIL="",
               HARNESS_URL=f"{base}/harness", HARNESS_API_KEY="k", HARNESS_ACCOUNT_ID="acc", HARNESS_ORG="o", HARNESS_PROJECT="proj",
               TEAMS_GRAPH_URL=f"{base}/graph", TEAMS_ACCESS_TOKEN="tok")

    with tempfile.TemporaryDirectory() as d:
        page = Path(d, "page.md")
        page.write_text("# Refunds\n\n- full within 30 days", encoding="utf-8")

        def run(label, args, expect, code=0, extra_env=None):
            r = subprocess.run([sys.executable, str(HERE / args[0] / "run.py"), *args[1:]], capture_output=True,
                               text=True, encoding="utf-8", env=dict(env, **(extra_env or {})))
            out = r.stdout + r.stderr
            check(label, r.returncode == code and all(x in out for x in expect), f"exit={r.returncode} output:\n{out}")

        run("sumologic: query uses cookie, prints records", ["sumologic", "query", "x | count", "--from", "-1h"], ["records: 1", "_count", "41"])
        run("sumologic: saved query", ["sumologic", "query", "@errors-by-source"], ["records: 1"])
        run("jira: test", ["jira", "test"], ["Test User"])
        run("jira: search falls back to Data Center API", ["jira", "search", "project = PAY"], ["PAY-1", "Refund broken"])
        run("jira: get with comments", ["jira", "get", "PAY-1"], ["Steps: cancel order", "Repro ok"])
        run("jira: comment needs --write", ["jira", "comment", "PAY-1", "hi"], ["needs --write"], code=1)
        run("confluence: search strips highlight marks", ["confluence", "search", "refund"], ["Refunds", "refund rules"])
        run("confluence: get falls back to v2 API", ["confluence", "get", "55"], ["## Rules", "Full refund within 30 days."])
        run("confluence: create needs --write", ["confluence", "create", "--space", "PAY", "--title", "X", "--text", "y"], ["needs --write"], code=1)
        run("confluence: create (v1)", ["confluence", "create", "--space", "PAY", "--title", "New", "--parent", "66",
                                        "--file", str(page), "--write"], ["Created page 77"])
        run("confluence: create falls back to v2", ["confluence", "create", "--space", "PAY", "--title", "Gone v1",
                                                    "--text", "hello", "--write"], ["Created page 78"])
        run("confluence: update --append bumps version", ["confluence", "update", "66", "--text", "more", "--append", "--write"],
            ["version 8"])
        run("harness: test", ["harness", "test"], ["project 'Payments'"])
        run("harness: runs", ["harness", "runs", "--status", "Failed"], ["E1", "2m05s", "alice"])
        run("harness: run-detail", ["harness", "run-detail", "E1"], ["Helm upgrade failed", "timeout"])
        run("harness: start --write", ["harness", "start", "deploy", "--write"], ["Execution ID: E2"])
        run("harness: bad key shows hint", ["harness", "test"], ["HTTP 401", "Authentication failed"], code=1,
            extra_env={"HARNESS_API_KEY": "bad"})
        run("msteams: test with Graph token", ["msteams", "test"], ["signed in as Test User"])
        run("msteams: channels by partial team name", ["msteams", "channels", "payments"], ["incidents", "General"])
        run("msteams: messages follow next page, newest first, skip system events",
            ["msteams", "messages", "Payments Team", "incid", "--limit", "10"], ["API is down", "Ana", "earlier", "2 rows"])
        run("msteams: ambiguous name is rejected", ["msteams", "channels", "a"], ["Several teams match"], code=1)
        run("msteams: post needs --write", ["msteams", "post", "Payments Team", "incidents", "hi"], ["needs --write"], code=1)
        run("msteams: post --write", ["msteams", "post", "Payments Team", "incidents", "**done**", "--write"], ["message M9"])

    cookie_calls = [s for s in seen if s[1].startswith("/sumo/v1/search/jobs/J1")]
    check("sumologic: cookie on every call, job deleted after",
          cookie_calls and all(s[2] == "JSESSIONID=abc" for s in cookie_calls) and any(s[0] == "DELETE" for s in cookie_calls))
    update = next((s for s in seen if s[0] == "PUT"), None)
    check("confluence: update keeps old body and appends new",
          update and "old body" in update[3]["body"]["storage"]["value"] and "more" in update[3]["body"]["storage"]["value"])
    create = next((s for s in seen if s[0] == "POST" and s[1] == "/wiki/rest/api/content" and s[3].get("title") == "New"), None)
    check("confluence: Markdown converted, parent set",
          create and "<h1>Refunds</h1>" in create[3]["body"]["storage"]["value"] and create[3]["ancestors"] == [{"id": "66"}])
    post = next((s for s in seen if s[0] == "POST" and s[1].startswith("/graph/teams")), None)
    check("msteams: post sends HTML", post and "<strong>done</strong>" in post[3]["body"]["content"])
    srv.shutdown()


def main():
    for test in (test_common, test_ec2_ssm, test_db_ssh, test_sumologic_time, test_msteams_webhook, test_search,
                 test_lint, test_connectors_against_mock):
        print(f"\n== {test.__name__[5:]}")
        test()
    print(f"\n{'All checks passed.' if not failures else f'{len(failures)} check(s) failed:'}")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
