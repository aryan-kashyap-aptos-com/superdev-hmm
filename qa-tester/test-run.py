"""Set up and check a QA test run. Standard library only.

    python qa-tester/test-run.py new "Charts library upgrade" --ticket ABC-123 \
        [--site https://example.com] [--login login.aspx] [--user tester] [--password "..."]
        creates qa-tester/runs/<date>-<topic>/ with plan.md to fill in (do this FIRST, before touching the website),
        and makes this run the active one (see `use`, below). Any of --site/--login/--user/--password you give are
        written into the plan's Login section; leave them out and fill in the placeholders by hand instead.
    python qa-tester/test-run.py task <run> "Open the report pages"
        creates tasks/NN-<name>/ inside the run: notes.md, screenshots/, network/. Also makes <run> the active one.
    python qa-tester/test-run.py use <run>
        makes <run> the active one, so the browser connector knows which site and login to use without --site/--run.
    python qa-tester/test-run.py check <run>
        checks the plan, the tasks, and the final summary.md (sections, result words, evidence files)

<run> is the folder name under qa-tester/runs/ (or a path).
Result words: Verified, Issue found, Could not verify, Not tested.

No .env file is needed for website testing: each run's plan.md carries its own site and login, in the Login
section, because different tests target different websites with different accounts. qa-tester/runs/ is never
pushed to git, so a real password in a plan.md stays private.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
TEMPLATES = HERE / "templates"
RESULT_WORDS = ["Verified", "Issue found", "Could not verify", "Not tested"]
OLD_WORDS = re.compile(r"\b(pass|passed|fail|failed)\b|[✅❌✔✖✓✗]", re.I)
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n]{2,}>")
SUMMARY_SECTIONS = ["in plain words", "the issue", "how it should work", "what we tested", "what we found",
                    "what we could not verify", "conclusion"]

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def slug(text, words=5):
    return "-".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split()[:words]) or "run"


def run_dir(name, base=RUNS):
    p = Path(name)
    return p if p.is_absolute() or p.exists() else base / name


LOGIN_ROW = {"site": "Site address", "login": "Sign-in page", "user": "Username", "password": "Password"}


def fill_login(text, **values):
    """Replace the placeholder cell of each given Login row ("site", "login", "user", "password") with its value."""
    for key, value in values.items():
        if value is None:
            continue
        label = LOGIN_ROW[key]
        text = re.sub(rf"(\|\s*{re.escape(label)}\s*\|)[^\n|]*(\|)", lambda m: m.group(1) + f" {value} " + m.group(2), text, count=1)
    return text


def set_active(folder, base):
    (base / "ACTIVE").write_text(folder.name, encoding="utf-8")


def cmd_new(a):
    folder = a.base / f"{datetime.date.today().isoformat()}-{slug(a.topic)}"
    if folder.exists():
        sys.exit(f"ERROR: {folder} already exists. Open its plan.md, or choose another topic.")
    (folder / "tasks").mkdir(parents=True)
    text = (TEMPLATES / "test-plan.md").read_text(encoding="utf-8")
    text = text.replace("# Test plan: <topic>", f"# Test plan: {a.topic}", 1)
    text = text.replace("Date: YYYY-MM-DD", f"Date: {datetime.date.today().isoformat()}", 1)
    if a.ticket:
        text = text.replace("Source: <ticket ID or request>", f"Source: {a.ticket}", 1)
    if a.environment:
        text = text.replace("Environment: <dev / qa / uat / other, in plain words>", f"Environment: {a.environment}", 1)
    text = fill_login(text, site=a.site, login=a.login, user=a.user, password=a.password)
    (folder / "plan.md").write_text(text, encoding="utf-8")
    set_active(folder, a.base)
    print(f"Created {folder} (now the active run)\nNext: fill in the rest of {folder / 'plan.md'} "
          f"(the Login section first, unless you gave it above), then add a task folder for each task:\n"
          f'  python qa-tester/test-run.py task {folder.name} "<what you do>"')


def cmd_use(a):
    folder = run_dir(a.run, a.base)
    if not (folder / "plan.md").exists():
        sys.exit(f"ERROR: {folder} has no plan.md, so it is not a run. Use `new` to create one.")
    set_active(folder, a.base)
    print(f"Active run: {folder.name}")


def cmd_task(a):
    folder = run_dir(a.run, a.base)
    if not (folder / "plan.md").exists():
        sys.exit(f"ERROR: {folder} has no plan.md. Create the run first: python qa-tester/test-run.py new \"<topic>\"")
    n = len([p for p in (folder / "tasks").glob("*") if p.is_dir()]) + 1
    task = folder / "tasks" / f"{n:02d}-{slug(a.name, 4)}"
    (task / "screenshots").mkdir(parents=True)
    (task / "network").mkdir()
    text = (TEMPLATES / "task-notes.md").read_text(encoding="utf-8")
    text = text.replace("# Task: <task name>", f"# Task: {a.name}", 1).replace("Date: YYYY-MM-DD", f"Date: {datetime.date.today().isoformat()}", 1)
    (task / "notes.md").write_text(text, encoding="utf-8")
    set_active(folder, a.base)
    print(f"Created {task}\nUse it with the browser:  --run {folder.name} --task {task.name}")


def table_rows(text, heading):
    """Rows of the first table after a heading, as dicts keyed by lower-case column names."""
    m = re.search(rf"^#{{1,6}}\s+{re.escape(heading)}\s*$(.*?)(?=^#{{1,6}}\s|\Z)", text, re.M | re.S | re.I)
    if not m:
        return []
    lines = [l.strip() for l in m.group(1).splitlines() if l.strip().startswith("|")]
    if len(lines) < 3:
        return []
    cols = [c.strip().lower() for c in lines[0].strip("|").split("|")]
    return [dict(zip(cols, [c.strip() for c in l.strip("|").split("|")])) for l in lines[2:]]


def headings(text):
    return {m.group(1).strip().lower() for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", re.sub(r"```.*?```", "", text, flags=re.S), re.M)}


def plan_password(plan_text):
    """The Login section's password, or None if it is still a placeholder or "none"."""
    m = re.search(r"^##\s+Login\s*$(.*?)(?=^##\s|\Z)", plan_text, re.M | re.S | re.I)
    for line in (m.group(1).splitlines() if m else []):
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() == "password":
            value = "|".join(cells[1:]).strip().strip("`").strip()
            if value and not re.fullmatch(r"<.*>", value) and value.lower() not in ("none", "-", "n/a"):
                return value
    return None


def leaked_password(folder, password):
    """Files (other than plan.md) that contain the plain password. The password must never leave plan.md."""
    hits = []
    for p in folder.rglob("*"):
        if p.is_file() and p.name != "plan.md" and p.suffix.lower() in (".md", ".txt", ".json", ".csv"):
            try:
                if password in p.read_text(encoding="utf-8", errors="ignore"):
                    hits.append(str(p.relative_to(folder)))
            except OSError:
                continue
    return hits


def check(folder):
    errors, warnings = [], []
    plan = folder / "plan.md"
    password = None
    if not plan.exists():
        errors.append("plan.md is missing (write the plan before testing)")
    else:
        text = plan.read_text(encoding="utf-8")
        left = PLACEHOLDER.findall(re.sub(r"```.*?```", "", text, flags=re.S))
        if left:
            errors.append(f"plan.md still has template text ({left[0]} and {len(left) - 1} more)" if len(left) > 1 else f"plan.md still has template text ({left[0]})")
        password = plan_password(text)
    tasks = sorted(p for p in (folder / "tasks").glob("*") if p.is_dir()) if (folder / "tasks").exists() else []
    if not tasks:
        warnings.append("no task folders yet")
    for t in tasks:
        notes = t / "notes.md"
        if not notes.exists():
            errors.append(f"{t.name}: notes.md is missing")
            continue
        body = notes.read_text(encoding="utf-8")
        if PLACEHOLDER.search(body):
            errors.append(f"{t.name}: notes.md still has template text")
        if not any((t / d).glob("*.png") for d in ("screenshots", "pages")) and not list(t.glob("**/*.png")):
            warnings.append(f"{t.name}: no screenshots")
    if password:
        hits = leaked_password(folder, password)
        if hits:
            errors.append("the Login password from plan.md appears in: " + ", ".join(hits) + " (it must never leave plan.md)")
    summary = folder / "summary.md"
    if not summary.exists():
        warnings.append("summary.md is missing (compile it when the tasks are done)")
        return errors, warnings
    text = summary.read_text(encoding="utf-8")
    have = headings(text)
    missing = [h for h in SUMMARY_SECTIONS if h not in have]
    if missing:
        errors.append(f"summary.md is missing section(s): {', '.join(missing)}")
    if PLACEHOLDER.search(re.sub(r"```.*?```", "", text, flags=re.S)):
        errors.append("summary.md still has template text")
    plain = re.search(r"^#{1,6}\s+In plain words\s*$(.*?)(?=^#{1,6}\s|\Z)", text, re.M | re.S | re.I)
    if plain and len(plain.group(1).split()) < 30:
        errors.append("summary.md: 'In plain words' is too short for a first-time reader")
    if OLD_WORDS.search(text):
        errors.append("summary.md uses pass/fail or tick/cross marks. Use: " + ", ".join(RESULT_WORDS))
    rows = table_rows(text, "What we tested")
    if not rows:
        errors.append("summary.md: the 'What we tested' table is empty or missing")
    for r in rows:
        result, ev = r.get("result", ""), r.get("evidence", "")
        word = next((w for w in RESULT_WORDS if result.lower().startswith(w.lower())), None)
        if not word:
            errors.append(f"case '{r.get('id', '?')}': result '{result}' is not one of: {', '.join(RESULT_WORDS)}")
        files = re.findall(r"[\w./-]+\.(?:png|json|md|csv|txt)", ev)
        if word in ("Verified", "Issue found") and not files:
            errors.append(f"case '{r.get('id', '?')}': '{word}' needs evidence (a file in this run's folder)")
        for f in files:
            if not (folder / f).exists():
                errors.append(f"case '{r.get('id', '?')}': evidence file '{f}' does not exist")
    return errors, warnings


def cmd_check(a):
    folder = run_dir(a.run, a.base)
    if not folder.is_dir():
        sys.exit(f"ERROR: {folder} does not exist.")
    errors, warnings = check(folder)
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"warning {w}")
    print(f"\n{len(errors)} errors, {len(warnings)} warnings.")
    sys.exit(1 if errors else 0)


def main():
    p = argparse.ArgumentParser(description="Set up and check a QA test run.")
    p.add_argument("--base", type=Path, default=RUNS, help=argparse.SUPPRESS)   # used by tests
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("topic")
    n.add_argument("--ticket")
    n.add_argument("--environment", help="dev / qa / uat / other, in plain words")
    n.add_argument("--site", help="the site's address, for the Login section")
    n.add_argument("--login", help="the sign-in page, for the Login section")
    n.add_argument("--user", help="the test account's username, for the Login section")
    n.add_argument("--password", help="the test account's password, for the Login section")
    n.set_defaults(fn=cmd_new)
    u = sub.add_parser("use"); u.add_argument("run"); u.set_defaults(fn=cmd_use)
    t = sub.add_parser("task"); t.add_argument("run"); t.add_argument("name"); t.set_defaults(fn=cmd_task)
    k = sub.add_parser("check"); k.add_argument("run"); k.set_defaults(fn=cmd_check)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
