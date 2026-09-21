"""Run PowerShell on EC2 via SSM."""

from __future__ import annotations

import time
from typing import Sequence

from botocore.exceptions import ClientError

from aws_env import aws_region, aws_session

DOCUMENT = "AWS-RunPowerShellScript"
POLL_SECONDS = 1.25
INVOCATION_WARMUP_SECONDS = 0.35


def ssm_ping_status(instance_id: str) -> str:
    client = aws_session().client("ssm", region_name=aws_region())
    response = client.describe_instance_information(
        Filters=[{"Key": "InstanceIds", "Values": [instance_id]}],
    )
    rows = response.get("InstanceInformationList", [])
    if not rows:
        return "NotManaged"
    return rows[0].get("PingStatus", "Unknown")


def run_powershell(
    instance_id: str,
    commands: Sequence[str],
    timeout_seconds: int = 180,
) -> dict[str, str]:
    client = aws_session().client("ssm", region_name=aws_region())
    response = client.send_command(
        InstanceIds=[instance_id],
        DocumentName=DOCUMENT,
        Parameters={"commands": list(commands)},
        TimeoutSeconds=timeout_seconds,
    )
    command_id = response["Command"]["CommandId"]
    time.sleep(INVOCATION_WARMUP_SECONDS)
    deadline = time.time() + timeout_seconds + 60
    while time.time() < deadline:
        try:
            result = client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code == "InvocationDoesNotExist":
                time.sleep(POLL_SECONDS)
                continue
            raise
        status = result.get("Status", "")
        if status in {"Pending", "InProgress", "Delayed"}:
            time.sleep(POLL_SECONDS)
            continue
        if status in {"Success", "Cancelled", "TimedOut", "Failed", "Cancelling"}:
            return {
                "status": status,
                "stdout": result.get("StandardOutputContent", "") or "",
                "stderr": result.get("StandardErrorContent", "") or "",
                "command_id": command_id,
            }
        time.sleep(POLL_SECONDS)
    raise TimeoutError(f"SSM command {command_id} timed out on {instance_id}")


PS_HOST_META = r"""
$ErrorActionPreference = 'SilentlyContinue'
$bios = Get-CimInstance Win32_BIOS
@{ SerialNumber = $bios.SerialNumber; ComputerName = $env:COMPUTERNAME } | ConvertTo-Json -Compress
""".strip()

PS_LIST_OMS_SERVICES = r"""
$ErrorActionPreference = 'Stop'
Get-Service | Where-Object { $_.Name -like 'OMS-*' } | ForEach-Object {
  [PSCustomObject]@{
    Name = $_.Name
    Status = $_.Status.ToString()
    StartType = $_.StartType.ToString()
  }
} | Sort-Object Name | ConvertTo-Json -Compress
""".strip()

PS_LIST_IIS = r"""
$ErrorActionPreference = 'Stop'
Import-Module WebAdministration
$sites = @(Get-Website | ForEach-Object {
  $path = $_.physicalPath
  [PSCustomObject]@{
    Name = $_.Name
    State = [string]$_.State
    AppPool = $_.applicationPool
    PhysicalPath = $path
  }
})
$pools = @(Get-IISAppPool | ForEach-Object {
  [PSCustomObject]@{ Name = $_.Name; State = [string]$_.State }
})
@{ Sites = $sites; AppPools = $pools } | ConvertTo-Json -Compress -Depth 4
""".strip()


def ps_tail_shoplogic_debug_bases(bases: list[str], lines: int = 120) -> str:
    escaped_paths = [b.replace("'", "''") for b in bases]
    ps_list = ", ".join(f"'{p}'" for p in escaped_paths)
    return f"""
$ErrorActionPreference = 'SilentlyContinue'
$bases = @({ps_list})
$names = @('ShopLogic.debug','ShopLogic.Debug.log','ShopLogic-Debug.log','shoplogic.debug')
$file = $null
$usedBase = $null
foreach ($base in $bases) {{
  if (-not (Test-Path -LiteralPath $base)) {{ continue }}
  $usedBase = $base
  $candidates = @()
  foreach ($n in $names) {{ $candidates += Join-Path $base $n }}
  $found = Get-ChildItem -LiteralPath $base -Recurse -Depth 3 -File -ErrorAction SilentlyContinue |
    Where-Object {{ $_.Name -match 'ShopLogic' -and $_.Name -match 'debug|Debug' }} |
    Sort-Object LastWriteTime -Descending
  foreach ($f in $found) {{ $candidates += $f.FullName }}
  $file = $candidates | Where-Object {{ Test-Path -LiteralPath $_ }} | Select-Object -First 1
  if ($file) {{ break }}
}}
if (-not $file) {{
  Write-Output "NO_LOG: ShopLogic debug not found on this server."
  Write-Output "Tried paths:"
  $bases | ForEach-Object {{ Write-Output "  $_" }}
  exit 0
}}
Write-Output "=== Host path: $usedBase ==="
Write-Output "=== Log file: $file ==="
Get-Content -LiteralPath $file -Tail {lines} -ErrorAction Stop
""".strip()


def ps_tail_shoplogic_debug(physical_path: str, lines: int = 120) -> str:
    from path_candidates import shoplogic_path_candidates

    return ps_tail_shoplogic_debug_bases(shoplogic_path_candidates(physical_path), lines)


def ps_tail_toro_logs(service_name: str, lines: int = 80) -> str:
    safe = service_name.replace("'", "''")
    return f"""
$ErrorActionPreference = 'SilentlyContinue'
$svcName = '{safe}'
$svc = Get-CimInstance Win32_Service -Filter "Name='$svcName'"
$installDir = $null
if ($svc -and $svc.PathName) {{
  $path = $svc.PathName.Trim().Trim('"')
  $installDir = Split-Path -Parent $path
}}
if (-not $installDir -or -not (Test-Path $installDir)) {{
  $installDir = Join-Path 'D:\\torojobs' $svcName
}}
$searchRoots = @($installDir)
$searchRoots += @(
  (Join-Path $installDir 'log'),
  (Join-Path $installDir 'logs'),
  (Join-Path 'D:\\torojobs' $svcName),
  (Join-Path (Join-Path 'D:\\torojobs' $svcName) 'log')
) | Where-Object {{ $_ -and (Test-Path $_) }} | Select-Object -Unique
$log = $null
foreach ($root in $searchRoots) {{
  $log = Get-ChildItem -Path $root -Recurse -Depth 4 -File -Include *.log,*.txt -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($log) {{ break }}
}}
if (-not $log) {{
  Write-Output "NO_LOG for service $svcName"
  Write-Output "Install dir: $installDir"
  Write-Output "Checked:"
  $searchRoots | ForEach-Object {{ Write-Output "  $_" }}
  Write-Output "Files in install dir (top 20):"
  Get-ChildItem -Path $installDir -ErrorAction SilentlyContinue | Select-Object -First 20 Name, LastWriteTime | Format-Table -AutoSize | Out-String
  exit 0
}}
Write-Output "=== $($log.FullName) ==="
Get-Content -Path $log.FullName -Tail {lines} -ErrorAction Stop
""".strip()


def ps_service_status(service_name: str) -> str:
    safe = service_name.replace("'", "''")
    return (
        f"$s = Get-Service -Name '{safe}' -ErrorAction SilentlyContinue; "
        f"if (-not $s) {{ '{{\"Status\":\"Missing\"}}' }} else "
        f"{{ $s | Select-Object Name, @{{N='Status';E={{$_.Status.ToString()}}}} | ConvertTo-Json -Compress }}"
    )


def ps_website_state(site_name: str) -> str:
    safe = site_name.replace("'", "''")
    return (
        f"Import-Module WebAdministration -ErrorAction Stop; "
        f"$w = Get-Website -Name '{safe}' -ErrorAction SilentlyContinue; "
        f"if (-not $w) {{ '{{\"State\":\"Missing\"}}' }} else "
        f"{{ $pool = $w.applicationPool; $ps = (Get-WebAppPoolState -Name $pool).Value; "
        f"@{{ Name='{safe}'; State=[string]$w.State; AppPool=$pool; PoolState=[string]$ps }} | ConvertTo-Json -Compress }}"
    )


def ps_app_pool_state(pool_name: str) -> str:
    safe = pool_name.replace("'", "''")
    return (
        f"Import-Module WebAdministration -ErrorAction Stop; "
        f"@{{ Pool='{safe}'; PoolState=[string](Get-WebAppPoolState -Name '{safe}').Value }} | ConvertTo-Json -Compress"
    )


def ps_list_directory(path: str) -> str:
    """List folder + server clock in one SSM round-trip."""
    safe = path.replace("'", "''")
    return f"""
$ErrorActionPreference = 'Stop'
$p = '{safe}'
if (-not (Test-Path -LiteralPath $p)) {{ throw "PATH_NOT_FOUND: $p" }}
$items = @(Get-ChildItem -LiteralPath $p -Force | ForEach-Object {{
  [PSCustomObject]@{{
    Name = $_.Name
    IsDirectory = [bool]$_.PSIsContainer
    Length = if ($_.PSIsContainer) {{ 0 }} else {{ [long]$_.Length }}
    LastWriteTime = $_.LastWriteTime.ToString('o')
  }}
}})
if ($items.Count -gt 0) {{
  $items = $items | Sort-Object @{{Expression='IsDirectory';Descending=$true}}, Name
}}
@{{ 
  Server = @{{
    ComputerName = $env:COMPUTERNAME
    ServerTimeLocal = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    ServerTimeUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss')
    TimeZone = [System.TimeZoneInfo]::Local.Id
  }}
  Items = @($items)
}} | ConvertTo-Json -Compress -Depth 5
""".strip()


def ssm_failed_message(result: dict[str, str]) -> str:
    from ui_helpers import format_ssm_error

    return format_ssm_error(
        result.get("stderr", ""),
        result.get("stdout", ""),
        result.get("status", ""),
    )


def ps_file_length(path: str) -> str:
    safe = path.replace("'", "''")
    return (
        f"$p = '{safe}'; if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {{ throw 'NOT_A_FILE' }}; "
        f"(Get-Item -LiteralPath $p).Length"
    )


def ps_read_file_chunk_base64(path: str, offset: int, length: int) -> str:
    safe = path.replace("'", "''")
    return f"""
$ErrorActionPreference = 'Stop'
$p = '{safe}'
$offset = {offset}
$length = {length}
$fs = [System.IO.File]::Open($p, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
try {{
  $fs.Seek($offset, [System.IO.SeekOrigin]::Begin) | Out-Null
  $buf = New-Object byte[] $length
  $read = $fs.Read($buf, 0, $length)
  @{{ Offset = $offset; Read = $read; Base64 = [Convert]::ToBase64String($buf, 0, $read) }} | ConvertTo-Json -Compress
}} finally {{
  $fs.Close()
}}
""".strip()


def ps_tail_text_file(path: str, tail_lines: int = 200, max_bytes: int = 524_288) -> str:
    """Read tail of a text file on the remote host (for log/config preview)."""
    safe = path.replace("'", "''")
    return f"""
$ErrorActionPreference = 'Stop'
$p = '{safe}'
if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {{ throw "NOT_A_FILE: $p" }}
$len = (Get-Item -LiteralPath $p).Length
Write-Output "=== $p ($len bytes) ==="
if ($len -gt {max_bytes}) {{
  Get-Content -LiteralPath $p -Tail {tail_lines} -ErrorAction Stop
}} else {{
  Get-Content -LiteralPath $p -ErrorAction Stop
}}
""".strip()


def ps_read_file_base64(path: str, max_bytes: int = 8_388_608) -> str:
    safe = path.replace("'", "''")
    return f"""
$ErrorActionPreference = 'Stop'
$p = '{safe}'
if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {{ throw "NOT_A_FILE: $p" }}
$len = (Get-Item -LiteralPath $p).Length
if ($len -gt {max_bytes}) {{ throw "FILE_TOO_LARGE: $len bytes (max {max_bytes})" }}
@{{ Path = $p; Length = $len; Base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($p)) }} | ConvertTo-Json -Compress
""".strip()


def ps_service_action(service_name: str, action: str) -> str:
    safe = service_name.replace("'", "''")
    if action == "restart":
        return f"Restart-Service -Name '{safe}' -Force -ErrorAction Stop"
    if action == "start":
        return f"Start-Service -Name '{safe}' -ErrorAction Stop"
    if action == "stop":
        return f"Stop-Service -Name '{safe}' -Force -ErrorAction Stop"
    raise ValueError(f"Unknown action: {action}")


def ps_iis_recycle_pool(pool_name: str) -> str:
    safe = pool_name.replace("'", "''")
    return f"Import-Module WebAdministration; Restart-WebAppPool -Name '{safe}'"


def ps_iis_site_action(site_name: str, action: str) -> str:
    safe = site_name.replace("'", "''")
    if action == "start":
        return f"Import-Module WebAdministration; Start-Website -Name '{safe}'"
    if action == "stop":
        return f"Import-Module WebAdministration; Stop-Website -Name '{safe}'"
    if action == "restart":
        return (
            f"Import-Module WebAdministration; Stop-Website -Name '{safe}' -ErrorAction SilentlyContinue; "
            f"Start-Sleep -Seconds 2; Start-Website -Name '{safe}'"
        )
    raise ValueError(action)
