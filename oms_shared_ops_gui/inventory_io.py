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

ROLE_ORDER = ("toronado", "sitemanager", "content")


@dataclass(frozen=True)
class Bastion:
    label: str
    name_tag: str
    instance_id: str
    public_ip: str = ""


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
    bastion: Bastion | None = None
    ssm_parameter_prefix: str = "/"

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
        bastion_raw = raw.get("bastion")
        bastion: Bastion | None = None
        if isinstance(bastion_raw, dict) and bastion_raw.get("name_tag"):
            bastion = Bastion(
                label=str(bastion_raw.get("label", "Bastion host")),
                name_tag=str(bastion_raw["name_tag"]),
                instance_id=str(bastion_raw.get("instance_id", "")),
                public_ip=str(bastion_raw.get("public_ip", "")),
            )
        stacks.append(
            Stack(
                id=raw["id"],
                label=raw["label"],
                description=raw.get("description", ""),
                hosts=hosts,
                bastion=bastion,
                ssm_parameter_prefix=str(raw.get("ssm_parameter_prefix", "/")),
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
        bastion = stack.get("bastion")
        if isinstance(bastion, dict) and bastion.get("name_tag"):
            name_tags.add(bastion["name_tag"])

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
                    "public_ip": inst.get("PublicIpAddress") or "",
                    "state": inst.get("State", {}).get("Name", ""),
                }

    for stack in data.get("stacks", []):
        for host in stack.get("hosts", []):
            tag = host["name_tag"]
            if tag in lookup:
                host["instance_id"] = lookup[tag]["instance_id"]
                host["private_ip"] = lookup[tag]["private_ip"]
        bastion = stack.get("bastion")
        if isinstance(bastion, dict):
            tag = bastion.get("name_tag")
            if tag and tag in lookup:
                bastion["instance_id"] = lookup[tag]["instance_id"]
                bastion["public_ip"] = lookup[tag]["public_ip"]

    data["updated"] = date.today().isoformat()
    save_inventory(data)
    return data
