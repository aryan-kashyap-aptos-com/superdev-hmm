"""Export Sumo Logic query results to Excel."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from client import ROOT


def default_output_path(name: str | None = None) -> Path:
    exports_dir = ROOT / "exports"
    exports_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = name or f"sumologic_{stamp}.xlsx"
    if not filename.lower().endswith(".xlsx"):
        filename = f"{filename}.xlsx"
    return exports_dir / filename


def rows_to_sheet_values(fields: list[str], rows: list[dict[str, Any]]) -> tuple[list[str], list[list[Any]]]:
    if not fields and rows:
        fields = sorted({key for row in rows for key in row.keys()})
    sheet_rows: list[list[Any]] = []
    for row in rows:
        sheet_rows.append([row.get(field, "") for field in fields])
    return fields, sheet_rows


def write_excel(
    fields: list[str],
    rows: list[dict[str, Any]],
    output_path: Path,
    *,
    query: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers, sheet_rows = rows_to_sheet_values(fields, rows)

    workbook = Workbook()
    data_sheet = workbook.active
    data_sheet.title = "Results"

    data_sheet.append(headers)
    for cell in data_sheet[1]:
        cell.font = Font(bold=True)

    for row in sheet_rows:
        data_sheet.append(row)

    for index, header in enumerate(headers, start=1):
        lengths = [len(str(header))]
        for row in sheet_rows:
            value = row[index - 1]
            lengths.append(len(str(value)) if value is not None else 0)
        data_sheet.column_dimensions[get_column_letter(index)].width = min(max(lengths) + 2, 60)

    if query or metadata:
        meta_sheet = workbook.create_sheet("Query")
        if query:
            meta_sheet["A1"] = "Query"
            meta_sheet["A1"].font = Font(bold=True)
            meta_sheet["B1"] = query
        if metadata:
            row_index = 3
            for key, value in metadata.items():
                meta_sheet[f"A{row_index}"] = str(key)
                meta_sheet[f"A{row_index}"].font = Font(bold=True)
                meta_sheet[f"B{row_index}"] = str(value)
                row_index += 1

    workbook.save(output_path)
    return output_path
