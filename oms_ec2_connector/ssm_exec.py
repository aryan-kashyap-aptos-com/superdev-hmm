"""Run PowerShell on EC2 instances via AWS Systems Manager."""

from __future__ import annotations

import time
from pathlib import Path

from client import aws_region, aws_session, load_env
from instances import Instance

DOCUMENT = "AWS-RunPowerShellScript"
DEFAULT_TIMEOUT_SECONDS = 120
POLL_INTERVAL_SECONDS = 2


def run_powershell(instance: Instance, command: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, str]:
    load_env()
    if instance.ssm_status and instance.ssm_status != "Online":
        raise RuntimeError(
            f"Instance '{instance.alias}' ({instance.instance_id}) is not SSM Online "
            f"(status={instance.ssm_status}). Enable SSM agent and AmazonSSMManagedInstanceCore."
        )

    client = aws_session().client("ssm", region_name=aws_region())
    response = client.send_command(
        InstanceIds=[instance.instance_id],
        DocumentName=DOCUMENT,
        Parameters={"commands": [command]},
        TimeoutSeconds=timeout_seconds,
    )
    command_id = response["Command"]["CommandId"]

    deadline = time.time() + timeout_seconds + 30
    while time.time() < deadline:
        result = client.get_command_invocation(CommandId=command_id, InstanceId=instance.instance_id)
        status = result.get("Status", "")
        if status in {"Success", "Cancelled", "TimedOut", "Failed", "Cancelling"}:
            return {
                "status": status,
                "stdout": result.get("StandardOutputContent", "") or "",
                "stderr": result.get("StandardErrorContent", "") or "",
                "command_id": command_id,
            }
        time.sleep(POLL_INTERVAL_SECONDS)

    raise RuntimeError(f"Timed out waiting for SSM command {command_id} on {instance.instance_id}")


def run_script_file(instance: Instance, script_path: str | Path, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, str]:
    path = Path(script_path)
    if not path.exists():
        raise RuntimeError(f"Script not found: {path}")
    content = path.read_text(encoding="utf-8-sig")
    return run_powershell(instance, content, timeout_seconds=timeout_seconds)
