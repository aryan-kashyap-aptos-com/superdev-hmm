"""AWS Systems Manager Parameter Store helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aws_env import aws_region, aws_session


@dataclass(frozen=True)
class ParameterRow:
    name: str
    value: str
    type: str
    version: int
    last_modified: str
    description: str


def list_parameters_under_path(path: str, recursive: bool = True, max_results: int = 500) -> list[ParameterRow]:
    """List parameters under a path (path must start with /)."""
    prefix = path if path.startswith("/") else f"/{path}"
    if not prefix.endswith("/") and prefix != "/":
        prefix = f"{prefix}/"

    client = aws_session().client("ssm", region_name=aws_region())
    rows: list[ParameterRow] = []
    token: str | None = None
    while len(rows) < max_results:
        kwargs: dict[str, Any] = {
            "Path": prefix,
            "Recursive": recursive,
            "WithDecryption": True,
            "MaxResults": min(50, max_results - len(rows)),
        }
        if token:
            kwargs["NextToken"] = token
        response = client.get_parameters_by_path(**kwargs)
        names = [p["Name"] for p in response.get("Parameters", [])]
        if names:
            detail = client.get_parameters(Names=names, WithDecryption=True)
            for p in detail.get("Parameters", []):
                rows.append(
                    ParameterRow(
                        name=p.get("Name", ""),
                        value=p.get("Value", ""),
                        type=p.get("Type", "String"),
                        version=int(p.get("Version", 0)),
                        last_modified=str(p.get("LastModifiedDate", "")),
                        description=str(p.get("Description") or ""),
                    )
                )
        token = response.get("NextToken")
        if not token:
            break
    return sorted(rows, key=lambda r: r.name.lower())


def put_parameter(
    name: str,
    value: str,
    parameter_type: str = "String",
    description: str | None = None,
    overwrite: bool = True,
) -> None:
    client = aws_session().client("ssm", region_name=aws_region())
    kwargs: dict[str, Any] = {
        "Name": name,
        "Value": value,
        "Type": parameter_type,
        "Overwrite": overwrite,
    }
    if description:
        kwargs["Description"] = description
    client.put_parameter(**kwargs)


def create_parameter(name: str, value: str, parameter_type: str = "String", description: str = "") -> None:
    put_parameter(name, value, parameter_type=parameter_type, description=description or None, overwrite=False)
