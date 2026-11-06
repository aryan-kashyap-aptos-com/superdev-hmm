"""Check a product's knowledge pages. Standard library only.

    python product-knowledge/check-pages.py <product>
    python product-knowledge/check-pages.py <product> --strict     # warnings also fail

Errors (exit code 1): broken links, template text left in, missing required sections,
verified pages without evidence, coverage map rows that point to missing pages.
Warnings: orphan pages, long pages, pages with no example or diagram.
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

MAX_LINES = 200
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n]{2,}>")   # <Product name>, <one sentence ...>
CODE_BLOCK = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")

# Sections every page of that kind must have (heading text, case-insensitive).
REQUIRED = {
    "overview": ["in plain words", "the big picture", "the parts", "how to read these docs"],
    "system": ["in plain words", "where it fits", "how it works", "what can go wrong", "evidence"],
    "journey": ["in plain words", "the example we follow", "the path", "step by step, with the example"],
    "feature": ["in plain words", "how it works", "business rules", "scenarios"],
    "scenario": ["given", "when", "then", "evidence"],
}
STATUS_KINDS = {"system", "journey", "feature", "scenario", "overview"}


def kind_of(rel):
    parts = rel.parts
    if rel.name == "overview.md":
        return "overview"
    return {"systems": "system", "journeys": "journey", "features": "feature", "scenarios": "scenario"}.get(parts[0])


def strip_code(text):
    return INLINE_CODE.sub("", CODE_BLOCK.sub("", text))


def headings(text):
    return {m.group(1).strip().lower() for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", strip_code(text), re.M)}


def section(text, name):
    m = re.search(rf"^#{{1,6}}\s+{re.escape(name)}\s*$(.*?)(?=^#{{1,6}}\s|\Z)", text, re.M | re.S | re.I)
    return m.group(1).strip() if m else ""


def read_map(path):
    """Rows of the Coverage table in MAP.md as dicts."""
    text = path.read_text(encoding="utf-8")
    rows = []
    for line in section(text, "Coverage").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and not set("".join(cells)) <= set("-: "):
            rows.append(dict(zip(["area", "kind", "level", "page", "status"], cells)))
    return [r for r in rows if r["area"].lower() != "area"]


def lint(product_dir):
    errors, warnings = [], []
    pages = sorted(p for p in product_dir.rglob("*.md"))
    rels = {p.relative_to(product_dir) for p in pages}
    linked = set()

    for page in pages:
        rel = page.relative_to(product_dir)
        text = page.read_text(encoding="utf-8")
        body = strip_code(text)
        name = rel.as_posix()

        for target in LINK.findall(body):
            if re.match(r"[a-z]+:|#|mailto:", target):
                continue
            path = target.split("#")[0]
            if not path:
                continue
            resolved = (page.parent / path).resolve()
            try:
                linked.add(resolved.relative_to(product_dir.resolve()))
            except ValueError:
                pass
            if not resolved.exists():
                errors.append(f"{name}: broken link to '{target}'")

        left = PLACEHOLDER.findall(body)
        if left:
            errors.append(f"{name}: template text left in ({left[0]}" + (f" and {len(left) - 1} more" if len(left) > 1 else "") + ")")

        kind = kind_of(rel)
        if kind in REQUIRED:
            have = headings(text)
            missing = [h for h in REQUIRED[kind] if h not in have]
            if missing:
                errors.append(f"{name}: missing section(s): {', '.join(missing)}")
        if kind in STATUS_KINDS:
            m = re.search(r"Status:\s*(draft|verified|outdated)\b", text)
            if not m:
                errors.append(f"{name}: missing 'Status: draft | verified | outdated'")
            elif m.group(1) == "verified" and kind in ("system", "journey", "feature", "scenario"):
                evidence = section(text, "Evidence")
                if not re.sub(r"[-*\s]|<[^>]*>", "", evidence):
                    errors.append(f"{name}: Status is verified but the Evidence section is empty")
            if kind in ("system", "journey", "overview", "feature") and "in plain words" in headings(text):
                plain = section(text, "In plain words")
                if len(plain.split()) < 15:
                    errors.append(f"{name}: 'In plain words' is too short to explain anything")

        if kind in ("overview", "system", "journey") and "```" not in text:
            warnings.append(f"{name}: no diagram (the writing guide asks for one)")
        if kind in ("system", "journey", "feature") and not re.search(r"\*\*Example:?\*\*|^#+\s+.*example", text, re.I | re.M):
            warnings.append(f"{name}: no concrete example")
        if len(text.splitlines()) > MAX_LINES:
            warnings.append(f"{name}: {len(text.splitlines())} lines; split pages over {MAX_LINES}")

    structural = {Path("MAP.md"), Path("glossary.md"), Path("gaps.md"), Path("overview.md")}
    for rel in sorted(rels - linked - structural):
        warnings.append(f"{rel.as_posix()}: no page links to it (orphan)")

    map_path = product_dir / "MAP.md"
    if map_path.exists():
        for row in read_map(map_path):
            status = row["status"].lower()
            if status not in ("todo", "in-progress", "done"):
                errors.append(f"MAP.md: '{row['area']}' has status '{row['status']}' (use todo, in-progress, done)")
            elif status != "todo" and Path(row["page"]) not in rels:
                errors.append(f"MAP.md: '{row['area']}' is {status} but page '{row['page']}' does not exist")
    else:
        warnings.append("MAP.md: missing. Plan with the user first (skills/document-product.md, Step 0)")
    if not (product_dir / "glossary.md").exists():
        warnings.append("glossary.md: missing")
    return errors, warnings, len(pages)


def main():
    p = argparse.ArgumentParser(description="Check product knowledge pages.")
    p.add_argument("product", help="product folder name inside product-knowledge/")
    p.add_argument("--strict", action="store_true", help="warnings also fail")
    p.add_argument("--dir", default=str(HERE), help=argparse.SUPPRESS)   # used by tests
    args = p.parse_args()

    product_dir = Path(args.dir) / args.product
    if not product_dir.is_dir():
        sys.exit(f"ERROR: {product_dir} does not exist.")
    errors, warnings, count = lint(product_dir)
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"warning {w}")
    print(f"\n{count} pages checked: {len(errors)} errors, {len(warnings)} warnings.")
    sys.exit(1 if errors or (args.strict and warnings) else 0)


if __name__ == "__main__":
    main()
