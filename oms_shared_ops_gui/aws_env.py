"""AWS credentials from local .env or sibling oms_ec2_connector env file."""

from __future__ import annotations

import os
from pathlib import Path

import boto3
from boto3.session import Session

ROOT = Path(__file__).resolve().parent
CONNECTOR_ROOT = ROOT.parent / "oms_ec2_connector"


def _load_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_aws_env() -> None:
    custom = os.getenv("OMS_OPS_ENV_FILE", "").strip()
    if custom:
        _load_file(Path(custom).expanduser().resolve())
        return
    _load_file(ROOT / ".env")
    _load_file(CONNECTOR_ROOT / ".env.pod2dev")


def aws_region() -> str:
    load_aws_env()
    return os.getenv("AWS_REGION", "us-east-1")


def aws_session() -> Session:
    load_aws_env()
    kwargs: dict[str, str] = {"region_name": aws_region()}
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    if access_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = os.environ["AWS_SECRET_ACCESS_KEY"]
        token = os.getenv("AWS_SESSION_TOKEN", "").strip()
        if token:
            kwargs["aws_session_token"] = token
    return boto3.Session(**kwargs)
