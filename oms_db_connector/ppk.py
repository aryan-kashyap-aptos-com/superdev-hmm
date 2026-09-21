"""Parse PuTTY PPK v2 RSA keys for paramiko."""

from __future__ import annotations

import base64
import struct
from io import StringIO

import paramiko
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def _read_string(data: bytes, offset: int) -> tuple[bytes, int]:
    length = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4
    return data[offset : offset + length], offset + length


def _bytes_to_int(value: bytes) -> int:
    return int.from_bytes(value, "big")


def _extract_blob(lines: list[str], label: str) -> bytes:
    section: list[str] = []
    count = 0
    mode = False
    for line in lines:
        if line.startswith(f"{label}-Lines:"):
            count = int(line.split(":", 1)[1].strip())
            mode = True
            continue
        if mode and line.startswith(("Public-Lines:", "Private-Lines:", "Private-MAC:")):
            if line.startswith(f"{label}-Lines:"):
                continue
            break
        if mode and count > 0:
            section.append(line)
            count -= 1
    return base64.b64decode("".join(section))


def ppk_to_paramiko(ppk_text: str) -> paramiko.RSAKey:
    lines = [line.strip() for line in ppk_text.splitlines()]
    if not lines or not lines[0].startswith("PuTTY-User-Key-File-"):
        raise ValueError("Unsupported PPK format")

    public_blob = _extract_blob(lines, "Public")
    private_blob = _extract_blob(lines, "Private")

    offset = 0
    _, offset = _read_string(public_blob, offset)
    e_bytes, offset = _read_string(public_blob, offset)
    n_bytes, offset = _read_string(public_blob, offset)

    offset = 0
    d_bytes, offset = _read_string(private_blob, offset)
    p_bytes, offset = _read_string(private_blob, offset)
    q_bytes, offset = _read_string(private_blob, offset)

    private_key = rsa.RSAPrivateNumbers(
        d=_bytes_to_int(d_bytes),
        p=_bytes_to_int(p_bytes),
        q=_bytes_to_int(q_bytes),
        dmp1=rsa.rsa_crt_dmp1(_bytes_to_int(d_bytes), _bytes_to_int(p_bytes)),
        dmq1=rsa.rsa_crt_dmq1(_bytes_to_int(d_bytes), _bytes_to_int(q_bytes)),
        iqmp=rsa.rsa_crt_iqmp(_bytes_to_int(p_bytes), _bytes_to_int(q_bytes)),
        public_numbers=rsa.RSAPublicNumbers(e=_bytes_to_int(e_bytes), n=_bytes_to_int(n_bytes)),
    ).private_key(default_backend())
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return paramiko.RSAKey.from_private_key(StringIO(pem))
