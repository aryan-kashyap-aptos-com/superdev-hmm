"""harness: read Harness CI/CD pipelines and runs. Starting a run needs --write."""
import argparse
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)


def api(method, path, params=None, body=None, content_type=None):
    key, account = c.need("HARNESS_API_KEY", "HARNESS_ACCOUNT_ID")
    base = (c.setting("HARNESS_URL", "https://app.harness.io")).rstrip("/")
    query = urllib.parse.urlencode({"accountIdentifier": account, **{k: v for k, v in (params or {}).items() if v is not None}})
    headers = {"x-api-key": key}
    if content_type:
        headers["Content-Type"] = content_type
    res = c.http(method, f"{base}{path}?{query}", headers, body)
    return res.get("data") if isinstance(res, dict) and "data" in res else res


def scope(args):
    org, project = args.org or c.setting("HARNESS_ORG"), args.project or c.setting("HARNESS_PROJECT")
    if not org or not project:
        raise c.ConnectorError("Missing org or project.", "Set HARNESS_ORG and HARNESS_PROJECT in .env, or pass --org and --project.")
    return {"orgIdentifier": org, "projectIdentifier": project}


def _duration(start, end):
    if not start or not end:
        return ""
    secs = int((int(end) - int(start)) / 1000)
    return f"{secs // 60}m{secs % 60:02d}s"


def cmd_test(args):
    s = scope(args)
    data = api("GET", f"/ng/api/projects/{s['projectIdentifier']}", {"orgIdentifier": s["orgIdentifier"]})
    name = (data or {}).get("project", {}).get("name", s["projectIdentifier"])
    print(f"Harness access OK: project '{name}' in org '{s['orgIdentifier']}'.")


def cmd_list(args):
    data = api("POST", "/pipeline/api/pipelines/list",
               {**scope(args), "page": 0, "size": args.limit, "searchTerm": args.search},
               {"filterType": "PipelineSetup"})
    rows = []
    for p in (data or {}).get("content", []):
        last = p.get("executionSummaryInfo") or {}
        rows.append([p.get("identifier"), p.get("name"), last.get("lastExecutionStatus", ""),
                     c.fmt_ms(last.get("lastExecutionTs"))])
    c.show_table(rows, ["identifier", "name", "last_status", "last_run"], "harness-pipelines", limit=args.limit)


def cmd_runs(args):
    body = {"filterType": "PipelineExecution"}
    if args.status:
        body["status"] = [args.status]
    data = api("POST", "/pipeline/api/pipelines/execution/summary",
               {**scope(args), "page": 0, "size": args.limit, "pipelineIdentifier": args.pipeline}, body)
    rows = []
    for e in (data or {}).get("content", []):
        trigger = (e.get("executionTriggerInfo") or {}).get("triggeredBy") or {}
        rows.append([e.get("planExecutionId"), e.get("pipelineIdentifier"), e.get("runSequence"), e.get("status"),
                     c.fmt_ms(e.get("startTs")), _duration(e.get("startTs"), e.get("endTs")),
                     trigger.get("identifier", "")])
    c.show_table(rows, ["execution_id", "pipeline", "run", "status", "started", "duration", "triggered_by"],
                 "harness-runs", limit=args.limit)


def cmd_run_detail(args):
    data = api("GET", f"/pipeline/api/pipelines/execution/v2/{args.execution_id}", scope(args)) or {}
    s = data.get("pipelineExecutionSummary") or {}
    print(f"Pipeline: {s.get('pipelineIdentifier')}  Run: {s.get('runSequence')}  Status: {s.get('status')}")
    print(f"Started: {c.fmt_ms(s.get('startTs'))}  Duration: {_duration(s.get('startTs'), s.get('endTs'))}")
    failure = (s.get("failureInfo") or {}).get("message")
    if failure:
        print(f"Failure: {c.clean(failure)}")
    rows = []
    for node in (s.get("layoutNodeMap") or {}).values():
        rows.append([node.get("name"), node.get("nodeType"), node.get("status"),
                     c.fmt_ms(node.get("startTs")), _duration(node.get("startTs"), node.get("endTs")),
                     (node.get("failureInfo") or {}).get("message", "")])
    print()
    c.show_table(rows, ["stage", "type", "status", "started", "duration", "failure"], "harness-run-detail", limit=100)


def cmd_start(args):
    c.require_write(args, "start")
    inputs = Path(args.inputs).read_text(encoding="utf-8") if args.inputs else ""
    data = api("POST", f"/pipeline/api/pipeline/execute/{args.pipeline}", scope(args), inputs, "application/yaml") or {}
    run = data.get("planExecution") or {}
    print(f"Started pipeline '{args.pipeline}'. Execution ID: {run.get('uuid', '(not returned)')}  Status: {run.get('status', '')}")
    print("Check progress with: run-detail <execution_id>")


def main():
    p = argparse.ArgumentParser(description="Read Harness pipelines and runs (start needs --write).")
    p.add_argument("--org", help="org identifier (default HARNESS_ORG)")
    p.add_argument("--project", help="project identifier (default HARNESS_PROJECT)")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("test", help="check settings and access").set_defaults(func=cmd_test)

    s = sub.add_parser("list", help="list pipelines")
    s.add_argument("--search", help="filter by name")
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("runs", help="list recent runs")
    s.add_argument("--pipeline", help="only this pipeline identifier")
    s.add_argument("--status", help="Success, Failed, Running, Aborted, Expired, ...")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_runs)

    s = sub.add_parser("run-detail", help="show stages and failure of one run")
    s.add_argument("execution_id")
    s.set_defaults(func=cmd_run_detail)

    s = sub.add_parser("start", help="start a pipeline run (needs --write)")
    s.add_argument("pipeline", help="pipeline identifier")
    s.add_argument("--inputs", help="YAML file with runtime inputs")
    s.add_argument("--write", action="store_true", help="needed; ask the user first")
    s.set_defaults(func=cmd_start)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    c.run(main)
