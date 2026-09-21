"""Compare AWS SSM parameters between V1 and V2 architecture paths."""
import json
from pathlib import Path

import pandas as pd

V1_PREFIX = "/oms/pod/qa/"
V2_PREFIX = "/oms/pod2/dev/"

V1_JSON = Path(r"C:\Users\akashyap\.cursor\projects\c-PROD-ConnectorSuite\agent-tools\b2184a3c-02c0-49be-a044-dafdd27649bb.txt")
V2_JSON = Path(r"C:\Users\akashyap\.cursor\projects\c-PROD-ConnectorSuite\agent-tools\0def1f6a-8e66-4c56-88c1-c0b538174df1.txt")
OUTPUT = Path(r"c:\PROD\ConnectorSuite\ssm_params_v1_vs_v2_comparison.xlsx")


def load_params(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        {"full_key": row[0], "value": row[1], "type": row[2]}
        for row in raw
    ]


def relative_key(full_key: str, prefix: str) -> str:
    return full_key[len(prefix) :] if full_key.startswith(prefix) else full_key


def build_comparison(v1: list[dict], v2: list[dict]) -> list[dict]:
    v1_map = {relative_key(p["full_key"], V1_PREFIX): p for p in v1}
    v2_map = {relative_key(p["full_key"], V2_PREFIX): p for p in v2}
    all_keys = sorted(set(v1_map) | set(v2_map))

    rows = []
    for key in all_keys:
        p1 = v1_map.get(key)
        p2 = v2_map.get(key)

        if p1 and p2:
            if p1["value"] == p2["value"]:
                status = "Same value"
            else:
                status = "Different value"
        elif p1:
            status = "Only in V1"
        else:
            status = "Only in V2"

        rows.append(
            {
                "relative_key": key,
                "v1_full_key": p1["full_key"] if p1 else "",
                "v1_value": p1["value"] if p1 else "",
                "v1_type": p1["type"] if p1 else "",
                "v2_full_key": p2["full_key"] if p2 else "",
                "v2_value": p2["value"] if p2 else "",
                "v2_type": p2["type"] if p2 else "",
                "status": status,
            }
        )
    return rows


def main() -> None:
    v1 = load_params(V1_JSON)
    v2 = load_params(V2_JSON)

    v1_df = pd.DataFrame(
        [
            {
                "parameter_key": p["full_key"],
                "relative_key": relative_key(p["full_key"], V1_PREFIX),
                "value": p["value"],
                "type": p["type"],
            }
            for p in sorted(v1, key=lambda x: x["full_key"])
        ]
    )

    v2_df = pd.DataFrame(
        [
            {
                "parameter_key": p["full_key"],
                "relative_key": relative_key(p["full_key"], V2_PREFIX),
                "value": p["value"],
                "type": p["type"],
            }
            for p in sorted(v2, key=lambda x: x["full_key"])
        ]
    )

    compare_df = pd.DataFrame(build_comparison(v1, v2))

    summary = pd.DataFrame(
        [
            {"metric": "V1 parameter count", "count": len(v1)},
            {"metric": "V2 parameter count", "count": len(v2)},
            {"metric": "Keys in both", "count": len(set(v1_df["relative_key"]) & set(v2_df["relative_key"]))},
            {"metric": "Only in V1", "count": len(set(v1_df["relative_key"]) - set(v2_df["relative_key"]))},
            {"metric": "Only in V2", "count": len(set(v2_df["relative_key"]) - set(v1_df["relative_key"]))},
            {
                "metric": "Same value (both present)",
                "count": len(compare_df[compare_df["status"] == "Same value"]),
            },
            {
                "metric": "Different value (both present)",
                "count": len(compare_df[compare_df["status"] == "Different value"]),
            },
        ]
    )

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        v1_df.to_excel(writer, sheet_name="V1 Architecture (pod-qa)", index=False)
        v2_df.to_excel(writer, sheet_name="V2 Architecture (pod2-dev)", index=False)
        compare_df.to_excel(writer, sheet_name="Comparison", index=False)
        summary.to_excel(writer, sheet_name="Summary", index=False)

        for sheet in writer.sheets.values():
            for col in sheet.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value is not None:
                        max_len = max(max_len, len(str(cell.value)))
                sheet.column_dimensions[col_letter].width = min(max_len + 2, 80)

    print(f"Written: {OUTPUT}")
    print(f"V1: {len(v1)} params | V2: {len(v2)} params")
    print(f"Only V1: {len(set(v1_df['relative_key']) - set(v2_df['relative_key']))}")
    print(f"Only V2: {len(set(v2_df['relative_key']) - set(v1_df['relative_key']))}")


if __name__ == "__main__":
    main()
