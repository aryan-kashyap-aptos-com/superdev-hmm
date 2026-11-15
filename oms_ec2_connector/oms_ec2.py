#!/usr/bin/env python3
"""OMS EC2 connector CLI — remote PowerShell via AWS SSM.

Usage:
  python oms_ec2.py --env .env.pod2dev list
  python oms_ec2.py --env .env.pod2dev test sitemanager
  python oms_ec2.py --env .env.pod2dev exec sitemanager "Get-Website | Select Name,State"
  python oms_ec2.py --env .env.pod2dev script sitemanager ..\\path\\to\\script.ps1
  python oms_ec2.py --env .env.pod2dev refresh
"""

from __future__ import annotations

import argparse
import sys

from client import env_name, load_env, set_env_file
from instances import fetch_live_instances, get_instance, list_instances
from ssm_exec import run_powershell, run_script_file


def _alias_to_env_key(alias: str) -> str:
    return alias.upper().replace("-", "_")


def cmd_list(_: argparse.Namespace) -> int:
    load_env()
    print(f"Environment: {env_name()}")
    print(f"{'ALIAS':<16} {'INSTANCE ID':<22} {'PRIVATE IP':<16} {'PUBLIC IP':<16} {'SSM':<10}")
    print("-" * 88)
    for inst in list_instances(include_ssm=True):
        public = inst.public_ip or "-"
        ssm = inst.ssm_status or "NotManaged"
        print(f"{inst.alias:<16} {inst.instance_id:<22} {inst.private_ip:<16} {public:<16} {ssm:<10}")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    inst = get_instance(args.alias)
    print(f"Alias       : {inst.alias}")
    print(f"Instance ID : {inst.instance_id}")
    print(f"Private IP  : {inst.private_ip}")
    if inst.public_ip:
        print(f"Public IP   : {inst.public_ip}")
    print(f"SSM status  : {inst.ssm_status or 'NotManaged'}")
    if inst.computer_name:
        print(f"Computer    : {inst.computer_name}")

    if inst.ssm_status != "Online":
        print("ERROR: Instance is not SSM Online. exec/script will not work until SSM is enabled.")
        return 1

    result = run_powershell(inst, "hostname; Get-Date -Format o")
    print(f"Command     : {result['status']}")
    if result["stdout"]:
        print(result["stdout"].rstrip())
    if result["stderr"]:
        print(result["stderr"].rstrip(), file=sys.stderr)
    return 0 if result["status"] == "Success" else 1


def cmd_exec(args: argparse.Namespace) -> int:
    inst = get_instance(args.alias)
    result = run_powershell(inst, args.command, timeout_seconds=args.timeout)
    if result["stdout"]:
        print(result["stdout"].rstrip())
    if result["stderr"]:
        print(result["stderr"].rstrip(), file=sys.stderr)
    if result["status"] != "Success":
        print(f"ERROR: SSM command {result['status']} ({result['command_id']})", file=sys.stderr)
        return 1
    return 0


def cmd_script(args: argparse.Namespace) -> int:
    inst = get_instance(args.alias)
    result = run_script_file(inst, args.script, timeout_seconds=args.timeout)
    if result["stdout"]:
        print(result["stdout"].rstrip())
    if result["stderr"]:
        print(result["stderr"].rstrip(), file=sys.stderr)
    if result["status"] != "Success":
        print(f"ERROR: SSM command {result['status']} ({result['command_id']})", file=sys.stderr)
        return 1
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    load_env()
    rows = fetch_live_instances(args.prefix)
    if not rows:
        print(f"No instances found for prefix '{args.prefix}'")
        return 1

    print(f"# Refresh snapshot for {env_name()} ({args.prefix}*)")
    print(f"# Generated from live AWS describe-instances")
    print()
    for row in rows:
        name = str(row.get("name") or "")
        alias = name.replace(args.prefix, "").strip("-").lower()
        if not alias:
            alias = "bastion" if "bastion" in name.lower() else name
        key = _alias_to_env_key(alias)
        instance_id = row.get("instance_id") or ""
        private_ip = row.get("private_ip") or ""
        public_ip = row.get("public_ip")
        state = row.get("state") or ""
        print(f"# {name} ({state})")
        print(f"INSTANCE_{key}_ID={instance_id}")
        print(f"INSTANCE_{key}_IP={private_ip}")
        if public_ip:
            print(f"INSTANCE_{key}_PUBLIC_IP={public_ip}")
        print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OMS EC2 connector (SSM PowerShell)")
    parser.add_argument("--env", default=".env.pod2dev", help="Path to env file (default: .env.pod2dev)")
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List configured instances")
    list_cmd.set_defaults(func=cmd_list)

    test = sub.add_parser("test", help="Test SSM connectivity to one instance")
    test.add_argument("alias", help="Instance alias (e.g. sitemanager, api, toronado)")
    test.set_defaults(func=cmd_test)

    exec_cmd = sub.add_parser("exec", help="Run a PowerShell command via SSM")
    exec_cmd.add_argument("alias")
    exec_cmd.add_argument("command", help="PowerShell to run on the instance")
    exec_cmd.add_argument("--timeout", type=int, default=120)
    exec_cmd.set_defaults(func=cmd_exec)

    script = sub.add_parser("script", help="Run a local .ps1 file on the instance via SSM")
    script.add_argument("alias")
    script.add_argument("script", help="Path to .ps1 file")
    script.add_argument("--timeout", type=int, default=300)
    script.set_defaults(func=cmd_script)

    refresh = sub.add_parser("refresh", help="Print env lines from live AWS instance data")
    refresh.add_argument("--prefix", default="oms-pod2-dev-", help="EC2 Name tag prefix")
    refresh.set_defaults(func=cmd_refresh)

    args = parser.parse_args()
    set_env_file(args.env)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
