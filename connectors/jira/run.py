"""jira: read and search Jira issues. Commenting and creating need --write."""
import argparse
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)

LIST_FIELDS = "summary,status,issuetype,priority,assignee,updated"
DETAIL_FIELDS = ("summary,status,issuetype,priority,assignee,reporter,labels,components,fixVersions,"
                 "parent,created,updated,resolution,description")


def api(method, path, params=None, body=None):
    url, token = c.need("JIRA_URL", "JIRA_TOKEN")
    email = c.setting("JIRA_EMAIL")
    # Cloud: email + API token (Basic). Data Center / Server: personal access token (Bearer).
    auth = c.basic_auth(email, token) if email else f"Bearer {token}"
    query = "?" + urllib.parse.urlencode(params) if params else ""
    return c.http(method, f"{url.rstrip('/')}{path}{query}", {"Authorization": auth}, body)


def _name(person):
    return (person or {}).get("displayName", "-")


def cmd_test(args):
    me = api("GET", "/rest/api/2/myself")
    print(f"Jira access OK as {me.get('displayName')} ({c.setting('JIRA_URL')}).")


def cmd_get(args):
    issue = api("GET", f"/rest/api/2/issue/{args.key}", {"fields": DETAIL_FIELDS})
    f = issue["fields"]
    lines = [
        f"{issue['key']}: {f.get('summary')}",
        f"Type: {(f.get('issuetype') or {}).get('name')} · Status: {(f.get('status') or {}).get('name')} · "
        f"Priority: {(f.get('priority') or {}).get('name', '-')} · Resolution: {(f.get('resolution') or {}).get('name', '-')}",
        f"Assignee: {_name(f.get('assignee'))} · Reporter: {_name(f.get('reporter'))}",
        f"Created: {f.get('created', '')[:16]} · Updated: {f.get('updated', '')[:16]}",
    ]
    if f.get("parent"):
        lines.append(f"Parent: {f['parent']['key']} {f['parent'].get('fields', {}).get('summary', '')}")
    if f.get("labels"):
        lines.append("Labels: " + ", ".join(f["labels"]))
    if f.get("components"):
        lines.append("Components: " + ", ".join(x["name"] for x in f["components"]))
    if f.get("fixVersions"):
        lines.append("Fix versions: " + ", ".join(x["name"] for x in f["fixVersions"]))
    lines += ["", "## Description", f.get("description") or "(empty)"]

    if args.comments:
        res = api("GET", f"/rest/api/2/issue/{args.key}/comment", {"orderBy": "-created", "maxResults": args.comments})
        comments = res.get("comments", [])
        lines += ["", f"## Comments (latest {len(comments)} of {res.get('total', len(comments))})"]
        for cm in comments:
            lines += [f"- {_name(cm.get('author'))}, {cm.get('created', '')[:16]}:", f"  {cm.get('body', '')}"]
    c.show_text("\n".join(lines), f"jira-{args.key}")


def cmd_search(args):
    params = {"jql": args.jql, "maxResults": args.limit, "fields": LIST_FIELDS}
    try:
        res = api("GET", "/rest/api/2/search/jql", params)   # Jira Cloud
    except c.ConnectorError as e:
        if e.status not in (404, 405, 410):
            raise
        res = api("GET", "/rest/api/2/search", params)        # Jira Data Center / Server
    rows = []
    for issue in res.get("issues", []):
        f = issue["fields"]
        rows.append([issue["key"], (f.get("issuetype") or {}).get("name"), (f.get("status") or {}).get("name"),
                     (f.get("priority") or {}).get("name", ""), _name(f.get("assignee")),
                     (f.get("updated") or "")[:10], f.get("summary")])
    c.show_table(rows, ["key", "type", "status", "priority", "assignee", "updated", "summary"], "jira", limit=args.limit)
    if res.get("nextPageToken") or res.get("total", 0) > len(rows):
        print("(more issues match; narrow the JQL or raise --limit)")


def cmd_comment(args):
    c.require_write(args, "comment")
    res = api("POST", f"/rest/api/2/issue/{args.key}/comment", body={"body": args.text})
    print(f"Comment added to {args.key} (id {res.get('id')}).")


def cmd_create(args):
    c.require_write(args, "create")
    fields = {"project": {"key": args.project}, "issuetype": {"name": args.type}, "summary": args.summary}
    if args.description:
        fields["description"] = args.description
    if args.labels:
        fields["labels"] = [x.strip() for x in args.labels.split(",") if x.strip()]
    res = api("POST", "/rest/api/2/issue", body={"fields": fields})
    print(f"Created {res.get('key')}: {c.setting('JIRA_URL').rstrip('/')}/browse/{res.get('key')}")


def main():
    p = argparse.ArgumentParser(description="Read and search Jira issues (comment and create need --write).")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("test", help="check settings and access").set_defaults(func=cmd_test)

    s = sub.add_parser("get", help="show one issue")
    s.add_argument("key", help="issue key, for example PROJ-123")
    s.add_argument("--comments", type=int, default=5, help="latest comments to show (default 5, 0 for none)")
    s.set_defaults(func=cmd_get)

    s = sub.add_parser("search", help="search with JQL")
    s.add_argument("jql")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("comment", help="add a comment (needs --write)")
    s.add_argument("key")
    s.add_argument("text")
    s.add_argument("--write", action="store_true", help="needed; ask the user first")
    s.set_defaults(func=cmd_comment)

    s = sub.add_parser("create", help="create an issue (needs --write)")
    s.add_argument("--project", required=True)
    s.add_argument("--type", default="Task", help="Task, Bug, Story, ... (default Task)")
    s.add_argument("--summary", required=True)
    s.add_argument("--description")
    s.add_argument("--labels", help="comma-separated")
    s.add_argument("--write", action="store_true", help="needed; ask the user first")
    s.set_defaults(func=cmd_create)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    c.run(main)
