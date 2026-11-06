"""confluence: search, read, create and update Confluence pages. Changes need --write."""
import argparse
import re
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)


def api(method, path, params=None, body=None):
    url, token = c.need("CONFLUENCE_URL", "CONFLUENCE_TOKEN")
    email = c.setting("CONFLUENCE_EMAIL")
    # Cloud: email + API token (Basic). Data Center / Server: personal access token (Bearer).
    auth = c.basic_auth(email, token) if email else f"Bearer {token}"
    query = "?" + urllib.parse.urlencode(params) if params else ""
    return c.http(method, f"{url.rstrip('/')}{path}{query}", {"Authorization": auth}, body)


def page_id(value):
    m = re.search(r"/pages/(\d+)", value) or re.search(r"pageId=(\d+)", value)
    if m:
        return m.group(1)
    if value.isdigit():
        return value
    raise c.ConnectorError(f"Cannot find a page ID in '{value}'.", "Give the numeric page ID or the page URL.")


def _moved(e):
    """True when an old API path is gone and the newer Cloud API should be tried."""
    return e.status in (404, 405, 410)


def search(cql, limit):
    """Use the general search API; fall back to content search on older servers."""
    try:
        res = api("GET", "/rest/api/search", {"cql": cql, "limit": limit})
        return [(r.get("content", {}).get("id", ""), r.get("title", ""),
                 (r.get("resultGlobalContainer") or {}).get("title", ""),
                 (r.get("lastModified") or "")[:10], re.sub(r"@@@(end)?hl@@@", "", r.get("excerpt", "")))
                for r in res.get("results", [])]
    except c.ConnectorError as e:
        if not _moved(e):
            raise
    res = api("GET", "/rest/api/content/search", {"cql": cql, "limit": limit, "expand": "space,version"})
    return [(r.get("id", ""), r.get("title", ""), (r.get("space") or {}).get("key", ""),
             ((r.get("version") or {}).get("when") or "")[:10], "") for r in res.get("results", [])]


def load_page(pid):
    """Return dict(title, space, version, when, body) using the v1 API, or the v2 Cloud API if v1 is gone."""
    try:
        p = api("GET", f"/rest/api/content/{pid}", {"expand": "body.storage,version,space"})
        v = p.get("version") or {}
        return {"title": p.get("title"), "space": (p.get("space") or {}).get("key", ""), "version": v.get("number"),
                "when": (v.get("when") or "")[:10], "body": ((p.get("body") or {}).get("storage") or {}).get("value", ""),
                "api": "v1"}
    except c.ConnectorError as e:
        if not _moved(e):
            raise
    p = api("GET", f"/api/v2/pages/{pid}", {"body-format": "storage"})
    v = p.get("version") or {}
    return {"title": p.get("title"), "space": p.get("spaceId", ""), "version": v.get("number"),
            "when": (v.get("createdAt") or "")[:10], "body": ((p.get("body") or {}).get("storage") or {}).get("value", ""),
            "api": "v2"}


def read_body(args):
    """Page content from --text or --file. Markdown is converted unless --html is given."""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        raise c.ConnectorError("Give the content with --file or --text.")
    return text if args.html else c.markdown_to_html(text)


def _page_url(pid):
    return f"{c.setting('CONFLUENCE_URL').rstrip('/')}/pages/viewpage.action?pageId={pid}"


def cmd_test(args):
    search("type=page", 1)
    print(f"Confluence access OK ({c.setting('CONFLUENCE_URL')}).")


def cmd_search(args):
    parts = ["type=page"]
    if args.text:
        parts.append('text ~ "{}"'.format(args.text.replace("\\", "\\\\").replace('"', '\\"')))
    if args.space:
        parts.append(f'space = "{args.space}"')
    if args.under:
        parts.append(f"ancestor = {page_id(args.under)}")
    if len(parts) == 1:
        raise c.ConnectorError("Give search text, --space, or --under.")
    cql = " AND ".join(parts) + " ORDER BY lastmodified DESC"
    c.show_table(search(cql, args.limit), ["id", "title", "space", "updated", "excerpt"], "confluence-search", limit=args.limit)


def cmd_get(args):
    pid = page_id(args.page)
    p = load_page(pid)
    header = f"# {p['title']}\nPage {pid} · Space {p['space']} · Version {p['version']} · Updated {p['when']}\n\n"
    c.show_text(header + c.html_to_text(p["body"]), f"confluence-{pid}")


def cmd_create(args):
    c.require_write(args, "create")
    body = read_body(args)
    parent = page_id(args.parent) if args.parent else None
    try:
        data = {"type": "page", "title": args.title, "space": {"key": args.space},
                "body": {"storage": {"value": body, "representation": "storage"}}}
        if parent:
            data["ancestors"] = [{"id": parent}]
        res = api("POST", "/rest/api/content", body=data)
    except c.ConnectorError as e:
        if not _moved(e):
            raise
        spaces = api("GET", "/api/v2/spaces", {"keys": args.space}).get("results", [])
        if not spaces:
            raise c.ConnectorError(f"Space '{args.space}' not found.") from None
        data = {"spaceId": spaces[0]["id"], "status": "current", "title": args.title,
                "body": {"representation": "storage", "value": body}}
        if parent:
            data["parentId"] = parent
        res = api("POST", "/api/v2/pages", body=data)
    print(f"Created page {res.get('id')}: {args.title}\n{_page_url(res.get('id'))}")


def cmd_update(args):
    c.require_write(args, "update")
    pid = page_id(args.page)
    current = load_page(pid)
    body = read_body(args)
    if args.append:
        body = current["body"] + "\n" + body
    title = args.title or current["title"]
    version = (current["version"] or 0) + 1
    if current["api"] == "v1":
        api("PUT", f"/rest/api/content/{pid}", body={
            "id": pid, "type": "page", "title": title, "version": {"number": version},
            "body": {"storage": {"value": body, "representation": "storage"}}})
    else:
        api("PUT", f"/api/v2/pages/{pid}", body={
            "id": pid, "status": "current", "title": title, "version": {"number": version},
            "body": {"representation": "storage", "value": body}})
    print(f"Updated page {pid} to version {version}: {title}\n{_page_url(pid)}")


def cmd_comment(args):
    c.require_write(args, "comment")
    pid = page_id(args.page)
    body = c.markdown_to_html(args.text)
    try:
        res = api("POST", "/rest/api/content", body={
            "type": "comment", "container": {"id": pid, "type": "page"},
            "body": {"storage": {"value": body, "representation": "storage"}}})
    except c.ConnectorError as e:
        if not _moved(e):
            raise
        res = api("POST", "/api/v2/footer-comments", body={"pageId": pid, "body": {"representation": "storage", "value": body}})
    print(f"Comment {res.get('id')} added to page {pid}.")


def main():
    p = argparse.ArgumentParser(description="Search, read, create and update Confluence pages (changes need --write).")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("test", help="check settings and access").set_defaults(func=cmd_test)

    s = sub.add_parser("search", help="find pages")
    s.add_argument("text", nargs="?", help="words to search for")
    s.add_argument("--space", help="space key")
    s.add_argument("--under", help="only pages below this page (ID or URL)")
    s.add_argument("--limit", type=int, default=15)
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("get", help="read a page as text")
    s.add_argument("page", help="page ID or URL")
    s.set_defaults(func=cmd_get)

    def content_args(s):
        s.add_argument("--file", help="content file (Markdown, or Confluence HTML with --html)")
        s.add_argument("--text", help="content as text (Markdown)")
        s.add_argument("--html", action="store_true", help="content is Confluence storage HTML, not Markdown")
        s.add_argument("--write", action="store_true", help="needed; ask the user first")

    s = sub.add_parser("create", help="create a page (needs --write)")
    s.add_argument("--space", required=True, help="space key")
    s.add_argument("--title", required=True)
    s.add_argument("--parent", help="parent page ID or URL")
    content_args(s)
    s.set_defaults(func=cmd_create)

    s = sub.add_parser("update", help="replace or append page content (needs --write)")
    s.add_argument("page", help="page ID or URL")
    s.add_argument("--title", help="new title (default: keep)")
    s.add_argument("--append", action="store_true", help="add to the end instead of replacing")
    content_args(s)
    s.set_defaults(func=cmd_update)

    s = sub.add_parser("comment", help="add a comment to a page (needs --write)")
    s.add_argument("page", help="page ID or URL")
    s.add_argument("text", help="comment text (Markdown)")
    s.add_argument("--write", action="store_true", help="needed; ask the user first")
    s.set_defaults(func=cmd_comment)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    c.run(main)
