"""Spin up a clean copy of chat-sessions/ for a different product or team, on its own branch.
Standard library only.

    python scaffold-product.py --name billing-team
    python scaffold-product.py --name billing-team --prefix BT --from main

Keeps all the shared tooling (qa-tester/, tools/, connectors/, skills/, rules/) exactly as it is on the
source branch. Only resets chat-sessions/tickets/: real ticket workspaces accumulated on the source branch
are removed, EXAMPLE-000/ (the worked example) stays, and chat-sessions/tickets/README.md is rewritten back
to its generic form. save-session.py's AUTO_PREFIX is changed to --prefix (default: --name, upper-cased,
letters only, first 3 chars) so this product's auto-assigned ticket ids don't look like the source branch's.

Refuses to run with uncommitted changes, or if the branch name already exists. Leaves you checked out on
the new branch with one commit; nothing is pushed.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TICKETS = ROOT / "chat-sessions" / "tickets"
SAVE_SESSION = ROOT / "chat-sessions" / "save-session.py"
KEEP_TICKET_DIRS = {"EXAMPLE-000"}

GENERIC_TICKETS_README = """# Ticket workspaces

Real work product for a Jira ticket: specs, data models, queries, runbooks, test results. **Not** chat notes —
those stay in the dated session files one level up (`chat-sessions/*.md`), which point here for detail.

Flat folders only, named after the ticket id: `tickets/DCOMS-29203-.../` or an auto-assigned `tickets/{prefix}-0001/`.

## How a folder gets here

`chat-sessions/save-session.py start "<topic>" --goal "..." --ticket DCOMS-29203` creates a new workspace here
automatically. Omit `--ticket` for work with no Jira id and one is auto-assigned ({prefix}-NNNN) instead — either
way, put whatever the work actually produced inside the folder: there's no fixed shape, use whatever files it
calls for (a spec, a SQL file, a `runbook/`, `test-results/`, screenshots, a mock UI).

## See also

- `../EXAMPLE.md` — a full worked example, ticket-tied, pointing at `EXAMPLE-000/` below.
- `EXAMPLE-000/` — the dummy workspace that example session points to.
"""


def die(msg):
    sys.exit(f"ERROR: {msg}")


def run(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def git_ok():
    r = run("rev-parse", "--is-inside-work-tree", check=False)
    return r.returncode == 0 and r.stdout.strip() == "true"


def working_tree_clean():
    r = run("status", "--porcelain")
    return not r.stdout.strip()


def branch_exists(name):
    local = run("rev-parse", "--verify", "--quiet", f"refs/heads/{name}", check=False).returncode == 0
    return local


def default_prefix(name):
    letters = re.sub(r"[^A-Za-z]", "", name).upper()
    return (letters[:3] or "SD")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", required=True, help="new branch name, e.g. billing-team")
    p.add_argument("--prefix", help="auto-ticket prefix for this product (default: derived from --name)")
    p.add_argument("--from", dest="base", default="main", help="branch to scaffold from (default: main)")
    args = p.parse_args()

    if not git_ok():
        die("not inside a git repository.")
    if not working_tree_clean():
        die("working tree has uncommitted changes. Commit or stash first - scaffolding needs a clean start.")
    if branch_exists(args.name):
        die(f"branch '{args.name}' already exists locally. Pick a different --name or remove it first.")
    if run("rev-parse", "--verify", "--quiet", f"refs/heads/{args.base}", check=False).returncode != 0:
        die(f"base branch '{args.base}' does not exist locally. Fetch it first, or pass a different --from.")

    prefix = args.prefix or default_prefix(args.name)

    print(f"Creating branch '{args.name}' from '{args.base}'...")
    run("checkout", "-b", args.name, args.base)

    removed = []
    if TICKETS.is_dir():
        for d in sorted(TICKETS.iterdir()):
            if d.is_dir() and d.name not in KEEP_TICKET_DIRS:
                run("rm", "-r", "-q", str(d.relative_to(ROOT)))
                removed.append(d.name)

    tickets_readme = TICKETS / "README.md"
    tickets_readme.write_text(GENERIC_TICKETS_README.format(prefix=prefix), encoding="utf-8")
    run("add", str(tickets_readme.relative_to(ROOT)))

    if SAVE_SESSION.exists():
        text = SAVE_SESSION.read_text(encoding="utf-8")
        new_text, n = re.subn(r'^AUTO_PREFIX = ".*"$', f'AUTO_PREFIX = "{prefix}"', text, flags=re.M)
        if n:
            SAVE_SESSION.write_text(new_text, encoding="utf-8")
            run("add", str(SAVE_SESSION.relative_to(ROOT)))
        else:
            print("WARNING: could not find AUTO_PREFIX line in save-session.py; left unchanged.", file=sys.stderr)

    run("commit", "-m", f"Scaffold chat-sessions for {args.name} (auto-ticket prefix {prefix})")

    print(f"\nDone. Branch '{args.name}' checked out, auto-ticket prefix '{prefix}'.")
    if removed:
        print(f"Removed ticket workspaces (were specific to '{args.base}'): {', '.join(removed)}")
    print("Nothing pushed. When ready: git push -u origin", args.name)


if __name__ == "__main__":
    main()
