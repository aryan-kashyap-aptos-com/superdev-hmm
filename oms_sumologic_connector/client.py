"""Load .env and authenticate to the Sumo Logic Search Job API."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"

DEPLOYMENTS = {
    "us1": "https://api.sumologic.com/api",
    "us2": "https://api.us2.sumologic.com/api",
    "eu": "https://api.eu.sumologic.com/api",
    "au": "https://api.au.sumologic.com/api",
    "de": "https://api.de.sumologic.com/api",
    "jp": "https://api.jp.sumologic.com/api",
    "ca": "https://api.ca.sumologic.com/api",
    "in": "https://api.in.sumologic.com/api",
    "fed": "https://api.fed.sumologic.com/api",
}


def load_env() -> None:
    if not ENV_FILE.exists():
        raise RuntimeError(f"Missing {ENV_FILE}. Copy .env.example to .env and fill in values.")
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def api_base_url() -> str:
    load_env()
    deployment = os.getenv("SUMO_DEPLOYMENT", "us2").strip().lower()
    if deployment.startswith("http"):
        base = deployment.rstrip("/")
        return base if base.endswith("/api") else f"{base}/api"
    if deployment not in DEPLOYMENTS:
        raise RuntimeError(f"Unknown SUMO_DEPLOYMENT {deployment!r}. Use one of: {', '.join(DEPLOYMENTS)}")
    return DEPLOYMENTS[deployment]


def credentials() -> tuple[str, str]:
    load_env()
    missing = [name for name in ("SUMO_ACCESS_ID", "SUMO_ACCESS_KEY") if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing env: {', '.join(missing)}")
    return os.environ["SUMO_ACCESS_ID"], os.environ["SUMO_ACCESS_KEY"]


def default_timezone() -> str:
    load_env()
    return os.getenv("SUMO_TIMEZONE", "UTC")
