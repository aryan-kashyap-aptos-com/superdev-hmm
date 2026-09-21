#!/usr/bin/env python3
"""Update inventory.json instance IDs from AWS (CLI)."""

from inventory_io import INVENTORY_PATH, refresh_from_aws

if __name__ == "__main__":
    refresh_from_aws()
    print(f"Updated {INVENTORY_PATH}")
