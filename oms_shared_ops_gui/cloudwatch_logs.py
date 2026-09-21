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


def tail_log_group(log_group_name: str, limit: int = 80) -> str:
    client = aws_session().client("logs", region_name=aws_region())
    streams = client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy="LastEventTime",
        descending=True,
        limit=2,
    )
    stream_names = [s["logStreamName"] for s in streams.get("logStreams", [])]
    if not stream_names:
        return f"No streams in {log_group_name}"

    lines: list[str] = []
    for stream in stream_names:
        events = client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=stream,
            limit=limit,
            startFromHead=False,
        )
        for event in events.get("events", []):
            lines.append(event.get("message", ""))
        if len(lines) >= limit:
            break
    return "\n".join(lines[-limit:])
