"""Heuristics for OMS environments on shared Toro / IIS hosts (no hardcoded env list)."""

from __future__ import annotations

import re
from dataclasses import dataclass

TORO_SERVICE_RE = re.compile(
    r"^OMS-(JobManager|JobProcessor|Export|Import)-(?P<env>[^-]+(?:-[^-]+)*)-(?P<slot>\d+)$",
    re.IGNORECASE,
)
TORO_ANY_OMS_RE = re.compile(r"^OMS-", re.IGNORECASE)
PHYSICAL_ENV_RE = re.compile(r"[\\/]dev[\\/](?P<env>[^\\/]+)[\\/]", re.IGNORECASE)
UNC_ENV_RE = re.compile(r"[\\/]regression\d+[a-z]*[\\/]", re.IGNORECASE)
SITE_OMS_SUFFIXES = ("-sm", "-shoplogic", "-sitemanager", "-izenda", "-api")


@dataclass(frozen=True)
class DetectionResult:
    is_oms: bool
    environment: str
    reason: str


def environment_from_physical_path(path: str) -> str | None:
    if not path:
        return None
    match = PHYSICAL_ENV_RE.search(path.replace("/", "\\"))
    if match:
        return match.group("env")
    lowered = path.lower()
    for token in ("poddev", "regression", "omnipod", "perf15"):
        if token in lowered:
            parts = re.split(r"[\\/]", path)
            for part in parts:
                if token in part.lower() and len(part) > 3:
                    return part
    return None


def classify_toro_service(name: str) -> DetectionResult:
    text = name.strip()
    if not TORO_ANY_OMS_RE.match(text):
        return DetectionResult(False, "", "Name does not start with OMS-")
    match = TORO_SERVICE_RE.match(text)
    if match:
        env = match.group("env")
        return DetectionResult(True, env, f"Toro pair pattern OMS-*-{env}-<slot>")
    return DetectionResult(True, "unknown", "OMS- prefix (non-standard name; still treated as OMS)")


def classify_iis_site(site_name: str, physical_path: str = "") -> DetectionResult:
    name = site_name.strip()
    path = (physical_path or "").strip()
    env_from_path = environment_from_physical_path(path)
    if env_from_path:
        return DetectionResult(True, env_from_path, "Physical path contains \\dev\\{env}\\")
    lowered = name.lower()
    if any(lowered.endswith(suffix) or suffix in lowered for suffix in SITE_OMS_SUFFIXES):
        env_guess = name.split("-")[0] if "-" in name else name
        return DetectionResult(True, env_guess, "Site name matches OMS SM / ShopLogic suffix")
    if path and ("shoplogic" in path.lower() or "isms" in path.lower() or "sitemanager" in path.lower()):
        env = env_from_path or "unknown"
        return DetectionResult(True, env, "Physical path looks like OMS content (isms / ShopLogic)")
    if "shared-dev-sitemanager" in lowered or name == "Default Web Site":
        return DetectionResult(False, "", "Infrastructure / default site, not a tenant env")
    return DetectionResult(False, "", "No OMS naming or path signal")


def detection_rules_markdown() -> str:
    return """How OMS Engine detects environments

New regression / pod / omnipod tenants appear automatically when IIS or Toro lists them.
Nothing is maintained as a fixed env list in code.

Toronado (Windows services)
  • OMS-* services are treated as OMS.
  • Environment slug is parsed from names like:
      OMS-JobManager-regression202510qa-26
      OMS-JobProcessor-poddev-26
    Pattern: OMS-<role>-<environment>-<slot>

Site Manager (IIS)
  • Primary signal: physical path segment \\dev\\{environment}\\ (from UNC or D:\\content\\dev\\...).
  • Secondary: site name suffixes (-sm, -shoplogic, -izenda, etc.).
  • Excluded: shared infrastructure sites (e.g. shared-dev-sitemanager).

Why newer envs show up without a code change
  • Refresh loads live Get-Website / Get-Service output from the host.
  • Classification runs on each row using the rules above.
  • inventory.json only defines which EC2 instances to connect to, not tenant names.

Stack selection
  • Pick the stack (shared dev, pod2, perf15) to choose Toro / SM / content instance IDs.
  • Use Refresh (toolbar) after replacing EC2 instances in AWS; instance IDs refresh from inventory.json + AWS.
"""
