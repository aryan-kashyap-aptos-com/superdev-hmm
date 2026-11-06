"""sumologic: search Sumo Logic logs with the Search Job API. Read-only."""
import argparse
import http.cookiejar
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)

QUERIES_DIR = HERE / "queries"
FETCH_CAP = 10000
_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_time(value):
    """'now', '-15m', '-2h', '-1d', epoch ms, or 'YYYY-MM-DDTHH:MM:SS' (local time). Returns epoch ms."""
    value = value.strip()
    if value == "now":
        return int(time.time() * 1000)
    m = re.fullmatch(r"-(\d+)([smhdw])", value)
    if m:
        return int((time.time() - int(m.group(1)) * _UNITS[m.group(2)]) * 1000)
    if value.isdigit():
        return int(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return int(time.mktime(time.strptime(value, fmt)) * 1000)
        except ValueError:
            pass
    raise c.ConnectorError(f"Cannot read the time '{value}'.", "Use now, -15m, -2h, -1d, or 2026-11-01T10:00:00.")


class Sumo:
    def __init__(self):
        access_id, access_key = c.need("SUMO_ACCESS_ID", "SUMO_ACCESS_KEY")
        deployment = (c.setting("SUMO_DEPLOYMENT", "us1")).lower()
        self.base = c.setting("SUMO_API_URL") or (
            "https://api.sumologic.com/api" if deployment == "us1" else f"https://api.{deployment}.sumologic.com/api")
        self.auth = c.basic_auth(access_id, access_key)
        # Search jobs need the cookies from the create call on every later call.
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, method, path, body=None, params=None):
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        return c.http(method, url, {"Authorization": self.auth}, body, opener=self.opener)

    def search(self, query, start_ms, end_ms, max_wait):
        job = self.call("POST", "/v1/search/jobs", {
            "query": query, "from": start_ms, "to": end_ms, "timeZone": c.setting("SUMO_TIMEZONE", "UTC")})
        job_id = job["id"]
        try:
            deadline = time.time() + max_wait
            delay = 1
            while True:
                status = self.call("GET", f"/v1/search/jobs/{job_id}")
                state = status.get("state")
                if state == "DONE GATHERING RESULTS":
                    break
                if state == "CANCELLED":
                    raise c.ConnectorError("Sumo Logic cancelled the search.", "Simplify the query or shorten the time range.")
                if time.time() > deadline:
                    raise c.ConnectorError(f"Search still running after {max_wait}s.", "Shorten the time range, add filters, or raise --wait.")
                time.sleep(delay)
                delay = min(delay * 2, 5)
            errors = status.get("pendingErrors") or []
            if errors:
                raise c.ConnectorError("Query error: " + "; ".join(errors), "Fix the query syntax.")
            if status.get("recordCount", 0) > 0:
                return "records", self._page(job_id, "records", min(status["recordCount"], FETCH_CAP)), status
            return "messages", self._page(job_id, "messages", min(status.get("messageCount", 0), FETCH_CAP)), status
        finally:
            try:
                self.call("DELETE", f"/v1/search/jobs/{job_id}")
            except c.ConnectorError:
                pass

    def _page(self, job_id, kind, total):
        items, offset = [], 0
        while offset < total:
            res = self.call("GET", f"/v1/search/jobs/{job_id}/{kind}", params={"offset": offset, "limit": min(10000, total - offset)})
            batch = res.get(kind, [])
            if not batch:
                break
            items += [b["map"] for b in batch]
            offset += len(batch)
        return items


def _load_query(text):
    """A query can be inline text or @name to load sumologic/queries/name.txt."""
    if text.startswith("@"):
        path = QUERIES_DIR / (text[1:] + ("" if text.endswith(".txt") else ".txt"))
        if not path.exists():
            raise c.ConnectorError(f"Saved query not found: {path.name}", "Run 'saved' to list saved queries.")
        return path.read_text(encoding="utf-8").strip()
    return text


def cmd_test(args):
    sumo = Sumo()
    try:
        sumo.call("GET", "/v1/collectors", params={"limit": 1})
        print(f"Sumo Logic access OK ({sumo.base}).")
    except c.ConnectorError as e:
        if e.status == 403:
            print(f"Sumo Logic login OK ({sumo.base}). The key cannot list collectors, which is fine for search.")
        else:
            raise


def cmd_saved(args):
    files = sorted(QUERIES_DIR.glob("*.txt")) if QUERIES_DIR.exists() else []
    if not files:
        print(f"No saved queries. Add .txt files to {QUERIES_DIR}")
        return
    rows = [[f.stem, f.read_text(encoding="utf-8").strip().splitlines()[0][:150]] for f in files]
    c.show_table(rows, ["name", "first line"], "saved-queries", limit=200)


def cmd_query(args):
    query = _load_query(args.query)
    start, end = parse_time(args.start), parse_time(args.end)
    if start >= end:
        raise c.ConnectorError("--from must be earlier than --to.")
    print(f"Searching {c.fmt_ms(start)} to {c.fmt_ms(end)} (local time)...", file=sys.stderr)
    kind, items, status = Sumo().search(query, start, end, args.wait)
    if not items:
        print(f"No results. Messages scanned: {status.get('messageCount', 0)}.")
        return
    if kind == "records":
        columns = list(dict.fromkeys(k for item in items[:100] for k in item))
    else:
        preferred = ["_messagetime", "_sourcecategory", "_sourcehost", "_raw"]
        columns = [k for k in preferred if k in items[0]] or sorted(items[0])[:6]
    rows = []
    for item in items:
        row = []
        for col in columns:
            v = item.get(col, "")
            row.append(c.fmt_ms(v) if col in ("_messagetime", "_receipttime") and str(v).isdigit() else v)
        rows.append(row)
    print(f"{kind}: {len(items)}" + (" (fetch limit reached)" if len(items) >= FETCH_CAP else ""))
    c.show_table(rows, columns, "sumologic", limit=args.limit)


def main():
    p = argparse.ArgumentParser(description="Search Sumo Logic logs (read-only).")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("test", help="check settings and access").set_defaults(func=cmd_test)
    sub.add_parser("saved", help="list saved queries in sumologic/queries/").set_defaults(func=cmd_saved)

    s = sub.add_parser("query", help="run a search")
    s.add_argument("query", help="query text, or @name for a saved query")
    s.add_argument("--from", dest="start", default="-15m", help="start: -15m, -2h, -1d, or 2026-11-01T10:00:00 (default -15m)")
    s.add_argument("--to", dest="end", default="now", help="end (default now)")
    s.add_argument("--limit", type=int, default=c.MAX_ROWS, help="rows to print (all rows go to a file)")
    s.add_argument("--wait", type=int, default=120, help="max seconds to wait for the search (default 120)")
    s.set_defaults(func=cmd_query)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    c.run(main)
