# Connector: sumologic

## When to use

To search application and infrastructure logs in Sumo Logic: find errors, count events, trace a request, check what happened at a given time.

## Setup

1. Create an access ID and key in Sumo Logic (Preferences → Access Keys).
2. Copy `.env.example` to `.env` and fill it in.
3. `python connectors/sumologic/run.py test`

## Commands

| Command | What it does |
|---------|--------------|
| `test` | Checks the access key. |
| `saved` | Lists saved queries in `connectors/sumologic/queries/`. |
| `query "<query>" [--from -15m] [--to now] [--limit 50]` | Runs a search and prints the results. |
| `query @name ...` | Runs the saved query `queries/name.txt`. |

Time values: `now`, `-15m`, `-2h`, `-1d`, `-1w`, or `2026-11-01T10:00:00` (local time).

If the query has an aggregate (`count`, `timeslice`, ...), the script prints the aggregate rows.
Otherwise it prints messages: time, source category, host, and raw text.

## Rules

1. Start narrow: a short time range (`--from -15m` or `-1h`) and a `_sourceCategory` filter.
2. Count first, then read. Example: add `| count by _sourcecategory` to see where the matches are.
3. Run at most 3 queries for one question. If you have no answer after 3, tell the user what you found and ask how to narrow it.
4. Add `| limit 100` to message searches.
5. Log lines can hold personal data and secrets. Do not copy them into knowledge or session files.
6. Save useful queries as `queries/<name>.txt` so the next session can reuse them.

## Examples

```
python connectors/sumologic/run.py query "_sourceCategory=prod/api error | count by _sourcehost" --from -1h
python connectors/sumologic/run.py query "_sourceCategory=prod/api \"order 1042\" | limit 50" --from -1d
python connectors/sumologic/run.py query @errors-by-source --from -4h
```
