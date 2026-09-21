"""Runs the canonical script in tickets/RANDOM/name-tag-runs/apply-missing-name-tags.py."""
import os
import subprocess
import sys

_CANONICAL = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "tickets",
        "RANDOM",
        "name-tag-runs",
        "apply-missing-name-tags.py",
    )
)
raise SystemExit(subprocess.call([sys.executable, _CANONICAL] + sys.argv[1:]))
