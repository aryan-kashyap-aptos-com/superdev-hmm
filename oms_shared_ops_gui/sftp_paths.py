"""Map OMS environments to SFTP path templates from stack inventory."""

from __future__ import annotations

from inventory_io import SftpConfig, Stack
from env_detection import classify_iis_site, environment_from_physical_path


def sftp_sm_path(config: SftpConfig, env_slug: str) -> str:
    template = config.path_roots.get("sm", "/dev/{env}/sm")
    return template.format(env=env_slug).replace("\\", "/").rstrip("/")


def sftp_task_path(config: SftpConfig, env_slug: str) -> str:
    template = config.path_roots.get("task", "/task/{env}/")
    return template.format(env=env_slug).replace("\\", "/")


def sftp_path_for_iis_site(stack: Stack, site_name: str, physical_path: str) -> str | None:
    if not stack.sftp:
        return None
    det = classify_iis_site(site_name, physical_path)
    env = environment_from_physical_path(physical_path) or (det.environment if det.is_oms else "")
    if not env or env == "unknown":
        return None
    return sftp_sm_path(stack.sftp, env)
