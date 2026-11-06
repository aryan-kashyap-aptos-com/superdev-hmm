# Scenarios

Test cases saved as files, so they can be replayed with one command, live in the runner panel, without the AI working out each step again.

```
python connectors/browser/run.py play qa-tester/scenarios/<name>.json --run <run folder> --task <task folder>
```

- Start from `qa-tester/templates/scenario.json`. The format, every action, and every check are described in `connectors/browser/GUIDE.md`.
- Use paths, not full addresses (`"url": "reports/sales.aspx"`): they are resolved against the site's address from the environments list.
- Passwords never go in a scenario. Write `"value": "$password"` (or `"$user"`): it is read from the Login section
  of the run's `plan.md` at the moment the scenario runs, and is never shown in the panel, a log, or a report.
- Files here are **private** (gitignored): they name internal pages. Only this README is pushed.
- When a scenario passes reliably, it becomes a regression check: replay it after every release.
