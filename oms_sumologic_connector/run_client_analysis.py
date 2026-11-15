from pathlib import Path
from search import run_query


def q(template: str, client: str) -> str:
    return Path(f"queries/{template}.txt").read_text().replace("{client}", client).strip()


def run(name: str, client: str, tfrom: str, label: str) -> list:
    fields, rows, status = run_query(
        q(name, client),
        time_from=tfrom,
        time_to="now",
        result_type="records",
        max_rows=50,
    )
    print(f"[{label}] records={len(rows)} msgs={status.get('messageCount')}")
    cols = fields or (list(rows[0].keys()) if rows else [])
    print("\t".join(cols))
    for row in rows:
        print("\t".join(str(row.get(c, "")) for c in cols))
    print()
    return rows


_, clients, _ = run_query(
    "_sourceCategory=DCOMS/API/PROD/* | count by _sourceCategory | sort by _count desc | limit 8",
    time_from="-7d",
    time_to="now",
    result_type="records",
    max_rows=8,
)
print("[active prod API clients - 7d]")
for row in clients:
    print(row.get("_sourcecategory"), row.get("_count"))
print()

run("health", "jmc", "-24h", "JML/jmc health 24h")
run("api_distinct", "jmc", "-7d", "JML/jmc distinct APIs 7d")

# JMC uses legacy OMS/api, not DCOMS/API/PROD/jmc
legacy_distinct = "_collector=OMS-jmc* AND _sourceCategory=OMS/api | parse regex field=_raw \"\\\"(?<method>GET|POST|PUT|DELETE|PATCH)[^\\\"]* (?<path>/[^\\\"\\\\s?]+)\" nodrop | count_distinct(path)"
_, rows, status = run_query(legacy_distinct, time_from="-7d", time_to="now", result_type="records")
print("[JML/jmc distinct APIs 7d via OMS/api]", rows)
print()

legacy_health = '_collector=OMS-jmc* AND _sourceCategory=OMS/api | where _loglevel in ("ERROR","WARN") | count by _loglevel'
_, rows, _ = run_query(legacy_health, time_from="-24h", time_to="now", result_type="records")
print("[JML/jmc API health 24h via OMS/api]")
for row in rows:
    print(row)
