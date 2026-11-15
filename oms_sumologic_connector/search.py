"""Run Sumo Logic search jobs and collect messages or aggregate records."""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from client import api_base_url, credentials, default_timezone

DONE_STATE = "DONE GATHERING RESULTS"
FAILED_STATES = {"CANCELLED", "FAILED GATHERING RESULTS"}


def parse_time(value: str) -> str:
    value = value.strip()
    if value.lower() == "now":
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    relative = re.fullmatch(r"-(\d+)([mhd])", value.lower())
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2)
        delta = {"m": timedelta(minutes=amount), "h": timedelta(hours=amount), "d": timedelta(days=amount)}[unit]
        return (datetime.now(timezone.utc) - delta).strftime("%Y-%m-%dT%H:%M:%S")

    return value


def _request(method: str, path: str, **kwargs: Any) -> requests.Response:
    access_id, access_key = credentials()
    url = f"{api_base_url()}{path}"
    response = requests.request(method, url, auth=(access_id, access_key), timeout=120, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(f"Sumo API {method} {path} failed ({response.status_code}): {response.text}")
    return response


def create_search_job(
    query: str,
    *,
    time_from: str,
    time_to: str,
    time_zone: str | None = None,
) -> str:
    payload = {
        "query": query,
        "from": parse_time(time_from),
        "to": parse_time(time_to),
        "timeZone": time_zone or default_timezone(),
    }
    response = _request("POST", "/v1/search/jobs", json=payload)
    if response.status_code != 202:
        raise RuntimeError(f"Unexpected create job status {response.status_code}: {response.text}")
    job_id = response.json()["id"]
    return str(job_id)


def wait_for_job(job_id: str, *, poll_seconds: float = 2.0, timeout_seconds: int = 600) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = _request("GET", f"/v1/search/jobs/{job_id}")
        status = response.json()
        state = status.get("state", "")
        if state == DONE_STATE:
            return status
        if state in FAILED_STATES:
            raise RuntimeError(f"Search job {job_id} failed with state {state!r}")
        time.sleep(poll_seconds)
    raise RuntimeError(f"Search job {job_id} timed out after {timeout_seconds}s")


def delete_job(job_id: str) -> None:
    _request("DELETE", f"/v1/search/jobs/{job_id}")


def _fetch_pages(path: str, *, limit: int, max_rows: int | None) -> tuple[list[str], list[dict[str, Any]]]:
    fields: list[str] = []
    rows: list[dict[str, Any]] = []
    offset = 0
    page_size = min(limit, 1000)

    while True:
        response = _request("GET", path, params={"offset": offset, "limit": page_size})
        payload = response.json()
        if not fields:
            fields = [field["name"] for field in payload.get("fields", [])]

        batch_key = "messages" if "messages" in payload else "records"
        batch = payload.get(batch_key, [])
        for item in batch:
            rows.append(dict(item.get("map", {})))
            if max_rows is not None and len(rows) >= max_rows:
                return fields, rows

        if len(batch) < page_size:
            break
        offset += page_size

    return fields, rows


def run_query(
    query: str,
    *,
    time_from: str = "-15m",
    time_to: str = "now",
    time_zone: str | None = None,
    result_type: str = "auto",
    limit: int = 1000,
    max_rows: int | None = None,
    cleanup: bool = True,
) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    job_id = create_search_job(query, time_from=time_from, time_to=time_to, time_zone=time_zone)
    try:
        status = wait_for_job(job_id)
        use_records = result_type == "records" or (
            result_type == "auto" and int(status.get("recordCount", 0) or 0) > 0
        )
        suffix = "records" if use_records else "messages"
        fields, rows = _fetch_pages(
            f"/v1/search/jobs/{job_id}/{suffix}",
            limit=limit,
            max_rows=max_rows,
        )
        return fields, rows, status
    finally:
        if cleanup:
            try:
                delete_job(job_id)
            except Exception:
                pass


def verify_connection() -> dict[str, Any]:
    job_id = create_search_job("* | count", time_from="-5m", time_to="now")
    try:
        status = wait_for_job(job_id, timeout_seconds=120)
        return status
    finally:
        try:
            delete_job(job_id)
        except Exception:
            pass
