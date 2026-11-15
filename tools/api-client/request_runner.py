"""Resolve {{variables}} against an environment + collection variables, then send the request.

No pre-request/test script execution (see README) - this covers plain variable
substitution and the common Postman auth types (basic, bearer, apikey).
"""
from __future__ import annotations

import re
import time
from typing import Any

import requests

VAR_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def substitute(text: str, variables: dict[str, str]) -> str:
    if not text:
        return text

    def repl(match: re.Match) -> str:
        key = match.group(1)
        return str(variables.get(key, match.group(0)))

    return VAR_RE.sub(repl, text)


def _apply_auth(auth: dict, headers: dict, params: dict, variables: dict[str, str]) -> None:
    kind = auth.get("type", "noauth")
    if kind == "bearer":
        token = substitute(auth.get("token", ""), variables)
        headers["Authorization"] = f"Bearer {token}"
    elif kind == "basic":
        import base64

        user = substitute(auth.get("username", ""), variables)
        pwd = substitute(auth.get("password", ""), variables)
        token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    elif kind == "apikey":
        key = substitute(auth.get("key", ""), variables)
        value = substitute(auth.get("value", ""), variables)
        where = auth.get("in", "header")
        if where == "query":
            params[key] = value
        else:
            headers[key] = value


def build_request(req: dict, variables: dict[str, str]) -> dict:
    url = substitute(req.get("url", ""), variables)
    headers = {
        h["key"]: substitute(h["value"], variables)
        for h in req.get("headers", [])
        if h.get("key") and not h.get("disabled")
    }
    params = {
        q["key"]: substitute(q["value"], variables)
        for q in req.get("query", [])
        if q.get("key") and not q.get("disabled")
    }
    _apply_auth(req.get("auth", {}), headers, params, variables)

    body_spec = req.get("body", {"mode": "none"})
    data = None
    json_body = None
    if body_spec.get("mode") == "raw":
        raw = substitute(body_spec.get("raw", ""), variables)
        if body_spec.get("language") == "json":
            import json as _json

            try:
                json_body = _json.loads(raw) if raw.strip() else None
            except ValueError:
                data = raw
        else:
            data = raw
    elif body_spec.get("mode") == "urlencoded":
        data = {
            r["key"]: substitute(r["value"], variables)
            for r in body_spec.get("rows", [])
            if r.get("key") and not r.get("disabled")
        }

    return {
        "method": req.get("method", "GET"),
        "url": url,
        "headers": headers,
        "params": params,
        "json": json_body,
        "data": data,
    }


def send(req: dict, variables: dict[str, str], timeout: float = 30.0, verify: bool = True) -> dict:
    built = build_request(req, variables)
    started = time.perf_counter()
    if not verify:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        resp = requests.request(
            built["method"], built["url"],
            headers=built["headers"], params=built["params"],
            json=built["json"], data=built["data"],
            timeout=timeout, verify=verify,
        )
    except requests.RequestException as exc:
        return {
            "ok": False, "error": str(exc), "request": built,
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
        }
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    try:
        body_json: Any = resp.json()
        pretty = None
    except ValueError:
        body_json = None
        pretty = resp.text
    return {
        "ok": True,
        "status": resp.status_code,
        "reason": resp.reason,
        "headers": dict(resp.headers),
        "body_json": body_json,
        "body_text": pretty if pretty is not None else None,
        "elapsed_ms": elapsed_ms,
        "size_bytes": len(resp.content),
        "request": {**built, "resolved_url": resp.url},
    }
