"""Markdown -> HTML / PDF / Word conversion for the MD reader."""
from __future__ import annotations

from pathlib import Path

import markdown as md_lib
from bs4 import BeautifulSoup, NavigableString
from docx import Document
from docx.shared import Pt

MD_EXTENSIONS = ["fenced_code", "tables", "sane_lists", "toc"]

PAGE_CSS = """
@import url('https://fonts.googleapis.com');
"""

HTML_WRAP = """<!doctype html><html><head><meta charset="utf-8"><style>
body{{font:14px/1.65 -apple-system,"Segoe UI",Arial,sans-serif;color:#1d1d1f;max-width:760px;margin:0 auto;padding:48px 24px}}
h1,h2,h3,h4{{font-weight:600;letter-spacing:-.01em;margin:1.4em 0 .5em}}
h1{{font-size:28px;border-bottom:1px solid #e5e5e7;padding-bottom:.3em}}
h2{{font-size:21px}}
h3{{font-size:17px}}
code{{font-family:ui-monospace,Menlo,Consolas,monospace;background:#f0f0f3;padding:1px 6px;border-radius:5px;font-size:.88em}}
pre{{background:#f5f5f7;border:1px solid #e5e5e7;border-radius:10px;padding:14px 16px;overflow:auto}}
pre code{{background:none;padding:0}}
blockquote{{margin:0;padding:4px 16px;border-left:3px solid #c7c7cc;color:#4a4a4e}}
table{{border-collapse:collapse;width:100%;margin:1em 0}}
th,td{{border:1px solid #e5e5e7;padding:6px 10px;text-align:left;font-size:13px}}
.doc-break{{page-break-before:always}}
.doc-title{{font-size:13px;color:#8e8e93;text-transform:uppercase;letter-spacing:.06em;margin-top:2.2em}}
</style></head><body>{body}</body></html>"""


def render_html(markdown_text: str) -> str:
    return md_lib.markdown(markdown_text, extensions=MD_EXTENSIONS)


def _combined_html(docs: list[tuple[str, str]]) -> str:
    parts = []
    for i, (name, text) in enumerate(docs):
        cls = "doc-break" if i > 0 else ""
        parts.append(f'<div class="{cls}"><p class="doc-title">{name}</p>{render_html(text)}</div>')
    return HTML_WRAP.format(body="".join(parts))


def export_pdf(docs: list[tuple[str, str]], out_path: Path) -> Path:
    from playwright.sync_api import sync_playwright

    html = _combined_html(docs)
    tmp_html = out_path.with_suffix(".tmp.html")
    tmp_html.write_text(html, encoding="utf-8")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(tmp_html.resolve().as_uri())
            page.pdf(path=str(out_path), format="A4", print_background=True,
                     margin={"top": "0.4in", "bottom": "0.4in", "left": "0.4in", "right": "0.4in"})
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)
    return out_path


def _add_inline(paragraph, node) -> None:
    for child in node.children:
        if isinstance(child, NavigableString):
            paragraph.add_run(str(child))
        elif child.name in ("strong", "b"):
            run = paragraph.add_run(child.get_text())
            run.bold = True
        elif child.name in ("em", "i"):
            run = paragraph.add_run(child.get_text())
            run.italic = True
        elif child.name == "code":
            run = paragraph.add_run(child.get_text())
            run.font.name = "Consolas"
        elif child.name == "a":
            paragraph.add_run(child.get_text())
        else:
            paragraph.add_run(child.get_text())


def _add_node(document: Document, node) -> None:
    name = getattr(node, "name", None)
    if name is None:
        return
    if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        document.add_heading(node.get_text(), level=int(name[1]))
    elif name == "p":
        _add_inline(document.add_paragraph(), node)
    elif name in ("ul", "ol"):
        style = "List Bullet" if name == "ul" else "List Number"
        for li in node.find_all("li", recursive=False):
            _add_inline(document.add_paragraph(style=style), li)
    elif name == "pre":
        code_text = node.get_text()
        p = document.add_paragraph()
        run = p.add_run(code_text)
        run.font.name = "Consolas"
        run.font.size = Pt(9.5)
    elif name == "blockquote":
        _add_inline(document.add_paragraph(style="Intense Quote"), node)
    elif name == "table":
        rows = node.find_all("tr")
        if rows:
            cols = len(rows[0].find_all(["td", "th"]))
            table = document.add_table(rows=0, cols=cols)
            table.style = "Light Grid"
            for tr in rows:
                cells = tr.find_all(["td", "th"])
                row = table.add_row().cells
                for i, cell in enumerate(cells):
                    row[i].text = cell.get_text()
    elif name == "hr":
        document.add_paragraph("―" * 20)
    else:
        for child in node.find_all(recursive=False):
            _add_node(document, child)


def export_docx(docs: list[tuple[str, str]], out_path: Path) -> Path:
    document = Document()
    for i, (name, text) in enumerate(docs):
        if i > 0:
            document.add_page_break()
        heading = document.add_paragraph()
        run = heading.add_run(name)
        run.bold = True
        run.font.size = Pt(10)
        soup = BeautifulSoup(render_html(text), "html.parser")
        for node in soup.find_all(recursive=False):
            _add_node(document, node)
    document.save(out_path)
    return out_path
