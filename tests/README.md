# Tests

`selftest.py` checks the whole toolkit **without network access and without passwords**. Run it after every change:

```
python tests/selftest.py
```

Exit code 0 means every check passed. A failed check prints its name and what it saw.

## What it covers

| Area | Examples of what is checked |
|------|-----------------------------|
| Shared connector code | `.env` reading, tables and file output, read-only SQL guard, HTML and markdown conversion |
| Read-only guards | `ec2-ssm` allows `df -h` but blocks `rm`, `;`, `>` and PowerShell commands that change things |
| Connectors | Each HTTP connector against a local mock server; database tunnel and engine logic; log time ranges |
| Browser | Allowed sites, private site list, sign-in page setting, element naming, state wording, secret redaction |
| Scenarios | File validation, plain-sentence step names, count rules, `$SETTING` values, the template file |
| QA runs | `test-run.py` new, task, check: template text, result words, evidence files, too-short summaries |
| Knowledge and sessions | Search ranking, the page checker, `save-session.py` |

## Adding checks

Write a `test_<area>()` function that calls `check("<what should hold>", condition, detail)`, and add it to the list in `main()`.
Use temporary folders for files and the mock server for HTTP. Never call a real system from here.
