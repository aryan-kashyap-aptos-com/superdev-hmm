"""Human-readable labels for Windows service enums returned as JSON numbers."""

from __future__ import annotations

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
