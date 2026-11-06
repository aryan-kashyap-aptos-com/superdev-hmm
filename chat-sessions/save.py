"""Save chat sessions with one command. Standard library only.

    python chat-sessions/save.py start "Fix refund bug" --goal "Partial refunds double count tax" [--product shop]
    python chat-sessions/save.py note --section "Where we are" --replace --text "Found the cause" --text "Fix in progress"
    python chat-sessions/save.py note --section "Decisions" --text "Use rounding at line level, because the spec says so"
    python chat-sessions/save.py note --section "Next steps" --replace --text "Run the tests" --text "Open the PR"
    python chat-sessions/save.py index          # rebuild INDEX.md: one line per saved session

`note` works on the session named in LATEST.md (or --file). It edits the newest "Session N" block.
`--replace` swaps the whole section; without it the text is added to the end of the section.
Sections: Goal, Where we are, Decisions, Tried and failed, Files and systems touched, Evidence, Open questions, Next steps, Watch out.
Never write secrets. Session files are private to this machine (see .gitignore).
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LATEST = HERE / "LATEST.md"
INDEX = HERE / "INDEX.md"
SKIP = {"LATEST.md", "TEMPLATE.md", "INDEX.md", "README.md"}
EMPTY = "(none yet)"
SECTIONS = ["Goal", "Where we are", "Decisions", "Tried and failed", "Files and systems touched",
            "Evidence", "Open questions", "Next steps", "Watch out"]

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def die(msg):
    sys.exit(f"ERROR: {msg}")


def slug(text):
    words = re.sub(r"[^a-z0-9]+", " ", text.lower()).split()[:4]
    return "-".join(words) or "session"


def block(n, goal):
    parts = [f"## Session {n}", ""]
    for name in SECTIONS:
        parts += [f"### {name}", goal if name == "Goal" else EMPTY, ""]
    return "\n".join(parts)


def latest_file():
    if not LATEST.exists():
        return None
    m = re.search(r"^File:\s*(\S+\.md)\s*$", LATEST.read_text(encoding="utf-8"), re.M)
    return ROOT / m.group(1) if m else None


def set_latest(path):
    rel = path.relative_to(ROOT).as_posix()
    LATEST.write_text(f"# Latest session\n\nFile: {rel}\n", encoding="utf-8")


def cmd_start(args):
    path = HERE / f"{datetime.date.today().isoformat()}-{slug(args.topic)}.md"
    if path.exists():
        text = path.read_text(encoding="utf-8")
        n = len(re.findall(r"^## Session \d+", text, re.M)) + 1
        path.write_text(text.rstrip() + "\n\n" + block(n, args.goal), encoding="utf-8")
        print(f"Added Session {n} to {path.relative_to(ROOT).as_posix()}")
    else:
        head = f"# {args.topic}\n\nDate: {datetime.date.today().isoformat()}\nProject / product: {args.product or 'unknown'}\n\n"
        path.write_text(head + block(1, args.goal), encoding="utf-8")
        print(f"Created {path.relative_to(ROOT).as_posix()}")
    set_latest(path)
    build_index()


def cmd_note(args):
    path = ROOT / args.file if args.file else latest_file()
    if not path or not path.exists():
        die("no session yet. Run: python chat-sessions/save.py start \"<topic>\" --goal \"<goal>\"")
    wanted = next((s for s in SECTIONS if s.lower() == args.section.lower()), None)
    if not wanted:
        die(f"unknown section '{args.section}'. Use one of: {', '.join(SECTIONS)}")
    text = path.read_text(encoding="utf-8")
    starts = [m.start() for m in re.finditer(r"^## Session \d+", text, re.M)]
    if not starts:
        die(f"{path.name} has no '## Session N' block")
    head, last = text[:starts[-1]], text[starts[-1]:]
    m = re.search(rf"^### {re.escape(wanted)}\s*\n(.*?)(?=^### |\Z)", last, re.M | re.S)
    if not m:
        die(f"section '{wanted}' not found in the newest session")
    old = [l for l in m.group(1).strip().splitlines() if l.strip() and l.strip() != EMPTY]
    numbered = wanted == "Next steps"
    new = [t.strip() for t in args.text if t.strip()]
    if not new:
        die("give at least one --text")
    lines = new if args.replace else old + new
    if numbered:
        plain = [re.sub(r"^(\d+\.|-)\s*", "", l) for l in lines]
        lines = [f"{i}. {l}" for i, l in enumerate(plain, 1)]
    else:
        lines = [l if l.startswith("-") else f"- {l}" for l in lines] if wanted != "Goal" else lines
    body = "\n".join(lines) + "\n\n"
    last = last[:m.start(1)] + body + last[m.end(1):]
    path.write_text(head + last, encoding="utf-8")
    print(f"Updated '{wanted}' in {path.relative_to(ROOT).as_posix()}")
    build_index()


def first_line(text, section):
    m = re.search(rf"^### {re.escape(section)}\s*\n(.*?)(?=^### |\Z)", text, re.M | re.S)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        line = re.sub(r"^(\d+\.|-)\s*", "", line.strip())
        if line and line != EMPTY:
            return line
    return ""


def build_index():
    rows = []
    for p in sorted(HERE.glob("*.md"), reverse=True):
        if p.name in SKIP:
            continue
        text = p.read_text(encoding="utf-8")
        title = (re.match(r"#\s+(.+)", text) or [None, p.stem])[1]
        goal = first_line(text.split("## Session")[-1] if "## Session" in text else text, "Goal")
        nxt = first_line(text.split("## Session")[-1] if "## Session" in text else text, "Next steps")
        rows.append(f"| {p.stem[:10]} | [{title}]({p.name}) | {goal} | {nxt} |".replace("\n", " "))
    out = ["# All sessions", "", "Newest first. Open a file only when you need its detail.", "",
           "| Date | Session | Goal | Next step |", "|------|---------|------|-----------|"] + rows
    INDEX.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Save chat sessions.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start", help="create today's session file and point LATEST.md at it")
    s.add_argument("topic")
    s.add_argument("--goal", required=True)
    s.add_argument("--product")
    s.set_defaults(fn=cmd_start)
    n = sub.add_parser("note", help="add to or replace a section of the newest session")
    n.add_argument("--section", required=True)
    n.add_argument("--text", action="append", required=True)
    n.add_argument("--replace", action="store_true")
    n.add_argument("--file", help="session file, relative to the toolkit folder (default: the one in LATEST.md)")
    n.set_defaults(fn=cmd_note)
    sub.add_parser("index", help="rebuild INDEX.md").set_defaults(fn=lambda a: (build_index(), print("Rebuilt INDEX.md")))
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
