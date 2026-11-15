#!/usr/bin/env python3
"""MD Reader - a local, private viewer for Markdown files.

Add one or many .md files, reorder them in the sidebar, read them rendered
(not raw), and export the current file or the whole stack to Word or PDF.
Everything lives under tools/md-reader/library/ on this machine only; the
server binds to 127.0.0.1 and never calls out anywhere.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

from exporter import export_docx, export_pdf, render_html

ROOT = Path(__file__).resolve().parent
LIBRARY = ROOT / "library"
META_PATH = LIBRARY / "_order.json"
STATIC = ROOT / "static"
LIBRARY.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=None)


def _load_meta() -> list[dict]:
    if not META_PATH.exists():
        return []
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def _save_meta(entries: list[dict]) -> None:
    META_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _entry_path(entry_id: str) -> Path:
    return LIBRARY / f"{entry_id}.md"


@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.get("/static/<path:name>")
def static_files(name: str):
    return send_from_directory(STATIC, name)


@app.get("/api/files")
def list_files():
    return jsonify(_load_meta())


@app.post("/api/files")
def add_files():
    entries = _load_meta()
    added = []
    for f in request.files.getlist("files"):
        name = f.filename or "untitled.md"
        entry_id = uuid.uuid4().hex[:12]
        f.save(_entry_path(entry_id))
        entry = {"id": entry_id, "name": name}
        entries.append(entry)
        added.append(entry)
    _save_meta(entries)
    return jsonify({"added": added, "files": entries})


@app.put("/api/files/order")
def reorder_files():
    order = request.get_json(force=True).get("order", [])
    entries = {e["id"]: e for e in _load_meta()}
    reordered = [entries[i] for i in order if i in entries]
    _save_meta(reordered)
    return jsonify(reordered)


@app.delete("/api/files/<entry_id>")
def delete_file(entry_id: str):
    entries = [e for e in _load_meta() if e["id"] != entry_id]
    _save_meta(entries)
    path = _entry_path(entry_id)
    if path.exists():
        path.unlink()
    return jsonify(entries)


@app.get("/api/files/<entry_id>/html")
def file_html(entry_id: str):
    path = _entry_path(entry_id)
    if not path.exists():
        return jsonify({"error": "not found"}), 404
    text = path.read_text(encoding="utf-8", errors="replace")
    return jsonify({"html": render_html(text)})


def _resolve_ids(ids: list[str] | None) -> list[dict]:
    entries = _load_meta()
    if not ids:
        return entries
    by_id = {e["id"]: e for e in entries}
    return [by_id[i] for i in ids if i in by_id]


@app.post("/api/export/pdf")
def export_pdf_route():
    body = request.get_json(force=True) or {}
    entries = _resolve_ids(body.get("ids"))
    if not entries:
        return jsonify({"error": "no files selected"}), 400
    docs = [(e["name"], _entry_path(e["id"]).read_text(encoding="utf-8", errors="replace")) for e in entries]
    out_path = ROOT / "exports" / f"{uuid.uuid4().hex[:8]}.pdf"
    out_path.parent.mkdir(exist_ok=True)
    export_pdf(docs, out_path)
    return send_file(out_path, as_attachment=True, download_name=body.get("filename", "notes.pdf"))


@app.post("/api/export/docx")
def export_docx_route():
    body = request.get_json(force=True) or {}
    entries = _resolve_ids(body.get("ids"))
    if not entries:
        return jsonify({"error": "no files selected"}), 400
    docs = [(e["name"], _entry_path(e["id"]).read_text(encoding="utf-8", errors="replace")) for e in entries]
    out_path = ROOT / "exports" / f"{uuid.uuid4().hex[:8]}.docx"
    out_path.parent.mkdir(exist_ok=True)
    export_docx(docs, out_path)
    return send_file(out_path, as_attachment=True, download_name=body.get("filename", "notes.docx"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5151, debug=False)
