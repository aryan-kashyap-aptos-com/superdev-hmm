"""Load .env and build an authenticated boto3 session."""

from __future__ import annotations

import os
from pathlib import Path

import boto3
from boto3.session import Session

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
_ACTIVE_ENV_FILE: Path | None = None


def set_env_file(path: str | Path | None) -> None:
    global _ACTIVE_ENV_FILE
    if path is None:
        _ACTIVE_ENV_FILE = None
        return
    _ACTIVE_ENV_FILE = Path(path).expanduser().resolve()


def env_file_path() -> Path:
    if _ACTIVE_ENV_FILE is not None:
        return _ACTIVE_ENV_FILE
    custom = os.getenv("CONNECTOR_ENV_FILE", "").strip()
    if custom:
        return Path(custom).expanduser().resolve()
    return ENV_FILE


def load_env() -> None:
    env_file = env_file_path()
    if not env_file.exists():
        raise RuntimeError(f"Missing {env_file}. Copy .env.example to .env and fill in values.")
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def aws_session() -> Session:
    load_env()
    missing = [
        name
        for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "SECRET_ARN")
        if not os.getenv(name)
    ]
    if missing:
        raise RuntimeError(f"Missing env: {', '.join(missing)}")

    kwargs: dict[str, str] = {
        "aws_access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
        "aws_secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
        "region_name": os.environ["AWS_REGION"],
    }
    session_token = os.getenv("AWS_SESSION_TOKEN", "").strip()
    if session_token:
        kwargs["aws_session_token"] = session_token

    return boto3.Session(**kwargs)


def secret_arn() -> str:
    load_env()
    return os.environ["SECRET_ARN"]
