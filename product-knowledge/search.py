"""Search product knowledge (and, with --sessions, saved chat sessions). Standard library only.

    python product-knowledge/search.py "partial refund"
    python product-knowledge/search.py "refund" --product shop --limit 5
    python product-knowledge/search.py "helm timeout" --sessions
    python product-knowledge/search.py --related portfolio/overview.md

Reads both `product-knowledge/` (public, example-only) and the private, gitignored
`product-knowledge-local/` (real sites, real systems) — same layout, same rules, searched together.
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SESSIONS = HERE.parent / "chat-sessions"
LOCAL = HERE.parent / "product-knowledge-local"
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+\.md)[^)]*\)")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def _files(root, product):
    base = root / product if product else root
    if not base.exists():
        return []
    return [p for p in base.rglob("*.md")
            if "templates" not in p.relative_to(root).parts and p.name != "README.md"]


def collect(folder, product, with_sessions):
    files = _files(folder, product)
    if not files and not LOCAL.exists():
        sys.exit(f"ERROR: {folder / product if product else folder} does not exist.")
    files += _files(LOCAL, product)
    if with_sessions and SESSIONS.exists():
        files += [p for p in SESSIONS.glob("*.md") if p.name not in ("TEMPLATE.md", "LATEST.md")]
    docs = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), p.stem)
        status = re.search(r"Status:\s*(\w+)", text)
        docs.append((p, title, status.group(1) if status else "", text))
    return docs


def build_graph(docs):
    """One-hop relations, free: every page already links related pages with relative
    Markdown links (product-knowledge/README.md, Rule 3). No new syntax to maintain."""
    by_path = {d[0].resolve(): d for d in docs}
    links_out = {}
    for path, _, _, text in docs:
        src = path.resolve()
        targets = []
        for m in LINK_RE.finditer(text):
            target = (path.parent / m.group(1)).resolve()
            if target in by_path and target != src and target not in targets:
                targets.append(target)
        links_out[src] = targets
    links_in = {p: [] for p in by_path}
    for src, targets in links_out.items():
        for t in targets:
            if src not in links_in[t]:
                links_in[t].append(src)
    return by_path, links_out, links_in


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


def _show(path, title, status, root):
    try:
        shown = path.relative_to(root).as_posix()
    except ValueError:
        shown = path.as_posix()
    return f"{shown}  —  {title}" + (f"  [{status}]" if status else "")


def main():
    p = argparse.ArgumentParser(description="Search product knowledge.")
    p.add_argument("query", nargs="?", help="words to search for")
    p.add_argument("--product", help="only this product folder")
    p.add_argument("--sessions", action="store_true", help="also search saved chat sessions")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--related", metavar="PATH_OR_WORDS",
                    help="show what links to, and is linked from, a page "
                         "(a path like portfolio/overview.md, or words to find it by)")
    p.add_argument("--dir", default=str(HERE), help=argparse.SUPPRESS)   # used by tests
    args = p.parse_args()

    base = Path(args.dir)
    root = base.parent
    docs = collect(base, args.product, args.sessions)
    if not docs:
        print("No knowledge files yet. Create them with skills/document-product.md.")
        return

    if args.related:
        by_path, links_out, links_in = build_graph(docs)
        target = (root / args.related).resolve()
        if target not in by_path:
            terms = [t.lower() for t in re.findall(r"\w+", args.related)]
            hit = next(iter(search_plain(docs, terms, 1) or search_fts(docs, terms, 1)), None)
            if not hit:
                sys.exit(f"ERROR: no page matches '{args.related}'.")
            target = hit[0][0].resolve()
        _, title, status, _ = by_path[target]
        print("Page: " + _show(target, title, status, root))
        print("\nLinks to:")
        for t in links_out.get(target, []) or []:
            print("  " + _show(t, by_path[t][1], by_path[t][2], root))
        if not links_out.get(target):
            print("  (none)")
        print("\nLinked from:")
        for s in links_in.get(target, []) or []:
            print("  " + _show(s, by_path[s][1], by_path[s][2], root))
        if not links_in.get(target):
            print("  (none)")
        return

    if not args.query:
        sys.exit("ERROR: give words to search for, or use --related.")
    terms = [t.lower() for t in re.findall(r"\w+", args.query)]
    if not terms:
        sys.exit("ERROR: give at least one word to search for.")
    try:
        results = search_fts(docs, terms, args.limit)
    except sqlite3.OperationalError:
        results = search_plain(docs, terms, args.limit)
    if not results:
        print(f"No matches in {len(docs)} files.")
        return
    for (path, title, status, _), snippet in results:
        print(_show(path, title, status, root))
        print(f"    {snippet.strip()[:240]}")
    print(f"\n({len(results)} of {len(docs)} files matched. Open only the files you need.)")


if __name__ == "__main__":
    main()
