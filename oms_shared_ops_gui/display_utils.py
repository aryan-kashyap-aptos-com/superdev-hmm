"""Human-readable labels for Windows service enums returned as JSON numbers."""

from __future__ import annotations

from datetime import datetime


def format_file_size(num_bytes: object) -> str:
    try:
        n = int(num_bytes or 0)
    except (TypeError, ValueError):
        return "-"
    if n < 0:
        return "-"
    if n < 1024:
        return f"{n} B"
    units = ("KB", "MB", "GB", "TB")
    value = float(n)
    for unit in units:
        value /= 1024.0
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "KB" else f"{value:.0f} KB"
    return f"{n} B"


def format_remote_timestamp(iso_text: object) -> str:
    text = str(iso_text or "").strip()
    if not text:
        return "-"
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return text[:19] if len(text) > 19 else text


# System.ServiceProcess.ServiceControllerStatus
SERVICE_STATUS_BY_INT: dict[int, str] = {
    1: "Stopped",
    2: "Start pending",
    3: "Stop pending",
    4: "Running",
    5: "Continue pending",
    6: "Pause pending",
    7: "Paused",
}

# System.ServiceProcess.ServiceStartMode
START_TYPE_BY_INT: dict[int, str] = {
    0: "Boot",
    1: "System",
    2: "Automatic",
    3: "Manual",
    4: "Disabled",
}


def format_service_status(raw: object) -> str:
    if raw is None:
        return "Unknown"
    if isinstance(raw, int):
        return SERVICE_STATUS_BY_INT.get(raw, f"Unknown ({raw})")
    text = str(raw).strip()
    if text.isdigit():
        return SERVICE_STATUS_BY_INT.get(int(text), f"Unknown ({text})")
    return text


def format_start_type(raw: object) -> str:
    if raw is None:
        return "Unknown"
    if isinstance(raw, int):
        return START_TYPE_BY_INT.get(raw, f"Unknown ({raw})")
    text = str(raw).strip()
    if text.isdigit():
        return START_TYPE_BY_INT.get(int(text), f"Unknown ({text})")
    return text


def status_tag(status_label: str) -> str:
    normalized = status_label.lower().replace(" ", "")
    if "running" in normalized:
        return "Running"
    if "stopped" in normalized and "pending" not in normalized:
        return "Stopped"
    if "pending" in normalized or "paused" in normalized:
        return "Pending"
    return ""


def iis_state_tag(state: str) -> str:
    text = (state or "").strip().lower()
    if text == "started":
        return "IISStarted"
    if text == "stopped":
        return "IISStopped"
    if "ing" in text or not text:
        return "IISPending"
    return "IISNeutral"


def iis_row_tag(site_state: str, pool_state: str) -> str:
    """Row color: worst of site vs app pool (red if either down)."""
    site = (site_state or "").strip().lower()
    pool = (pool_state or "").strip().lower()
    if "stopped" in site or "stopped" in pool:
        return "IISStopped"
    if "ing" in site or "ing" in pool or "…" in site_state or "…" in pool_state:
        return "IISPending"
    if site == "started" and pool == "started":
        return "IISStarted"
    if site == "started":
        return "IISStarted"
    return "IISNeutral"
