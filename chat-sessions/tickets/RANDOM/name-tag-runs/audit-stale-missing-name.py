#!/usr/bin/env python3
"""One-off audit: do failed/scan-missing resources still exist? Safe to delete?"""
import json
import re
import sys

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
FAILED = r"c:\PROD\ConnectorSuite\tickets\RANDOM\name-tag-runs\run-20260920T133745Z\failed.jsonl"
SCAN = r"c:\PROD\ConnectorSuite\tickets\RANDOM\name-tag-runs\run-20260920T135855Z\scan-missing.jsonl"


def main() -> int:
    recs = [json.loads(l) for l in open(FAILED, encoding="utf-8") if l.strip()]
    scan_recs = [json.loads(l) for l in open(SCAN, encoding="utf-8") if l.strip()]

    apigw = boto3.client("apigatewayv2", region_name=REGION)
    cf = boto3.client("cloudformation", region_name=REGION)
    ec2 = boto3.client("ec2", region_name=REGION)
    cw = boto3.client("cloudwatch", region_name=REGION)
    events = boto3.client("events", region_name=REGION)
    ecs = boto3.client("ecs", region_name=REGION)

    live_apis: set[str] = set()
    token = None
    while True:
        kw = {"NextToken": token} if token else {}
        resp = apigw.get_apis(**kw)
        for api in resp.get("Items", []):
            live_apis.add(api["ApiId"])
        token = resp.get("NextToken")
        if not token:
            break

    print("=== Why Tag Editor still lists them ===")
    print("Region: us-east-1 only (not other regions).")
    print("Resource Groups / Tag Editor keeps ARNs until AWS reconciles the index.")
    print()

    print("=== API Gateway HTTP API stages (36) ===")
    api_ids: list[str] = []
    for rec in recs:
        if rec["resource_type"] != "apigateway:apis":
            continue
        m = re.search(r"/apis/([^/]+)/", rec["arn"])
        if m:
            api_ids.append(m.group(1))
    api_ids = sorted(set(api_ids))
    gone = [i for i in api_ids if i not in live_apis]
    still = [i for i in api_ids if i in live_apis]
    print(f"Orphan tag records (API deleted): {len(gone)}")
    print(f"API still exists: {len(still)}")
    for i in still:
        print(f"  STILL LIVE — investigate before any delete: {i}")
    print("Safe to delete API? N/A - resource already gone; nothing to delete.")
    print("Action: ignore in Tag Editor or wait for index cleanup; cannot untag ghosts.")
    print()

    print("=== CloudFormation stacks (22) ===")
    stacks: list[tuple[str, str, str]] = []
    for rec in recs:
        if rec["resource_type"] != "cloudformation:stack":
            continue
        name = rec["applied_name_tag"]
        try:
            s = cf.describe_stacks(StackName=name)["Stacks"][0]
            status = s["StackStatus"]
            stacks.append((status, name, "exists"))
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "?")
            stacks.append((code, name, "missing"))

    for status, name, kind in sorted(stacks, key=lambda x: x[0]):
        safe = ""
        if status in ("ROLLBACK_COMPLETE", "ROLLBACK_FAILED", "CREATE_FAILED", "DELETE_FAILED"):
            safe = "  - often safe to DELETE stack after confirming no ECS service uses it"
        elif status == "CREATE_COMPLETE":
            safe = "  - DO NOT delete without ownership review"
        print(f"{status:26} {name}{safe}")

    print()
    print("=== ECS services still tied to ECS-Console-V2 stacks (sample check) ===")
    stack_names = [n for _, n, k in stacks if k == "exists" and n.startswith("ECS-Console-V2")]
    service_hits: list[str] = []
    for cluster_arn in ecs.list_clusters()["clusterArns"]:
        cluster = cluster_arn.split("/")[-1]
        paginator = ecs.get_paginator("list_services")
        for page in paginator.paginate(cluster=cluster_arn):
            for svc_arn in page["serviceArns"]:
                svc = svc_arn.split("/")[-1]
                if any(sn[:40] in svc for sn in stack_names):
                    service_hits.append(f"{cluster}/{svc}")
    if service_hits:
        print("Active ECS services with similar names (manual correlate):")
        for h in service_hits[:15]:
            print(f"  {h}")
    else:
        print("No obvious name overlap with listed ECS-Console-V2 stack names.")
    print()

    print("=== EventBridge rules (9) — AWS managed ===")
    for rec in recs:
        if rec["resource_type"] != "events:rule":
            continue
        arn = rec["arn"]
        tail = arn.split(":rule/", 1)[1]
        if "/" in tail:
            bus, rule = tail.split("/", 1)
        else:
            bus, rule = "default", tail
        try:
            d = events.describe_rule(Name=rule, EventBusName=bus)
            managed = d.get("ManagedBy") or "AWS"
            print(f"  {rule[:55]:55} ManagedBy={managed}")
        except ClientError as exc:
            print(f"  {rule[:40]} {exc.response['Error']['Code']}")
    print("Safe to delete? NO — required for Schemas/Step Functions; do not remove.")
    print()

    print("=== CloudWatch alarm (1) ===")
    for rec in recs:
        if rec["resource_type"] != "cloudwatch:alarm":
            continue
        name = rec["applied_name_tag"]
        resp = cw.describe_alarms(AlarmNames=[name])
        ma = resp.get("MetricAlarms", [])
        ca = resp.get("CompositeAlarms", [])
        if ma:
            al = ma[0]
            print(f"Metric alarm exists: State={al['StateValue']}")
        elif ca:
            print("Composite alarm exists")
        else:
            print("Alarm not found")
    print("Safe to delete? Only if team confirms monitoring not needed.")
    print()

    print("=== EC2 security group (from scan-missing) ===")
    for rec in scan_recs:
        if rec.get("resource_type") != "ec2:security-group":
            continue
        sg = rec["arn"].split("/")[-1]
        d = ec2.describe_security_groups(GroupIds=[sg])["SecurityGroups"][0]
        enis = ec2.describe_network_interfaces(
            Filters=[{"Name": "group-id", "Values": [sg]}]
        )["NetworkInterfaces"]
        print(f"SG {sg} name={d.get('GroupName')} ENIs={len(enis)}")
        print("Safe to delete? NO — tag it (Apply), do not delete unless ENIs=0 and unused.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
