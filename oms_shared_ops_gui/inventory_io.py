"""Load / refresh stack inventory from inventory.json and AWS."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from aws_env import aws_region, aws_session

ROOT = Path(__file__).resolve().parent
INVENTORY_PATH = ROOT / "inventory.json"

ROLE_ORDER = ("toronado", "sitemanager")


@dataclass(frozen=True)
class Host:
    role: str
    label: str
    name_tag: str
    instance_id: str
    private_ip: str


@dataclass(frozen=True)
class Stack:
    id: str
    label: str
    description: str
    hosts: tuple[Host, ...]

    def host_by_role(self, role: str) -> Host | None:
        for h in self.hosts:
            if h.role == role:
                return h
        return None


def load_inventory() -> tuple[str, list[Stack]]:
    data = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    region = data.get("region", "us-east-1")
    stacks: list[Stack] = []
    for raw in data.get("stacks", []):
        hosts = tuple(
            Host(
                role=h["role"],
                label=h.get("label", h["role"]),
                name_tag=h["name_tag"],
                instance_id=h["instance_id"],
                private_ip=h.get("private_ip", ""),
            )
            for h in raw.get("hosts", [])
        )
        stacks.append(
            Stack(
                id=raw["id"],
                label=raw["label"],
                description=raw.get("description", ""),
                hosts=hosts,
            )
        )
    return region, stacks


def save_inventory(data: dict[str, Any]) -> None:
    INVENTORY_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def refresh_from_aws() -> dict[str, Any]:
    """Update instance IDs/IPs for known name tags in inventory.json."""
    data = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    ec2 = aws_session().client("ec2", region_name=aws_region())
    name_tags: set[str] = set()
    for stack in data.get("stacks", []):
        for host in stack.get("hosts", []):
            name_tags.add(host["name_tag"])

    lookup: dict[str, dict[str, str]] = {}
    for name in sorted(name_tags):
        response = ec2.describe_instances(
            Filters=[
                {"Name": "tag:Name", "Values": [name]},
                {"Name": "instance-state-name", "Values": ["running", "stopped", "pending"]},
            ],
        )
        for reservation in response.get("Reservations", []):
            for inst in reservation.get("Instances", []):
                lookup[name] = {
                    "instance_id": inst.get("InstanceId", ""),
                    "private_ip": inst.get("PrivateIpAddress") or "",
                    "state": inst.get("State", {}).get("Name", ""),
                }

    for stack in data.get("stacks", []):
        for host in stack.get("hosts", []):
            tag = host["name_tag"]
            if tag in lookup:
                host["instance_id"] = lookup[tag]["instance_id"]
                host["private_ip"] = lookup[tag]["private_ip"]

    data["updated"] = date.today().isoformat()
    save_inventory(data)
    return data
