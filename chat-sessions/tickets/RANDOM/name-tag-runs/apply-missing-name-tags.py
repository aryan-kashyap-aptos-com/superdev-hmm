#!/usr/bin/env python3
"""
Apply missing AWS resource tag key "Name" (exact, case-sensitive — same as Tag Editor).

Run with no arguments for an interactive wizard.
Non-interactive: --apply or --dry-run plus --region and optional --all-regions.

Requires: boto3, AWS credentials with tag permissions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterator

import boto3
from botocore.exceptions import ClientError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REGION = "us-east-1"
DEFAULT_WORKERS = 20

RESOURCE_TYPES = [
    "acm:certificate",
    "apigateway:apis",
    "apigateway:restapis",
    "autoscaling:autoScalingGroup",
    "backup:backup-plan",
    "backup:backup-vault",
    "cloudformation:stack",
    "cloudfront:distribution",
    "cloudwatch:alarm",
    "dynamodb:table",
    "ec2:elastic-ip",
    "ec2:image",
    "ec2:instance",
    "ec2:natgateway",
    "ec2:network-interface",
    "ec2:security-group",
    "ec2:snapshot",
    "ec2:volume",
    "ec2:vpc-endpoint",
    "ecr:repository",
    "ecs:cluster",
    "ecs:service",
    "ecs:task-definition",
    "eks:cluster",
    "elasticache:cluster",
    "elasticfilesystem:file-system",
    "elasticloadbalancing:loadbalancer",
    "elasticloadbalancing:targetgroup",
    "events:rule",
    "kinesis:stream",
    "kms:key",
    "lambda:function",
    "logs:log-group",
    "rds:cluster",
    "rds:db",
    "rds:pg",
    "rds:secgrp",
    "rds:snapshot",
    "rds:subgrp",
    "s3:bucket",
    "secretsmanager:secret",
    "sns:topic",
    "sqs:queue",
    "ssm:parameter",
    "states:stateMachine",
]

HTTP_API_NAMES_BY_REGION: dict[str, dict[str, str]] = {}
_CLIENT_CACHE: dict[str, dict[str, Any]] = {}
_CLIENT_LOCK = threading.Lock()
_JSONL_LOCK = threading.Lock()


@dataclass
class Candidate:
    region: str
    resource_type: str
    arn: str
    previous_tags: dict[str, str]
    applied_name_tag: str


@dataclass
class ScanStats:
    region: str
    total: int = 0
    already_named: int = 0
    missing_name: int = 0
    by_type_missing: dict[str, int] = field(default_factory=dict)
    by_type_total: dict[str, int] = field(default_factory=dict)


@dataclass
class RunConfig:
    dry_run: bool
    regions: list[str]
    workers: int
    skip_mq: bool
    ecs_check: bool
    output_dir: str
    no_color: bool
    non_interactive: bool


class Term:
    def __init__(self, use_color: bool) -> None:
        self.use = use_color and os.environ.get("NO_COLOR") is None

    def _wrap(self, code: str, text: str) -> str:
        if not self.use:
            return text
        return f"\033[{code}m{text}\033[0m"

    def bold(self, text: str) -> str:
        return self._wrap("1", text)

    def dim(self, text: str) -> str:
        return self._wrap("2", text)

    def green(self, text: str) -> str:
        return self._wrap("32", text)

    def yellow(self, text: str) -> str:
        return self._wrap("33", text)

    def red(self, text: str) -> str:
        return self._wrap("31", text)

    def cyan(self, text: str) -> str:
        return self._wrap("36", text)

    def magenta(self, text: str) -> str:
        return self._wrap("35", text)


class LiveStatus:
    """Spinner + status line (TTY only)."""

    _FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, term: Term) -> None:
        self.term = term
        self.enabled = sys.stdout.isatty() and term.use
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.label = "Working"
        self.detail = ""

    def set(self, label: str, detail: str = "") -> None:
        self.label = label
        self.detail = detail

    def __enter__(self) -> LiveStatus:
        if self.enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        if self.enabled:
            sys.stdout.write("\r" + " " * 100 + "\r")
            sys.stdout.flush()

    def _run(self) -> None:
        i = 0
        while not self._stop.is_set():
            frame = self._FRAMES[i % len(self._FRAMES)]
            line = f"{self.term.cyan(frame)} {self.term.bold(self.label)}"
            if self.detail:
                line += f"  {self.term.dim(self.detail)}"
            sys.stdout.write(f"\r{line[:110]:<110}")
            sys.stdout.flush()
            i += 1
            time.sleep(0.07)


def progress_bar(term: Term, done: int, total: int, width: int = 36) -> str:
    if total <= 0:
        return term.dim("[--------------------] 0%")
    pct = min(100, int(100 * done / total))
    filled = int(width * done / total)
    bar = "█" * filled + "░" * (width - filled)
    return f"{term.cyan('[')}{bar}{term.cyan(']')} {term.bold(str(pct))}%"


def print_progress_line(term: Term, done: int, total: int, label: str = "Progress") -> None:
    """One updating line (not a scrolling chart)."""
    line = f"  {label}: {progress_bar(term, done, total)}  {done}/{total}"
    if sys.stdout.isatty():
        # Strip ANSI for padding width is hard; pad generously
        sys.stdout.write("\r" + line + " " * 8)
        sys.stdout.flush()
    elif done == total:
        print(line)


def finish_progress_line() -> None:
    if sys.stdout.isatty():
        sys.stdout.write("\n")
        sys.stdout.flush()


def enable_windows_ansi() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def clear_screen(no_clear: bool) -> None:
    """Clear terminal when interactive TTY (menu clutter removed before the run)."""
    if no_clear or not sys.stdout.isatty():
        return
    if sys.platform == "win32":
        os.system("cls")  # noqa: S605 — reliable on Windows cmd/powershell
    else:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def print_banner(term: Term) -> None:
    line = "─" * 52
    print()
    print(term.cyan(line))
    print(term.bold(term.magenta("  AWS Name tag tool")))
    print(term.dim("  Tag key Name only (case-sensitive). Does not copy lowercase name."))
    print(term.cyan(line))


def print_rule(term: Term, title: str) -> None:
    print()
    print(term.bold(f"  {title}"))
    print(term.dim("  " + "·" * 48))


def print_config_panel(term: Term, config: RunConfig, run_dir: str) -> None:
    mode = term.cyan("DRY RUN") if config.dry_run else term.green("APPLY")
    reg = (
        ", ".join(config.regions)
        if len(config.regions) <= 2
        else f"{len(config.regions)} regions"
    )
    print()
    print(term.bold("  Ready"))
    print(f"    Mode      {mode}")
    print(f"    Region(s) {reg}")
    print(f"    Workers   {config.workers}")
    print(f"    Output    {term.dim(run_dir)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find resources missing Name and apply it.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--region", default=None)
    parser.add_argument("--all-regions", action="store_true")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--output-dir", default=SCRIPT_DIR)
    parser.add_argument("--skip-mq", action="store_true")
    parser.add_argument(
        "--ecs-check",
        action="store_true",
        help="Slow extra check: ECS task defs attached to services (off by default)",
    )
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Do not clear the terminal between setup and the run",
    )
    parser.add_argument("--non-interactive", action="store_true")
    return parser.parse_args()


def prompt_choice(term: Term, title: str, options: list[tuple[str, str]], default: str = "1") -> str:
    print_rule(term, title)
    for key, label in options:
        suffix = term.green("  ← default") if key == default else ""
        print(f"    {term.cyan(f'[{key}]')} {label}{suffix}")
    while True:
        raw = input(f"\n  {term.bold('Pick')} [{default}]: ").strip() or default
        if any(raw == k for k, _ in options):
            return raw
        print(term.red("  Invalid — try again."))


def list_account_regions() -> list[str]:
    ec2 = boto3.client("ec2", region_name=DEFAULT_REGION)
    return sorted(r["RegionName"] for r in ec2.describe_regions(AllRegions=False)["Regions"])


def resolve_config(args: argparse.Namespace, term: Term) -> RunConfig:
    interactive = not args.non_interactive and not args.dry_run and not args.apply

    if interactive:
        print_banner(term)
        mode_key = prompt_choice(
            term,
            "Mode",
            [
                ("1", "Dry run — scan and preview (no AWS tag writes)"),
                ("2", "Apply — scan, backup, write Name tags"),
            ],
        )
        dry_run = mode_key == "1"

        region_key = prompt_choice(
            term,
            "Region",
            [
                ("1", f"us-east-1 (default)"),
                ("2", "Another single region"),
                ("3", "All enabled regions in this account"),
            ],
        )
        if region_key == "1":
            regions = [DEFAULT_REGION]
        elif region_key == "2":
            r = input("  Region code (e.g. eu-west-1): ").strip()
            if not r:
                print(term.red("  Region required."))
                sys.exit(2)
            regions = [r]
        else:
            with LiveStatus(term) as live:
                live.set("Listing regions")
                regions = list_account_regions()
            print(f"  {term.dim(str(len(regions)))} regions selected.")

        if args.all_regions:
            regions = list_account_regions()
        elif args.region:
            regions = [args.region]

        workers = max(1, min(args.workers, 32))
        skip_mq = args.skip_mq
        ecs_check = args.ecs_check
        non_interactive = False
    else:
        if not args.dry_run and not args.apply:
            print("Use --dry-run or --apply with --non-interactive.", file=sys.stderr)
            sys.exit(2)
        dry_run = args.dry_run
        regions = (
            list_account_regions()
            if args.all_regions
            else [args.region or os.environ.get("AWS_REGION") or DEFAULT_REGION]
        )
        workers = max(1, min(args.workers, 32))
        skip_mq = args.skip_mq
        ecs_check = args.ecs_check
        non_interactive = True

    return RunConfig(
        dry_run=dry_run,
        regions=regions,
        workers=workers,
        skip_mq=skip_mq,
        ecs_check=ecs_check,
        output_dir=args.output_dir,
        no_color=args.no_color,
        non_interactive=non_interactive,
    )


# (predicate, resource_type) — first match wins
_ARN_RULES: list[tuple[Callable[[str], bool], str]] = [
    (lambda a: a.startswith("arn:aws:s3:::"), "s3:bucket"),
    (lambda a: ":apigateway:" in a and "/apis/" in a, "apigateway:apis"),
    (lambda a: ":apigateway:" in a and "/restapis/" in a, "apigateway:restapis"),
    (lambda a: ":autoscaling:" in a, "autoscaling:autoScalingGroup"),
    (lambda a: ":backup:" in a and "backup-plan" in a, "backup:backup-plan"),
    (lambda a: ":backup:" in a and "backup-vault" in a, "backup:backup-vault"),
    (lambda a: ":cloudformation:" in a, "cloudformation:stack"),
    (lambda a: ":cloudfront:" in a, "cloudfront:distribution"),
    (lambda a: ":cloudwatch:" in a, "cloudwatch:alarm"),
    (lambda a: ":dynamodb:" in a, "dynamodb:table"),
    (lambda a: ":elasticache:" in a, "elasticache:cluster"),
    (lambda a: ":elasticfilesystem:" in a, "elasticfilesystem:file-system"),
    (lambda a: ":elasticloadbalancing:" in a and "targetgroup/" in a, "elasticloadbalancing:targetgroup"),
    (lambda a: ":elasticloadbalancing:" in a, "elasticloadbalancing:loadbalancer"),
    (lambda a: ":events:" in a, "events:rule"),
    (lambda a: ":kinesis:" in a, "kinesis:stream"),
    (lambda a: ":kms:" in a, "kms:key"),
    (lambda a: ":lambda:" in a, "lambda:function"),
    (lambda a: ":logs:" in a, "logs:log-group"),
    (lambda a: ":states:" in a, "states:stateMachine"),
    (lambda a: ":sns:" in a, "sns:topic"),
    (lambda a: ":sqs:" in a, "sqs:queue"),
    (lambda a: ":secretsmanager:" in a, "secretsmanager:secret"),
    (lambda a: ":ssm:" in a, "ssm:parameter"),
    (lambda a: ":ecs:" in a and "task-definition/" in a, "ecs:task-definition"),
    (lambda a: ":ecs:" in a and "service/" in a, "ecs:service"),
    (lambda a: ":ecs:" in a and "cluster/" in a, "ecs:cluster"),
    (lambda a: ":eks:" in a, "eks:cluster"),
    (lambda a: ":ecr:" in a, "ecr:repository"),
    (lambda a: ":acm:" in a, "acm:certificate"),
    (lambda a: ":rds:" in a and ":cluster:" in a, "rds:cluster"),
    (lambda a: ":rds:" in a and ":snapshot:" in a, "rds:snapshot"),
    (lambda a: ":rds:" in a and ":pg:" in a, "rds:pg"),
    (lambda a: ":rds:" in a and ":subgrp:" in a, "rds:subgrp"),
    (lambda a: ":rds:" in a and ":secgrp:" in a, "rds:secgrp"),
    (lambda a: ":rds:" in a and ":db:" in a, "rds:db"),
    (lambda a: ":ec2:" in a and ":instance/" in a, "ec2:instance"),
    (lambda a: ":ec2:" in a and ":volume/" in a, "ec2:volume"),
    (lambda a: ":ec2:" in a and ":snapshot/" in a, "ec2:snapshot"),
    (lambda a: ":ec2:" in a and ":security-group/" in a, "ec2:security-group"),
    (lambda a: ":ec2:" in a and ":network-interface/" in a, "ec2:network-interface"),
    (lambda a: ":ec2:" in a and ":image/" in a, "ec2:image"),
    (lambda a: ":ec2:" in a and ":elastic-ip/" in a, "ec2:elastic-ip"),
    (lambda a: ":ec2:" in a and ":natgateway/" in a, "ec2:natgateway"),
    (lambda a: ":ec2:" in a and ":vpc-endpoint/" in a, "ec2:vpc-endpoint"),
]


def infer_resource_type(arn: str) -> str | None:
    for pred, rtype in _ARN_RULES:
        if pred(arn):
            return rtype
    return None


def has_exact_name(tags: dict[str, str]) -> bool:
    return "Name" in tags


def sanitize_apigw_tag_value(value: str) -> str:
    value = value.replace("$", "")
    value = re.sub(r"[^A-Za-z0-9 _.\:/=+\-@]", "-", value)
    return value[:256]


def short_arn(arn: str, max_len: int = 70) -> str:
    if len(arn) <= max_len:
        return arn
    return arn[: max_len - 3] + "..."


def get_clients(region: str) -> dict[str, Any]:
    with _CLIENT_LOCK:
        if region not in _CLIENT_CACHE:
            _CLIENT_CACHE[region] = {
                "tagging": boto3.client("resourcegroupstaggingapi", region_name=region),
                "apigw": boto3.client("apigatewayv2", region_name=region),
                "events": boto3.client("events", region_name=region),
                "cw": boto3.client("cloudwatch", region_name=region),
                "ec2": boto3.client("ec2", region_name=region),
                "ecs": boto3.client("ecs", region_name=region),
                "mq": boto3.client("mq", region_name=region),
            }
        return _CLIENT_CACHE[region]


def load_http_api_names(region: str) -> dict[str, str]:
    if region in HTTP_API_NAMES_BY_REGION:
        return HTTP_API_NAMES_BY_REGION[region]
    names: dict[str, str] = {}
    apigw = get_clients(region)["apigw"]
    token = None
    while True:
        kwargs = {"NextToken": token} if token else {}
        try:
            resp = apigw.get_apis(**kwargs)
        except ClientError:
            break
        for api in resp.get("Items", []):
            names[api["ApiId"]] = api.get("Name") or api["ApiId"]
        token = resp.get("NextToken")
        if not token:
            break
    HTTP_API_NAMES_BY_REGION[region] = names
    return names


def derive_name_value(arn: str, resource_type: str, region: str) -> str:
    http_names = HTTP_API_NAMES_BY_REGION.get(region, {})
    if resource_type == "s3:bucket":
        return arn.replace("arn:aws:s3:::", "").split("/")[0]
    if resource_type == "ssm:parameter":
        part = arn.split(":parameter", 1)[-1]
        return part if part.startswith("/") else f"/{part}"
    if resource_type == "secretsmanager:secret":
        tail = arn.split(":secret:", 1)[-1]
        return re.sub(r"-[A-Za-z0-9]{6}$", "", tail)
    if resource_type == "logs:log-group":
        return arn.split(":log-group:", 1)[-1].replace(":*", "").lstrip("/")
    if resource_type in {"ecs:service", "ecs:cluster"}:
        return arn.split("/")[-1]
    if resource_type == "ecs:task-definition":
        return arn.split("task-definition/", 1)[-1]
    if resource_type == "cloudformation:stack":
        return arn.split(":stack/", 1)[1].split("/")[0]
    if resource_type in {"elasticloadbalancing:loadbalancer", "elasticloadbalancing:targetgroup"}:
        if "loadbalancer/" in arn:
            return arn.split("loadbalancer/", 1)[-1].split("/")[1]
        return arn.split("targetgroup/", 1)[-1].split("/")[0]
    if resource_type == "apigateway:restapis":
        return arn.split("/")[-1]
    if resource_type == "apigateway:apis":
        if "/apis/" not in arn:
            return arn.split("/")[-1]
        api_id = arn.split("/apis/", 1)[1].split("/")[0]
        api_name = http_names.get(api_id, api_id)
        if "/stages/" in arn:
            stage = arn.split("/stages/", 1)[1]
            return sanitize_apigw_tag_value(f"{api_name}-{stage}")
        return api_name
    if resource_type == "states:stateMachine":
        return arn.split(":stateMachine:", 1)[-1]
    if resource_type in {"sns:topic", "sqs:queue"}:
        return arn.split(":")[-1]
    if resource_type == "events:rule":
        return arn.split(":rule/", 1)[-1].replace("/", "-")
    if resource_type == "lambda:function":
        return arn.split(":function:", 1)[-1]
    if resource_type == "cloudwatch:alarm":
        return arn.split(":alarm:", 1)[-1]
    if resource_type == "kms:key":
        return arn.split("key/", 1)[-1] if "key/" in arn else arn.split(":")[-1]
    if resource_type == "rds:db":
        return arn.split(":db:", 1)[-1]
    if resource_type == "rds:cluster":
        return arn.split(":cluster:", 1)[-1]
    if resource_type == "rds:pg":
        return arn.split(":pg:", 1)[-1]
    if resource_type == "rds:subgrp":
        return arn.split(":subgrp:", 1)[-1]
    if resource_type == "rds:secgrp":
        return arn.split(":secgrp:", 1)[-1]
    if resource_type == "rds:snapshot":
        return arn.split(":snapshot:", 1)[-1]
    if resource_type == "ec2:security-group":
        return arn.split("/")[-1]
    if "/" in arn:
        return arn.split("/")[-1]
    return arn.split(":")[-1]


def iter_tagged_resources(
    tagging: Any,
    on_progress: Callable[[int], None] | None = None,
) -> Iterator[dict]:
    """One paginated pass for all resource types (much faster than per-type scans)."""
    token = None
    total = 0
    while True:
        kwargs: dict[str, Any] = {
            "ResourceTypeFilters": RESOURCE_TYPES,
            "ResourcesPerPage": 100,
        }
        if token:
            kwargs["PaginationToken"] = token
        try:
            resp = tagging.get_resources(**kwargs)
        except ClientError:
            return
        batch = resp.get("ResourceTagMappingList", [])
        total += len(batch)
        if on_progress:
            on_progress(total)
        yield from batch
        token = resp.get("PaginationToken")
        if not token:
            break


def scan_region(
    region: str,
    skip_mq: bool,
    progress: Callable[[str, int], None] | None,
) -> tuple[ScanStats, list[Candidate]]:
    stats = ScanStats(region=region)
    pending: list[tuple[str, dict[str, str], str]] = []
    needs_apigw = False

    tagging = get_clients(region)["tagging"]

    def on_count(n: int) -> None:
        if progress:
            progress(region, n)

    for item in iter_tagged_resources(tagging, on_count):
        arn = item["ResourceARN"]
        rtype = infer_resource_type(arn)
        if not rtype:
            continue
        stats.total += 1
        stats.by_type_total[rtype] = stats.by_type_total.get(rtype, 0) + 1
        tags = {t["Key"]: t["Value"] for t in item.get("Tags", [])}
        if has_exact_name(tags):
            stats.already_named += 1
            continue
        stats.missing_name += 1
        stats.by_type_missing[rtype] = stats.by_type_missing.get(rtype, 0) + 1
        if rtype == "apigateway:apis":
            needs_apigw = True
        pending.append((arn, tags, rtype))

    if needs_apigw:
        load_http_api_names(region)

    candidates = [
        Candidate(
            region=region,
            resource_type=rtype,
            arn=arn,
            previous_tags=tags,
            applied_name_tag=derive_name_value(arn, rtype, region),
        )
        for arn, tags, rtype in pending
    ]

    if not skip_mq:
        mq = get_clients(region)["mq"]
        try:
            brokers = mq.list_brokers()["BrokerSummaries"]
        except ClientError:
            brokers = []
        for broker in brokers:
            arn = broker["BrokerArn"]
            name = broker["BrokerName"]
            tags = mq.list_tags(ResourceArn=arn).get("Tags", {})
            stats.total += 1
            stats.by_type_total["mq:broker"] = stats.by_type_total.get("mq:broker", 0) + 1
            if has_exact_name(tags):
                stats.already_named += 1
                continue
            stats.missing_name += 1
            stats.by_type_missing["mq:broker"] = stats.by_type_missing.get("mq:broker", 0) + 1
            candidates.append(
                Candidate(
                    region=region,
                    resource_type="mq:broker",
                    arn=arn,
                    previous_tags=dict(tags),
                    applied_name_tag=name,
                )
            )

    return stats, candidates


def merge_scan_stats(target: ScanStats, part: ScanStats) -> None:
    target.total += part.total
    target.already_named += part.already_named
    target.missing_name += part.missing_name
    for k, v in part.by_type_total.items():
        target.by_type_total[k] = target.by_type_total.get(k, 0) + v
    for k, v in part.by_type_missing.items():
        target.by_type_missing[k] = target.by_type_missing.get(k, 0) + v


def scan_all_regions(
    regions: list[str],
    skip_mq: bool,
    live: LiveStatus | None,
) -> tuple[ScanStats, list[Candidate]]:
    combined = ScanStats(region="(all)" if len(regions) > 1 else regions[0])
    all_candidates: list[Candidate] = []
    counts: dict[str, int] = {}

    def progress(region: str, n: int) -> None:
        counts[region] = n
        if live:
            total = sum(counts.values())
            live.set("Scanning resources", f"{region} · {total:,} listed")

    if len(regions) == 1:
        st, c = scan_region(regions[0], skip_mq, progress)
        merge_scan_stats(combined, st)
        return combined, c

    with ThreadPoolExecutor(max_workers=min(6, len(regions))) as pool:
        futs = {pool.submit(scan_region, r, skip_mq, progress): r for r in regions}
        for fut in as_completed(futs):
            st, cands = fut.result()
            merge_scan_stats(combined, st)
            all_candidates.extend(cands)
    return combined, all_candidates


def write_jsonl_bulk(path: str, records: list[dict]) -> None:
    if not records:
        return
    with open(path, "w", encoding="utf-8") as handle:
        for rec in records:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")


def append_jsonl(path: str, record: dict) -> None:
    with _JSONL_LOCK:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def apply_name_tag(cand: Candidate) -> None:
    clients = get_clients(cand.region)
    arn = cand.arn
    name_value = cand.applied_name_tag
    rtype = cand.resource_type

    if rtype == "mq:broker":
        clients["mq"].create_tags(ResourceArn=arn, Tags={"Name": name_value})
        return
    if rtype == "apigateway:apis" and "/stages/" in arn:
        clients["apigw"].tag_resource(ResourceArn=arn, Tags={"Name": name_value})
        return
    if rtype == "events:rule":
        clients["events"].tag_resource(ResourceARN=arn, Tags=[{"Key": "Name", "Value": name_value}])
        return
    if rtype == "cloudwatch:alarm":
        clients["cw"].tag_resource(ResourceARN=arn, Tags=[{"Key": "Name", "Value": name_value}])
        return
    if rtype == "ec2:security-group":
        sg_id = arn.split("/")[-1]
        clients["ec2"].create_tags(Resources=[sg_id], Tags=[{"Key": "Name", "Value": name_value}])
        return

    delay = 0.2
    for attempt in range(8):
        try:
            resp = clients["tagging"].tag_resources(ResourceARNList=[arn], Tags={"Name": name_value})
            failed = resp.get("FailedResourcesMap") or {}
            if arn in failed:
                raise ClientError({"Error": failed[arn]}, "TagResources")
            return
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"ThrottlingException", "TooManyRequestsException", "RequestLimitExceeded"} and attempt < 7:
                time.sleep(delay)
                delay *= 1.6
                continue
            raise


def apply_candidates(
    candidates: list[Candidate],
    dry_run: bool,
    workers: int,
    backup_jsonl: str,
    applied_jsonl: str,
    failed_jsonl: str,
    term: Term,
) -> tuple[list[dict], list[dict], int, int]:
    applied_records: list[dict] = []
    failed_records: list[dict] = []
    applied_n = 0
    failed_n = 0
    total = len(candidates)
    done_lock = threading.Lock()
    done = 0

    def work(cand: Candidate) -> tuple[str, dict | None, dict | None]:
        rec = {
            "region": cand.region,
            "resource_type": cand.resource_type,
            "arn": cand.arn,
            "previous_tags": cand.previous_tags,
            "applied_name_tag": cand.applied_name_tag,
        }
        if dry_run:
            return "would", {**rec, "action": "would_apply"}, None
        append_jsonl(backup_jsonl, rec)
        try:
            apply_name_tag(cand)
            append_jsonl(applied_jsonl, rec)
            return "ok", {**rec, "action": "applied"}, None
        except Exception as exc:
            fail = {**rec, "error": str(exc)}
            append_jsonl(failed_jsonl, fail)
            return "fail", None, fail

    action = "Preview (dry run)" if dry_run else "Apply"
    print_rule(term, action)
    print(f"  {total} resource(s) missing Name")

    if dry_run:
        for cand in candidates:
            rec = {
                "region": cand.region,
                "resource_type": cand.resource_type,
                "arn": cand.arn,
                "previous_tags": cand.previous_tags,
                "applied_name_tag": cand.applied_name_tag,
                "action": "would_apply",
            }
            applied_records.append(rec)
        applied_n = total
        print(f"  {term.cyan('No AWS calls')} — listed below is what Apply would tag.")
        return applied_records, failed_records, applied_n, failed_n

    print(f"  {term.dim(f'Tagging with {workers} workers…')}")
    label = "Tagging"

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(work, c) for c in candidates]
        for fut in as_completed(futures):
            status, ok_rec, fail_rec = fut.result()
            with done_lock:
                done += 1
                d = done
            if status == "ok":
                applied_n += 1
                if ok_rec:
                    applied_records.append(ok_rec)
            else:
                failed_n += 1
                if fail_rec:
                    failed_records.append(fail_rec)
            print_progress_line(term, d, total, label=label)

    finish_progress_line()
    print(f"  {term.green('Finished')} {applied_n} tagged, {failed_n} failed")

    return applied_records, failed_records, applied_n, failed_n


def audit_in_use_ecs_task_definitions(region: str) -> tuple[int, list[str]]:
    seen: set[str] = set()
    missing_arns: list[str] = []
    ecs = get_clients(region)["ecs"]
    try:
        clusters = ecs.list_clusters()["clusterArns"]
    except ClientError:
        return 0, []
    for cluster_arn in clusters:
        service_arns: list[str] = []
        paginator = ecs.get_paginator("list_services")
        for page in paginator.paginate(cluster=cluster_arn):
            service_arns.extend(page["serviceArns"])
        for i in range(0, len(service_arns), 10):
            batch = service_arns[i : i + 10]
            resp = ecs.describe_services(cluster=cluster_arn, services=batch)
            for svc in resp.get("services", []):
                td_arn = svc["taskDefinition"]
                if td_arn in seen:
                    continue
                seen.add(td_arn)
                tags_list = ecs.list_tags_for_resource(resourceArn=td_arn).get("tags", [])
                tags = {t["key"]: t["value"] for t in tags_list}
                if "Name" not in tags:
                    missing_arns.append(td_arn)
    return len(seen), missing_arns


def print_scan_report(term: Term, regions: list[str], scan: ScanStats, elapsed: float) -> None:
    print_rule(term, "Scan results")
    if len(regions) == 1:
        print(f"  Region     {regions[0]}")
    else:
        print(f"  Regions    {len(regions)}")
    print(f"  Time       {term.bold(f'{elapsed:.1f}s')}")
    print()
    print(f"  {term.bold('Checked'):<14} {scan.total:>8,}")
    print(f"  {term.green('Has Name'):<14} {scan.already_named:>8,}")
    print(f"  {term.yellow('Missing Name'):<14} {scan.missing_name:>8,}")

    if scan.by_type_missing:
        print()
        print(term.dim("  Where Name is missing (count by resource type):"))
        for rtype, count in sorted(scan.by_type_missing.items(), key=lambda x: (-x[1], x[0]))[:12]:
            print(f"    {term.yellow(f'{count:>4}')}  {rtype}")


def print_applied_report(term: Term, records: list[dict], dry_run: bool) -> None:
    if not records:
        return
    title = "Would tag" if dry_run else "Tagged successfully"
    print_rule(term, f"{title} ({len(records)})")
    by_key: dict[tuple[str, str], list[dict]] = {}
    for rec in records:
        key = (rec.get("region", "?"), rec.get("resource_type", "?"))
        by_key.setdefault(key, []).append(rec)

    for (region, rtype) in sorted(by_key.keys()):
        group = by_key[(region, rtype)]
        print(f"\n  {term.cyan(region)} · {term.bold(rtype)} ({len(group)})")
        for rec in sorted(group, key=lambda r: r.get("applied_name_tag", ""))[:25]:
            print(f"    {term.green('Name')}: {rec.get('applied_name_tag', '')}")
            print(f"    {term.dim(short_arn(rec.get('arn', '')))}")
        if len(group) > 25:
            print(term.dim(f"    … +{len(group) - 25} more in applied.jsonl"))


def print_failed_report(term: Term, records: list[dict], failed_path: str) -> None:
    if not records:
        return
    by_type: dict[str, int] = {}
    for rec in records:
        rtype = rec.get("resource_type", "unknown")
        by_type[rtype] = by_type.get(rtype, 0) + 1

    print_rule(term, f"Failed ({len(records)})")
    print(term.dim(f"  {failed_path}"))
    for rtype, count in sorted(by_type.items(), key=lambda x: (-x[1], x[0])):
        print(f"    {term.red(f'{count:>4}')}  {rtype}")


def print_ecs_report(term: Term, regions: list[str]) -> None:
    print_rule(term, "ECS in-use task defs (optional)")
    for region in regions:
        total, missing = audit_in_use_ecs_task_definitions(region)
        if total == 0:
            continue
        if not missing:
            print(f"  {region}: {term.green('OK')} — {total} task defs all have Name")
        else:
            print(f"  {region}: {term.red(str(len(missing)))} missing / {total} in use")


def confirm_apply(term: Term, count: int) -> bool:
    print()
    print(term.yellow(f"  Write Name on {count} resources?"))
    print(term.dim("  Backups go to backup.jsonl in the run folder."))
    answer = input(f"  Type {term.bold('APPLY')} to continue: ").strip()
    return answer.upper() == "APPLY"


def main() -> int:
    args = parse_args()
    enable_windows_ansi()
    term = Term(use_color=not args.no_color)
    config = resolve_config(args, term)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = os.path.join(os.path.abspath(config.output_dir), f"run-{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    backup_jsonl = os.path.join(run_dir, "backup.jsonl")
    failed_jsonl = os.path.join(run_dir, "failed.jsonl")
    applied_jsonl = os.path.join(run_dir, "applied.jsonl")
    summary_path = os.path.join(run_dir, "summary.json")
    scan_jsonl = os.path.join(run_dir, "scan-missing.jsonl")

    clear_screen(args.no_clear)
    print_banner(term)
    print_config_panel(term, config, run_dir)

    print_rule(term, "Scan")
    t0 = time.time()
    with LiveStatus(term) as live:
        live.set("Scanning", config.regions[0] if len(config.regions) == 1 else f"{len(config.regions)} regions")
        scan_stats, candidates = scan_all_regions(config.regions, config.skip_mq, live)
    elapsed = time.time() - t0

    write_jsonl_bulk(
        scan_jsonl,
        [
            {
                "region": c.region,
                "resource_type": c.resource_type,
                "arn": c.arn,
                "applied_name_tag": c.applied_name_tag,
            }
            for c in candidates
        ],
    )

    clear_screen(args.no_clear)
    print_banner(term)
    print_config_panel(term, config, run_dir)
    print_scan_report(term, config.regions, scan_stats, elapsed)

    applied_records: list[dict] = []
    failed_records: list[dict] = []
    applied_n = failed_n = 0

    if candidates:
        if not config.dry_run and not config.non_interactive:
            if not confirm_apply(term, len(candidates)):
                print(term.yellow("\n  Cancelled — no changes made."))
                return 0

        applied_records, failed_records, applied_n, failed_n = apply_candidates(
            candidates,
            config.dry_run,
            config.workers,
            backup_jsonl,
            applied_jsonl,
            failed_jsonl,
            term,
        )
    else:
        print()
        print(term.green("  Nothing missing — you're fully tagged for this scope."))

    print_applied_report(term, applied_records, config.dry_run)
    print_failed_report(term, failed_records, failed_jsonl)

    if config.ecs_check:
        with LiveStatus(term) as live:
            live.set("ECS check")
            print_ecs_report(term, config.regions)
    else:
        print()
        print(term.dim("  Tip: pass --ecs-check for in-use ECS task definition audit (slower)."))

    summary = {
        "generated_at": timestamp,
        "dry_run": config.dry_run,
        "regions": config.regions,
        "workers": config.workers,
        "scan_seconds": round(elapsed, 2),
        "scan": {
            "total": scan_stats.total,
            "already_had_Name": scan_stats.already_named,
            "missing_Name": scan_stats.missing_name,
            "by_type_missing": scan_stats.by_type_missing,
        },
        "apply": {
            "applied": applied_n if not config.dry_run else 0,
            "would_apply": applied_n if config.dry_run else 0,
            "failed": failed_n,
        },
        "run_dir": run_dir,
    }
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print()
    print(term.cyan("─" * 52))
    if config.dry_run:
        print(f"  {term.bold('Done')} — dry run, {term.cyan(str(applied_n))} would be tagged")
    else:
        print(f"  {term.bold('Done')} — {term.green(str(applied_n))} tagged, {term.red(str(failed_n))} failed")
    print(f"  {term.dim(run_dir)}")
    print(term.cyan("─" * 52))

    return 0 if failed_n == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
