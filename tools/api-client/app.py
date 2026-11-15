#!/usr/bin/env python3
"""A local, Postman-shaped API client.

Import collections and environments exported from Postman, send requests with
{{variable}} substitution, and capture a screenshot of the request/response as
evidence - the same kind of visual proof qa-tester already produces for UI
steps, now available for API steps too. Binds to 127.0.0.1 only; requests you
send go wherever you point them, nothing else talks to the network.

Scripts: pre-request/test JS from the Postman collection are NOT executed
(see README.md) - this is plain variable substitution + send + view for v1.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

import evidence
import postman_import
import request_runner

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STATIC = ROOT / "static"
COLLECTIONS_PATH = DATA / "collections.json"
ENVIRONMENTS_PATH = DATA / "environments.json"
STATE_PATH = DATA / "state.json"
DATA.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=None)


def _load(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def _collections() -> list[dict]:
    return _load(COLLECTIONS_PATH, [])


def _environments() -> list[dict]:
    return _load(ENVIRONMENTS_PATH, [])


def _state() -> dict:
    return _load(STATE_PATH, {"active_env": None})


@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.get("/static/<path:name>")
def static_files(name: str):
    return send_from_directory(STATIC, name)


# ---- collections ----

@app.get("/api/collections")
def list_collections():
    return jsonify(_collections())


@app.post("/api/collections/import")
def import_collections():
    cols = _collections()
    added = []
    for f in request.files.getlist("files"):
        tmp = DATA / f"_upload_{uuid.uuid4().hex[:8]}_{f.filename}"
        f.save(tmp)
        try:
            parsed = postman_import.parse_collection(tmp)
        finally:
            tmp.unlink(missing_ok=True)
        cols.append(parsed)
        added.append({"id": parsed["id"], "name": parsed["name"], "count": len(parsed["requests"])})
    _save(COLLECTIONS_PATH, cols)
    return jsonify({"added": added})


@app.delete("/api/collections/<col_id>")
def delete_collection(col_id: str):
    cols = [c for c in _collections() if c["id"] != col_id]
    _save(COLLECTIONS_PATH, cols)
    return jsonify({"ok": True})


# ---- environments ----

@app.get("/api/environments")
def list_environments():
    return jsonify({"environments": _environments(), "active": _state().get("active_env")})


@app.post("/api/environments/import")
def import_environments():
    envs = _environments()
    added = []
    for f in request.files.getlist("files"):
        tmp = DATA / f"_upload_{uuid.uuid4().hex[:8]}_{f.filename}"
        f.save(tmp)
        try:
            parsed = postman_import.parse_environment(tmp)
        finally:
            tmp.unlink(missing_ok=True)
        envs.append(parsed)
        added.append({"id": parsed["id"], "name": parsed["name"]})
    _save(ENVIRONMENTS_PATH, envs)
    return jsonify({"added": added})


@app.put("/api/environments/<env_id>/values")
def update_environment(env_id: str):
    envs = _environments()
    body = request.get_json(force=True)
    for e in envs:
        if e["id"] == env_id:
            e["values"] = body.get("values", e["values"])
    _save(ENVIRONMENTS_PATH, envs)
    return jsonify({"ok": True})


@app.delete("/api/environments/<env_id>")
def delete_environment(env_id: str):
    envs = [e for e in _environments() if e["id"] != env_id]
    _save(ENVIRONMENTS_PATH, envs)
    state = _state()
    if state.get("active_env") == env_id:
        state["active_env"] = None
        _save(STATE_PATH, state)
    return jsonify({"ok": True})


@app.post("/api/environments/active")
def set_active_environment():
    env_id = request.get_json(force=True).get("env_id")
    state = _state()
    state["active_env"] = env_id
    _save(STATE_PATH, state)
    return jsonify({"ok": True})


# ---- send ----

def _merged_variables(collection_id: str | None) -> dict[str, str]:
    variables: dict[str, str] = {}
    if collection_id:
        for c in _collections():
            if c["id"] == collection_id:
                variables.update(c.get("variables", {}))
    env_id = _state().get("active_env")
    if env_id:
        for e in _environments():
            if e["id"] == env_id:
                variables.update(e.get("values", {}))
    return variables


@app.post("/api/send")
def send_request():
    body = request.get_json(force=True)
    req = body.get("request", {})
    variables = _merged_variables(body.get("collection_id"))
    result = request_runner.send(req, variables, verify=not body.get("skip_tls_verify", False))
    return jsonify(result)


# ---- evidence ----

@app.post("/api/evidence")
def capture_evidence():
    body = request.get_json(force=True)
    entry = body.get("entry", {})
    name = body.get("name", "request")
    path = evidence.capture(entry, name)
    return jsonify({"file": path.name})


@app.get("/api/evidence/<filename>")
def get_evidence(filename: str):
    return send_file(evidence.EVIDENCE_DIR / filename)


@app.get("/api/qa-runs")
def qa_runs():
    return jsonify(evidence.list_runs())


@app.post("/api/evidence/save-to-run")
def save_to_run():
    body = request.get_json(force=True)
    src = evidence.EVIDENCE_DIR / body["file"]
    target = evidence.copy_into_run(src, body["run"], body["task"], body.get("label", "api-call"))
    return jsonify({"saved_to": str(target)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5152, debug=False)
