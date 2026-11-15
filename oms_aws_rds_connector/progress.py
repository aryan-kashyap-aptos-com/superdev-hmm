"""Small helper so CLI steps print immediately."""

from __future__ import annotations

import sys


def step(message: str) -> None:
    print(message, flush=True)


def warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr, flush=True)
