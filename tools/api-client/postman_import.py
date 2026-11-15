"""Parse Postman v2.x collection and environment exports into a flat internal model.

Deliberately does not execute pre-request/test scripts (see tools/api-client/README.md) -
it imports the request shape (method, url, headers, params, body, auth) and leaves
`{{variables}}` for request_runner.py to substitute from the active environment.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return value.get("raw", "")
    return value or ""


def _parse_url(url: Any) -> tuple[str, list[dict]]:
    if isinstance(url, str):
        return url, []
    raw = url.get("raw", "")
    query = [
        {"key": q.get("key", ""), "value": q.get("value", ""), "disabled": bool(q.get("disabled"))}
        for q in url.get("query", []) or []
    ]
    return raw, query


def _parse_body(body: dict | None) -> dict:
    if not body:
        return {"mode": "none"}
    mode = body.get("mode", "none")
    if mode == "raw":
        return {"mode": "raw", "raw": body.get("raw", ""), "language": (body.get("options", {}).get("raw", {}) or {}).get("language", "json")}
    if mode in ("urlencoded", "formdata"):
        rows = [
            {"key": r.get("key", ""), "value": r.get("value", ""), "disabled": bool(r.get("disabled"))}
            for r in body.get(mode, []) or []
        ]
        return {"mode": mode, "rows": rows}
    return {"mode": mode}


def _parse_auth(auth: dict | None) -> dict:
    if not auth:
        return {"type": "inherit"}
    kind = auth.get("type", "noauth")
    fields = {}
    for item in auth.get(kind, []) or []:
        fields[item.get("key")] = item.get("value")
    return {"type": kind, **fields}


def _walk(items: list[dict], folder_path: list[str], out: list[dict]) -> None:
    for item in items:
        if "item" in item:
            _walk(item["item"], folder_path + [item.get("name", "")], out)
            continue
        req = item.get("request", {})
        url_raw, query = _parse_url(req.get("url", ""))
        out.append({
            "id": uuid.uuid4().hex[:12],
            "name": item.get("name", "Untitled"),
            "folder": " / ".join(folder_path),
            "method": req.get("method", "GET"),
            "url": url_raw,
            "query": query,
            "headers": [
                {"key": h.get("key", ""), "value": h.get("value", ""), "disabled": bool(h.get("disabled"))}
                for h in req.get("header", []) or []
            ],
            "body": _parse_body(req.get("body")),
            "auth": _parse_auth(req.get("auth")),
            "description": _text(req.get("description", "")),
        })


def parse_collection(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    requests_out: list[dict] = []
    _walk(data.get("item", []), [], requests_out)
    variables = {
        v.get("key"): v.get("value", "")
        for v in data.get("variable", []) or []
        if v.get("key")
    }
    return {
        "id": uuid.uuid4().hex[:12],
        "name": data.get("info", {}).get("name") or Path(path).stem,
        "source_file": Path(path).name,
        "variables": variables,
        "requests": requests_out,
    }


def parse_environment(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    values = {
        v.get("key"): v.get("value", "")
        for v in data.get("values", []) or []
        if v.get("key") and v.get("enabled", True)
    }
    return {
        "id": uuid.uuid4().hex[:12],
        "name": data.get("name") or Path(path).stem,
        "source_file": Path(path).name,
        "values": values,
    }
