"""Search product knowledge (and, with --sessions, saved chat sessions). Standard library only.

    python product-knowledge/search.py "partial refund"
    python product-knowledge/search.py "refund" --product shop --limit 5
    python product-knowledge/search.py "helm timeout" --sessions
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SESSIONS = HERE.parent / "chat-sessions"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def collect(folder, product, with_sessions):
    base = folder / product if product else folder
    if not base.exists():
        sys.exit(f"ERROR: {base} does not exist.")
    files = [p for p in base.rglob("*.md")
             if "templates" not in p.relative_to(folder).parts and p.name != "README.md"]
    if with_sessions and SESSIONS.exists():
        files += [p for p in SESSIONS.glob("*.md") if p.name not in ("TEMPLATE.md", "LATEST.md")]
    docs = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), p.stem)
        status = re.search(r"Status:\s*(\w+)", text)
        docs.append((p, title, status.group(1) if status else "", text))
    return docs


def search_fts(docs, terms, limit):
    db = sqlite3.connect(":memory:")
    db.execute("create virtual table docs using fts5(idx unindexed, title, body, tokenize='porter unicode61')")
    db.executemany("insert into docs values (?, ?, ?)", [(i, d[1], d[3]) for i, d in enumerate(docs)])
    match = " OR ".join(f'"{t}"*' for t in terms)
    rows = db.execute("select idx, snippet(docs, 2, '[', ']', ' ... ', 14) from docs where docs match ? "
                      "order by bm25(docs, 0, 5.0, 1.0) limit ?", (match, limit)).fetchall()
    return [(docs[int(i)], snip.replace("\n", " ")) for i, snip in rows]


def search_plain(docs, terms, limit):
    """Fallback when SQLite has no FTS5: count term hits, titles weigh 5x."""
    scored = []
    for d in docs:
        title, body = d[1].lower(), d[3].lower()
        score = sum(5 * title.count(t) + body.count(t) for t in terms)
        if score:
            pos = min((body.find(t) for t in terms if t in body), default=0)
            scored.append((score, d, d[3][max(0, pos - 60):pos + 100].replace("\n", " ")))
    scored.sort(key=lambda x: -x[0])
    return [(d, snip) for _, d, snip in scored[:limit]]


def main():
    p = argparse.ArgumentParser(description="Search product knowledge.")
    p.add_argument("query", help="words to search for")
    p.add_argument("--product", help="only this product folder")
    p.add_argument("--sessions", action="store_true", help="also search saved chat sessions")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--dir", default=str(HERE), help=argparse.SUPPRESS)   # used by tests
    args = p.parse_args()

    terms = [t.lower() for t in re.findall(r"\w+", args.query)]
    if not terms:
        sys.exit("ERROR: give at least one word to search for.")
    docs = collect(Path(args.dir), args.product, args.sessions)
    if not docs:
        print("No knowledge files yet. Create them with skills/document-product.md.")
        return
    try:
        results = search_fts(docs, terms, args.limit)
    except sqlite3.OperationalError:
        results = search_plain(docs, terms, args.limit)
    if not results:
        print(f"No matches in {len(docs)} files.")
        return
    root = HERE.parent
    for (path, title, status, _), snippet in results:
        try:
            shown = path.relative_to(root).as_posix()
        except ValueError:
            shown = path.as_posix()
        print(f"{shown}  —  {title}" + (f"  [{status}]" if status else ""))
        print(f"    {snippet.strip()[:240]}")
    print(f"\n({len(results)} of {len(docs)} files matched. Open only the files you need.)")


if __name__ == "__main__":
    main()
