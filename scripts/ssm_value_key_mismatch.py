"""Find SSM params where values match or are similar but key names differ."""
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

V1_PREFIX = "/oms/pod/qa/"
V2_PREFIX = "/oms/pod2/dev/"
V1_JSON = Path(r"C:\Users\akashyap\.cursor\projects\c-PROD-ConnectorSuite\agent-tools\v1_params.json")
V2_JSON = Path(r"C:\Users\akashyap\.cursor\projects\c-PROD-ConnectorSuite\agent-tools\v2_params.json")
OUTPUT = Path(r"c:\PROD\ConnectorSuite\ssm_similar_value_diff_key.xlsx")


def load_params(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    prefix = V1_PREFIX if "v1" in path.name else V2_PREFIX
    return {
        row[0][len(prefix) :]: {"full_key": row[0], "value": row[1], "type": row[2]}
        for row in raw
        if row[0].startswith(prefix)
    }


def normalize_value(value: str) -> str:
    v = value.strip().lower()
    replacements = [
        (r"oms[_-]?pod[_-]?qa", "ENV"),
        (r"oms[_-]?pod2[_-]?dev", "ENV"),
        (r"pod[_-]?qa", "ENV"),
        (r"pod2[_-]?dev", "ENV"),
        (r"podqa", "ENV"),
        (r"pod2dev", "ENV"),
        (r"oms-shared-dev", "RDS"),
        (r"oms-pod2-dev", "RDS"),
        (r"podqa_postgres", "DBUSER"),
        (r"omsadmin", "DBUSER"),
        (r"payment-cybersource-asf", "ASF"),
        (r"payment-aurus-asf", "ASF"),
        (r"payment-asf-paypal", "ASF"),
        (r"cybersource-payment", "ASF"),
        (r"aurus-payment", "ASF"),
        (r"paypal-payment", "ASF"),
    ]
    for pattern, repl in replacements:
        v = re.sub(pattern, repl, v, flags=re.IGNORECASE)
    return v


def norm_svc(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def key_similarity(k1: str, k2: str) -> float:
    return SequenceMatcher(None, k1.lower(), k2.lower()).ratio()


def service_and_suffix(key: str):
    parts = key.split("/", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (key, "")


def is_meaningful_value(value: str) -> bool:
    v = value.strip().lower()
    if v in {"true", "false", "na", "not-configured", "us-east-1", "5432", "500", "5000", "30", "900", "300", "1000"}:
        return False
    return len(v) >= 8 or "arn:aws:" in v or "http" in v or ".com" in v


def main() -> None:
    v1_map = load_params(V1_JSON)
    v2_map = load_params(V2_JSON)
    common = set(v1_map) & set(v2_map)
    v1_only = {k: v1_map[k] for k in set(v1_map) - common}
    v2_only = {k: v2_map[k] for k in set(v2_map) - common}

    # 1) High-confidence service renames: same suffix, similar service name, similar value
    high_conf = []
    v2_by_suffix = defaultdict(list)
    for k2, p2 in v2_only.items():
        svc2, suffix2 = service_and_suffix(k2)
        v2_by_suffix[suffix2].append((k2, p2, svc2))

    seen = set()
    for k1, p1 in v1_only.items():
        svc1, suffix1 = service_and_suffix(k1)
        for k2, p2, svc2 in v2_by_suffix.get(suffix1, []):
            svc_sim = SequenceMatcher(None, norm_svc(svc1), norm_svc(svc2)).ratio()
            if svc_sim < 0.82:
                continue
            exact = p1["value"] == p2["value"]
            norm = normalize_value(p1["value"]) == normalize_value(p2["value"])
            if not (exact or norm):
                continue
            pair = (k1, k2)
            if pair in seen:
                continue
            seen.add(pair)
            high_conf.append(
                {
                    "v1_relative_key": k1,
                    "v2_relative_key": k2,
                    "v1_service": svc1,
                    "v2_service": svc2,
                    "suffix": suffix1,
                    "service_similarity": round(svc_sim, 3),
                    "value_match": "exact" if exact else "env-normalized",
                    "v1_value": p1["value"],
                    "v2_value": p2["value"],
                }
            )

    # 2) Same normalized value, completely different key path
    value_map = []
    v1_by_norm = defaultdict(list)
    v2_by_norm = defaultdict(list)
    for k, p in v1_only.items():
        if is_meaningful_value(p["value"]):
            v1_by_norm[normalize_value(p["value"])].append((k, p))
    for k, p in v2_only.items():
        if is_meaningful_value(p["value"]):
            v2_by_norm[normalize_value(p["value"])].append((k, p))

    seen_val = set()
    for nv, items1 in v1_by_norm.items():
        if nv not in v2_by_norm:
            continue
        for k1, p1 in items1:
            for k2, p2 in v2_by_norm[nv]:
                if k1 == k2:
                    continue
                pair = (k1, k2)
                if pair in seen_val:
                    continue
                seen_val.add(pair)
                value_map.append(
                    {
                        "v1_relative_key": k1,
                        "v2_relative_key": k2,
                        "key_similarity": round(key_similarity(k1, k2), 3),
                        "value_match": "exact" if p1["value"] == p2["value"] else "env-normalized",
                        "normalized_value": nv,
                        "v1_value": p1["value"],
                        "v2_value": p2["value"],
                    }
                )

    value_map_df = pd.DataFrame(value_map).sort_values(
        ["key_similarity", "v1_relative_key"], ascending=[False, True]
    ) if value_map else pd.DataFrame()

    # 3) Payment / provider specific (user focus area)
    payment_rows = []
    payment_pat = re.compile(r"payment|provider|cyber|paypal|aurus|asf", re.I)
    for k1, p1 in v1_only.items():
        if not payment_pat.search(k1):
            continue
        for k2, p2 in v2_only.items():
            if not payment_pat.search(k2):
                continue
            if p1["value"] == p2["value"] or normalize_value(p1["value"]) == normalize_value(p2["value"]):
                payment_rows.append(
                    {
                        "v1_relative_key": k1,
                        "v2_relative_key": k2,
                        "keys_match": k1 == k2,
                        "value_match": "exact" if p1["value"] == p2["value"] else "env-normalized",
                        "v1_value": p1["value"],
                        "v2_value": p2["value"],
                    }
                )
    payment_df = pd.DataFrame(payment_rows).sort_values(["keys_match", "v1_relative_key"], ascending=[True, True]) if payment_rows else pd.DataFrame()

    high_df = pd.DataFrame(high_conf).sort_values(["service_similarity", "suffix"], ascending=[False, True]) if high_conf else pd.DataFrame()
    summary = pd.DataFrame(
        [
            {"category": "High-confidence renamed keys", "count": len(high_df)},
            {"category": "Similar value, different key (meaningful values)", "count": len(value_map_df)},
            {"category": "Payment-provider related mappings", "count": len(payment_df)},
            {"category": "V1-only keys", "count": len(v1_only)},
            {"category": "V2-only keys", "count": len(v2_only)},
        ]
    )

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        if not high_df.empty:
            high_df.to_excel(writer, sheet_name="High Confidence Renames", index=False)
        if not value_map_df.empty:
            value_map_df.to_excel(writer, sheet_name="Similar Value Diff Key", index=False)
        if not payment_df.empty:
            payment_df.to_excel(writer, sheet_name="Payment Provider Mapping", index=False)
        for sheet in writer.sheets.values():
            for col in sheet.columns:
                max_len = max((len(str(c.value)) for c in col if c.value is not None), default=10)
                sheet.column_dimensions[col[0].column_letter].width = min(max_len + 2, 90)

    print(f"Written: {OUTPUT}")
    print(f"High-confidence renames: {len(high_df)}")
    print(f"Similar value / diff key: {len(value_map_df)}")
    print(f"Payment-provider mappings: {len(payment_df)}")


if __name__ == "__main__":
    main()
