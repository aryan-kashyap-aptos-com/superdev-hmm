"""Map IIS UNC physical paths to local paths on content and Site Manager servers."""

from __future__ import annotations

import re


def content_server_path_from_unc(iis_physical: str) -> str | None:
    """
    UNC from IIS often looks like:
      \\\\omspod.aptos.com\\shareddev\\dev\\poddev\\sm
    On eom-core-shared-dev-cont the files live at:
      D:\\content\\dev\\poddev\\sm
    """
    normalized = (iis_physical or "").replace("/", "\\")
    match = re.search(r"\\dev\\([^\\]+)\\sm", normalized, re.IGNORECASE)
    if not match:
        return None
    env_name = match.group(1)
    return f"D:\\content\\dev\\{env_name}\\sm"


def shoplogic_path_candidates(iis_physical: str) -> list[str]:
    """Build path list: UNC from IIS, then likely local mirrors on content/SM drives."""
    raw = (iis_physical or "").strip().rstrip("\\/")
    if not raw:
        return []

    candidates: list[str] = []
    content_path = content_server_path_from_unc(raw)
    if content_path:
        candidates.append(content_path)

    candidates.append(raw)
    normalized = raw.replace("/", "\\")

    if normalized.startswith("\\\\"):
        stripped = normalized.lstrip("\\")
        parts = stripped.split("\\")
        if len(parts) >= 2:
            # \\host\share\rest -> share\rest and rest-only variants
            after_host = "\\".join(parts[1:])
            after_share = "\\".join(parts[2:]) if len(parts) > 2 else ""

            for rel in filter(None, [after_host, after_share]):
                for drive in ("D", "E", "F", "C"):
                    candidates.append(f"{drive}:\\{rel}")
                if "dev\\" in rel.lower():
                    tail = rel.split("dev\\", 1)[-1]
                    for drive in ("D", "E", "F"):
                        candidates.append(f"{drive}:\\dev\\{tail}")

    seen: set[str] = set()
    unique: list[str] = []
    for path in candidates:
        key = path.lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique
