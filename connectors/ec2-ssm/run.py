"""ec2-ssm: list AWS EC2 servers and run commands on them through SSM. Read-only commands unless --write."""
import argparse
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as c  # noqa: E402

c.load_env(HERE)

# Read-only mode: every pipeline segment must start with one of these.
LINUX_READ = {
    "cat", "head", "tail", "ls", "df", "du", "free", "uptime", "ps", "whoami", "hostname", "id", "date",
    "uname", "grep", "egrep", "zgrep", "zcat", "wc", "sort", "uniq", "cut", "tr", "column", "journalctl",
    "netstat", "ss", "ip", "ifconfig", "lsblk", "stat", "file", "which", "dmesg", "last", "w", "nproc",
    "lscpu", "pwd", "tac", "md5sum", "sha256sum", "getent", "nslookup", "dig", "ping",
}
LINUX_READ_PAIRS = {
    "systemctl status", "systemctl is-active", "systemctl is-enabled", "systemctl list-units",
    "docker ps", "docker logs", "docker images", "docker stats",
}
FIND_WRITE_FLAGS = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0", "-fprintf", "-fls"}

# PowerShell: every command position (start, after |, inside ( ) and { }, after =) must hold a read-only command.
WINDOWS_READ = {
    "out-string", "out-null", "ipconfig", "hostname", "whoami", "systeminfo", "netstat", "tasklist", "findstr",
    "nslookup", "ping", "dir", "type", "ls", "cat", "gci", "gc", "gi", "gp", "gps", "ps", "gsv", "gcim", "gwmi",
    "select", "where", "sort", "ft", "fl", "measure", "group", "sls", "%", "?", "foreach",
    "if", "elseif", "else",
}
WINDOWS_READ_VERB = re.compile(r"(?i)^(get|test|resolve|measure|select|where|sort|format|group|compare|convertto|convertfrom|foreach)-\w+$")
WINDOWS_SAFE_METHODS = {
    "tostring", "startswith", "endswith", "contains", "tolower", "toupper", "trim", "trimstart", "trimend", "split",
    "substring", "replace", "indexof", "equals", "gettype", "padleft", "padright", "length", "count",
}
# Chaining, redirects, sub-shells, call operators, and static .NET calls are never allowed in read-only mode.
LINUX_BLOCK = re.compile(r"[;&><`\n\r]|\$\(")
WINDOWS_BLOCK = re.compile(r"[;&><`\n\r]|\$\(|::")
_PS_TOKEN = re.compile(r"@\{|[|{}()=]|'(?:[^']|'')*'|\"[^\"]*\"|[^\s|{}()='\"]+")


def _extra_read():
    return {x.strip().lower() for x in (c.setting("EC2_SSM_EXTRA_READ_COMMANDS") or "").split(",") if x.strip()}


def _linux_problem(command, extra):
    for segment in command.split("|"):
        words = segment.split()
        if not words:
            return "an empty pipe segment"
        first, pair = words[0], " ".join(words[:2]).lower()
        if first == "find" and not FIND_WRITE_FLAGS & set(words):
            continue
        if first == "top" and "-b" in words:
            continue
        if not (first in LINUX_READ or pair in LINUX_READ_PAIRS or first.lower() in extra or pair in extra):
            return f"'{first}' (not on the read-only list)"
    return None


def _windows_problem(command, extra):
    for m in re.finditer(r"\.\s*([A-Za-z_]\w*)\s*\(", command):
        if m.group(1).lower() not in WINDOWS_SAFE_METHODS:
            return f"the method call '.{m.group(1)}()'"
    expect_command = True
    for tok in _PS_TOKEN.findall(command):
        if tok in ("|", "{", "(", "="):
            expect_command = True
        elif tok in ("@{", ")", "}"):
            expect_command = False      # @{ starts a hashtable, not a script block
        elif expect_command:
            expect_command = False
            word = tok.lower()
            if tok[0] in "$'\"[-" or tok[0].isdigit():
                continue                # a value, not a command
            if not (word in WINDOWS_READ or WINDOWS_READ_VERB.match(word) or word in extra):
                return f"'{tok}' (not on the read-only list)"
    return None


def check_read_only(command, windows):
    """Raise unless the command only reads. Returns nothing when the command is allowed."""
    blocked = (WINDOWS_BLOCK if windows else LINUX_BLOCK).search(command)
    if blocked:
        bad = f"'{blocked.group()}'" if blocked.group().strip() else "a line break"
    else:
        bad = (_windows_problem if windows else _linux_problem)(command, _extra_read())
    if bad:
        raise c.ConnectorError(
            f"This command is not allowed in read-only mode because of {bad}.",
            "Use a simpler read-only command. If it must change something, ask the user, then add --write.")


def _aws(service):
    try:
        import boto3
    except ImportError:
        raise c.ConnectorError("The boto3 package is not installed.",
                               "Run: pip install -r connectors/requirements.txt") from None
    return boto3.client(service, region_name=c.setting("AWS_REGION"))


def _aws_call(fn, **kwargs):
    from botocore.exceptions import BotoCoreError, ClientError
    try:
        return fn(**kwargs)
    except ClientError as e:
        raise c.ConnectorError(f"AWS error: {e.response.get('Error', {}).get('Message', e)}",
                               "Check AWS_PROFILE, AWS_REGION, permissions, and your AWS login.") from None
    except BotoCoreError as e:
        raise c.ConnectorError(f"AWS error: {e}", "Check AWS_PROFILE, AWS_REGION and your AWS login.") from None


def _names(ids):
    ec2_ids = [i for i in ids if i.startswith("i-")]
    if not ec2_ids:
        return {}
    res = _aws_call(_aws("ec2").describe_instances, InstanceIds=ec2_ids)
    names = {}
    for r in res["Reservations"]:
        for inst in r["Instances"]:
            tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
            names[inst["InstanceId"]] = tags.get("Name", "")
    return names


def _managed(filters=None):
    ssm = _aws("ssm")
    pages = ssm.get_paginator("describe_instance_information").paginate(Filters=filters or [])
    out = []
    from botocore.exceptions import BotoCoreError, ClientError
    try:
        for page in pages:
            out += page["InstanceInformationList"]
    except (ClientError, BotoCoreError) as e:
        raise c.ConnectorError(f"AWS error: {e}", "Check AWS_PROFILE, AWS_REGION, permissions, and your AWS login.") from None
    return out


def resolve(target):
    """Instance ID, or the value of the Name tag."""
    if re.match(r"^(i|mi)-[0-9a-f]+$", target):
        return target
    res = _aws_call(_aws("ec2").describe_instances,
                    Filters=[{"Name": "tag:Name", "Values": [target]},
                             {"Name": "instance-state-name", "Values": ["running"]}])
    ids = [i["InstanceId"] for r in res["Reservations"] for i in r["Instances"]]
    if not ids:
        raise c.ConnectorError(f"No running server named '{target}'.", "Run 'list' to see server names and IDs.")
    if len(ids) > 1:
        raise c.ConnectorError(f"Several servers are named '{target}': {', '.join(ids)}.", "Use an instance ID.")
    return ids[0]


def cmd_test(args):
    ident = _aws_call(_aws("sts").get_caller_identity)
    print(f"AWS login OK: account {ident['Account']}, {ident['Arn']}")
    print(f"Servers reachable through SSM in {c.setting('AWS_REGION', 'default region')}: {len(_managed())}")


def cmd_list(args):
    infos = _managed()
    names = _names([i["InstanceId"] for i in infos])
    rows = [[i["InstanceId"], names.get(i["InstanceId"], ""), i.get("PingStatus", ""), i.get("PlatformType", ""),
             i.get("PlatformName", ""), i.get("IPAddress", ""), i.get("ComputerName", "")] for i in infos]
    if args.filter:
        rows = [r for r in rows if args.filter.lower() in " ".join(r).lower()]
    rows.sort(key=lambda r: r[1])
    c.show_table(rows, ["instance_id", "name", "ssm", "platform", "os", "ip", "computer"], "ec2-ssm", limit=args.limit)


def cmd_run(args):
    instance = resolve(args.target)
    infos = _managed([{"Key": "InstanceIds", "Values": [instance]}])
    if not infos:
        raise c.ConnectorError(f"{instance} is not managed by SSM.", "The SSM agent must be installed and the server must have an SSM role.")
    info = infos[0]
    if info.get("PingStatus") != "Online":
        raise c.ConnectorError(f"{instance} SSM status is {info.get('PingStatus')}.", "The server must be running and its SSM agent online.")
    windows = info.get("PlatformType") == "Windows"

    if args.write:
        c.require_write(args, "run --write")
    else:
        check_read_only(args.command, windows)

    ssm = _aws("ssm")
    sent = _aws_call(ssm.send_command, InstanceIds=[instance],
                     DocumentName="AWS-RunPowerShellScript" if windows else "AWS-RunShellScript",
                     Parameters={"commands": [args.command], "executionTimeout": [str(args.timeout)]},
                     Comment="super-dev ec2-ssm connector")
    command_id = sent["Command"]["CommandId"]

    from botocore.exceptions import ClientError
    deadline = time.time() + args.timeout + 30
    while True:
        time.sleep(2)
        try:
            inv = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "InvocationDoesNotExist" and time.time() < deadline:
                continue
            raise c.ConnectorError(f"AWS error: {e}") from None
        if inv["Status"] not in ("Pending", "InProgress", "Delayed"):
            break
        if time.time() > deadline:
            raise c.ConnectorError(f"Command {command_id} still running after {args.timeout}s.", "Use a faster command, or raise --timeout.")

    print(f"Server: {instance} ({info.get('PlatformType')})  Status: {inv['Status']}  Exit code: {inv.get('ResponseCode')}")
    out = inv.get("StandardOutputContent", "")
    err = inv.get("StandardErrorContent", "")
    text = out + (f"\n--- stderr ---\n{err}" if err.strip() else "")
    c.show_text(text or "(no output)", "ec2-ssm-run")


def main():
    p = argparse.ArgumentParser(description="List EC2 servers and run commands through SSM (read-only unless --write).")
    sub = p.add_subparsers(dest="command_name", required=True)

    sub.add_parser("test", help="check AWS login and SSM access").set_defaults(func=cmd_test)

    s = sub.add_parser("list", help="list servers managed by SSM")
    s.add_argument("--filter", help="only rows containing this text")
    s.add_argument("--limit", type=int, default=100)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("run", help="run a shell (Linux) or PowerShell (Windows) command on one server")
    s.add_argument("target", help="instance ID or Name tag")
    s.add_argument("command", help="command text, in quotes")
    s.add_argument("--timeout", type=int, default=120, help="seconds (default 120)")
    s.add_argument("--write", action="store_true", help="allow any command; needs the user's permission")
    s.set_defaults(func=cmd_run)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    c.run(main)
