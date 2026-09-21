"""Resolve EC2 instance aliases from env vars."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from client import aws_region, aws_session, load_env

ALIAS_ALIASES = {
    "sm": "sitemanager",
    "site-manager": "sitemanager",
    "sitemgr": "sitemanager",
    "migration": "rds-migration",
    "rds-migration-host": "rds-migration",
}


@dataclass(frozen=True)
class Instance:
    alias: str
    instance_id: str
    private_ip: str
    public_ip: str | None = None
    ssm_status: str | None = None
    computer_name: str | None = None

    @property
    def display_ip(self) -> str:
        if self.public_ip:
            return f"{self.private_ip} (public {self.public_ip})"
        return self.private_ip


def _normalize_alias(alias: str) -> str:
    key = alias.strip().lower().replace("_", "-")
    return ALIAS_ALIASES.get(key, key)


def _discover_from_env() -> dict[str, Instance]:
    load_env()
    ids: dict[str, str] = {}
    private_ips: dict[str, str] = {}
    public_ips: dict[str, str] = {}

    for key, value in os.environ.items():
        match = re.fullmatch(r"INSTANCE_(.+)_PUBLIC_IP", key)
        if match:
            public_ips[_normalize_alias(match.group(1))] = value.strip()
            continue
        match = re.fullmatch(r"INSTANCE_(.+)_ID", key)
        if match:
            ids[_normalize_alias(match.group(1))] = value.strip()
            continue
        match = re.fullmatch(r"INSTANCE_(.+)_IP", key)
        if match:
            private_ips[_normalize_alias(match.group(1))] = value.strip()
            continue

    aliases = sorted(set(ids) | set(private_ips))
    instances: dict[str, Instance] = {}
    for alias in aliases:
        instance_id = ids.get(alias, "")
        private_ip = private_ips.get(alias, "")
        if not instance_id:
            raise RuntimeError(f"Missing INSTANCE_{alias.upper().replace('-', '_')}_ID in env file")
        instances[alias] = Instance(
            alias=alias,
            instance_id=instance_id,
            private_ip=private_ip,
            public_ip=public_ips.get(alias),
        )
    return instances


def list_instances(include_ssm: bool = True) -> list[Instance]:
    instances = _discover_from_env()
    ordered = [instances[key] for key in sorted(instances)]
    if not include_ssm:
        return ordered

    ssm_map = _ssm_status_map()
    enriched: list[Instance] = []
    for inst in ordered:
        ssm = ssm_map.get(inst.instance_id, {})
        enriched.append(
            Instance(
                alias=inst.alias,
                instance_id=inst.instance_id,
                private_ip=inst.private_ip,
                public_ip=inst.public_ip,
                ssm_status=ssm.get("ping_status"),
                computer_name=ssm.get("computer_name"),
            )
        )
    return enriched


def get_instance(alias: str) -> Instance:
    instances = _discover_from_env()
    key = _normalize_alias(alias)
    if key not in instances:
        known = ", ".join(sorted(instances))
        raise RuntimeError(f"Unknown instance alias '{alias}'. Known: {known}")
    for inst in list_instances(include_ssm=True):
        if inst.alias == key:
            return inst
    return instances[key]


def _ssm_status_map() -> dict[str, dict[str, str]]:
    client = aws_session().client("ssm", region_name=aws_region())
    result: dict[str, dict[str, str]] = {}
    token: str | None = None
    while True:
        kwargs: dict[str, object] = {}
        if token:
            kwargs["NextToken"] = token
        response = client.describe_instance_information(**kwargs)
        for row in response.get("InstanceInformationList", []):
            instance_id = row.get("InstanceId", "")
            if not instance_id:
                continue
            result[instance_id] = {
                "ping_status": row.get("PingStatus", "Unknown"),
                "computer_name": row.get("ComputerName", ""),
                "ip_address": row.get("IPAddress", ""),
            }
        token = response.get("NextToken")
        if not token:
            break
    return result


def fetch_live_instances(name_prefix: str) -> list[dict[str, str | None]]:
    ec2 = aws_session().client("ec2", region_name=aws_region())
    response = ec2.describe_instances(
        Filters=[{"Name": "tag:Name", "Values": [f"{name_prefix}*"]}],
    )
    rows: list[dict[str, str | None]] = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            name = ""
            for tag in instance.get("Tags", []):
                if tag.get("Key") == "Name":
                    name = tag.get("Value", "")
                    break
            rows.append(
                {
                    "name": name,
                    "instance_id": instance.get("InstanceId", ""),
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "state": instance.get("State", {}).get("Name", ""),
                }
            )
    return sorted(rows, key=lambda row: str(row.get("name") or ""))
