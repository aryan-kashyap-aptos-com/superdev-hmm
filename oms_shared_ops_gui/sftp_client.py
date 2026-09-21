"""SFTP access for large file browse/download (credentials from env or session prompt)."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from typing import Callable

import paramiko

from aws_env import load_aws_env

ProgressCallback = Callable[[int, int], None]


@dataclass
class SftpEntry:
    name: str
    is_directory: bool
    size: int
    mtime: float


def _load_creds() -> tuple[str, str, str]:
    load_aws_env()
    user = os.environ.get("OMS_SFTP_USER", "").strip()
    password = os.environ.get("OMS_SFTP_PASSWORD", "").strip()
    domain = os.environ.get("OMS_SFTP_DOMAIN", "omspod").strip()
    if user and "\\" not in user and domain:
        user = f"{domain}\\{user}"
    return user, password, domain


def resolve_credentials(
    username: str | None = None,
    password: str | None = None,
) -> tuple[str, str]:
    env_user, env_pass, _ = _load_creds()
    user = (username or env_user).strip()
    pwd = password or env_pass
    if not user:
        raise ValueError("SFTP user not set. Use Connect SFTP or set OMS_SFTP_USER in .env")
    if not pwd:
        raise ValueError("SFTP password not set. Use Connect SFTP or set OMS_SFTP_PASSWORD in .env")
    return user, pwd


class SftpSession:
    def __init__(self, host: str, port: int = 22) -> None:
        self.host = host
        self.port = port
        self._client: paramiko.SSHClient | None = None
        self._sftp: paramiko.SFTPClient | None = None
        self.username: str = ""

    @property
    def connected(self) -> bool:
        return self._sftp is not None

    def connect(self, username: str, password: str, timeout: int = 30) -> None:
        self.close()
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            self.host,
            port=self.port,
            username=username,
            password=password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
        )
        self._client = client
        self._sftp = client.open_sftp()
        self.username = username

    def close(self) -> None:
        if self._sftp:
            self._sftp.close()
            self._sftp = None
        if self._client:
            self._client.close()
            self._client = None

    def list_dir(self, path: str) -> list[SftpEntry]:
        if not self._sftp:
            raise RuntimeError("SFTP not connected")
        remote = path if path.startswith("/") else f"/{path}"
        entries: list[SftpEntry] = []
        for attr in self._sftp.listdir_attr(remote):
            is_dir = stat.S_ISDIR(attr.st_mode)
            entries.append(
                SftpEntry(
                    name=attr.filename,
                    is_directory=is_dir,
                    size=int(attr.st_size or 0),
                    mtime=float(attr.st_mtime or 0),
                )
            )
        entries.sort(key=lambda e: (not e.is_directory, e.name.lower()))
        return entries

    def download(
        self,
        remote_path: str,
        local_path: str,
        progress: ProgressCallback | None = None,
    ) -> int:
        if not self._sftp:
            raise RuntimeError("SFTP not connected")
        remote = remote_path if remote_path.startswith("/") else f"/{remote_path}"

        def _cb(done: int, total: int) -> None:
            if progress:
                progress(done, total)

        self._sftp.get(remote, local_path, callback=_cb)
        return os.path.getsize(local_path)
