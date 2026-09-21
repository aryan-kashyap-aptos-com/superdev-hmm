"""CloudWatch Logs helpers for ShopLogic API log groups."""

from __future__ import annotations

import time
from typing import Callable

from aws_env import aws_region, aws_session

# Prefixes that usually match ShopLogic API groups (avoids scanning every log group in the account).
_LOG_GROUP_PREFIXES = (
    "SHOPLOGICAPI",
    "ShopLogicAPI",
    "shoplogicapi",
    "/aws/",
    "/oms/",
    "oms-",
)

_cache: list[str] | None = None
_cache_at: float = 0.0
_CACHE_TTL_SECONDS = 300

SCAN_WINDOW_CHOICES: dict[str, int] = {
    "Last 1 hour": 60,
    "Last 6 hours": 360,
    "Last 24 hours": 24 * 60,
    "Last 7 days": 7 * 24 * 60,
}


def list_shoplogic_api_log_groups(force_refresh: bool = False) -> list[str]:
    global _cache, _cache_at
    if not force_refresh and _cache is not None and (time.time() - _cache_at) < _CACHE_TTL_SECONDS:
        return list(_cache)

    client = aws_session().client("logs", region_name=aws_region())
    matches: set[str] = set()

    for prefix in _LOG_GROUP_PREFIXES:
        token: str | None = None
        while True:
            kwargs: dict = {"logGroupNamePrefix": prefix, "limit": 50}
            if token:
                kwargs["nextToken"] = token
            response = client.describe_log_groups(**kwargs)
            for group in response.get("logGroups", []):
                name = group.get("logGroupName", "")
                upper = name.upper()
                if "SHOPLOGICAPI" in upper or ("SHOPLOGIC" in upper and "API" in upper):
                    matches.add(name)
            token = response.get("nextToken")
            if not token:
                break

    _cache = sorted(matches)
    _cache_at = time.time()
    return list(_cache)


def preload_log_groups_background(on_done: Callable[[list[str]], None] | None = None) -> None:
    import threading

    def worker() -> None:
        try:
            groups = list_shoplogic_api_log_groups(force_refresh=True)
            if on_done:
                on_done(groups)
        except Exception:
            if on_done:
                on_done([])

    threading.Thread(target=worker, daemon=True).start()


def tail_log_group(
    log_group_name: str,
    limit: int = 500,
    lookback_minutes: int = 24 * 60,
) -> str:
    """Return recent log lines from the newest streams, within the lookback window."""
    client = aws_session().client("logs", region_name=aws_region())
    start_ms = int((time.time() - lookback_minutes * 60) * 1000)

    streams = client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy="LastEventTime",
        descending=True,
        limit=3,
    )
    stream_names = [s["logStreamName"] for s in streams.get("logStreams", [])]
    if not stream_names:
        return f"No streams in {log_group_name}"

    header = (
        f"Log group: {log_group_name}\n"
        f"Window: last {lookback_minutes} minutes (up to {limit} events, newest streams first)\n"
        f"{'=' * 72}\n"
    )

    lines: list[str] = []
    for stream in stream_names:
        token: str | None = None
        while len(lines) < limit:
            kwargs: dict = {
                "logGroupName": log_group_name,
                "logStreamName": stream,
                "startTime": start_ms,
                "startFromHead": False,
                "limit": min(100, limit - len(lines)),
            }
            if token:
                kwargs["nextToken"] = token
            events = client.get_log_events(**kwargs)
            batch = events.get("events", [])
            if not batch:
                break
            for event in batch:
                lines.append(event.get("message", ""))
            token = events.get("nextForwardToken")
            if not token or len(batch) < kwargs["limit"]:
                break
        if len(lines) >= limit:
            break

    if not lines:
        return header + f"No events in the last {lookback_minutes} minutes."
    return header + "\n".join(lines[-limit:])
