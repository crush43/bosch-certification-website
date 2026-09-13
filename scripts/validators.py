"""Validation and issue reporting for Excel synchronization."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image


@dataclass
class Issue:
    level: str
    file: str
    sheet: str
    row: int | None
    field: str
    reason: str


class Issues:
    def __init__(self) -> None:
        self.warnings: list[Issue] = []
        self.errors: list[Issue] = []

    def warning(self, file: str, sheet: str, row: int | None, field: str, reason: str) -> None:
        self.warnings.append(Issue("warning", file, sheet, row, field, reason))

    def error(self, file: str, sheet: str, row: int | None, field: str, reason: str) -> None:
        self.errors.append(Issue("error", file, sheet, row, field, reason))

    def as_dict(self) -> dict[str, list[dict]]:
        return {
            "warnings": [asdict(issue) for issue in self.warnings],
            "errors": [asdict(issue) for issue in self.errors],
        }


def validate_headers(
    actual: dict[str, int], required: list[str], issues: Issues, file: str, sheet: str
) -> None:
    for header in required:
        if header not in actual:
            issues.error(file, sheet, None, header, "Required header not found")


def validate_enter1(records: list[dict], source_rows: dict[str, int], issues: Issues, file: str) -> None:
    seen: set[str] = set()
    for record in records:
        row = source_rows[record["id"]]
        for json_field, excel_field in (
            ("country", "国家"),
            ("category", "产品类别"),
            ("product", "产品名称"),
        ):
            if not record[json_field]["zh"]:
                issues.error(file, "铭牌信息", row, excel_field, "Required value is empty")
        if record["powerType"] not in ("", "Corded", "Cordless"):
            issues.error(
                file,
                "铭牌信息",
                row,
                "Corded/Cordless",
                f"Invalid value: {record['powerType']}",
            )
        if record["id"] in seen:
            issues.error(file, "铭牌信息", row, "id", f"Duplicate stable ID: {record['id']}")
        seen.add(record["id"])


def validate_enter2(records: list[dict], source_rows: dict[str, int], issues: Issues, file: str) -> None:
    seen: set[str] = set()
    for record in records:
        row = source_rows[record["id"]]
        if not record["country"]["zh"]:
            issues.error(file, "Certification Mark", row, "国家", "Required value is empty")
        if not record["name"]:
            issues.error(file, "Certification Mark", row, "标志", "Required value is empty")
        if not record["drawing"]:
            issues.warning(file, "Certification Mark", row, "图纸编号", "Recommended value is empty")
        if not record["image"]:
            issues.warning(file, "Certification Mark", row, "标志示意图", "No image is anchored to this row")
        if record["id"] in seen:
            issues.error(file, "Certification Mark", row, "id", f"Duplicate stable ID: {record['id']}")
        seen.add(record["id"])


def valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def validate_enter3(records: list[dict], source_rows: dict[str, int], issues: Issues, file: str) -> None:
    seen: set[str] = set()
    for record in records:
        row = source_rows[record["id"]]
        if not record["title"]:
            issues.error(file, "Reference Link", row, "名称", "Required value is empty")
        if not record["url"]:
            issues.error(file, "Reference Link", row, "URL", "Required value is empty")
        elif not valid_http_url(record["url"]):
            issues.error(file, "Reference Link", row, "URL", "URL must start with http:// or https://")
        if record["id"] in seen:
            issues.error(file, "Reference Link", row, "id", f"Duplicate stable ID: {record['id']}")
        seen.add(record["id"])


def validate_generated_files(build_root: Path, json_paths: list[Path], image_paths: list[Path]) -> None:
    for json_path in json_paths:
        with json_path.open("r", encoding="utf-8") as handle:
            json.load(handle)
    for relative_path in image_paths:
        absolute_path = build_root / relative_path
        if not absolute_path.is_file():
            raise RuntimeError(f"Generated image is missing: {relative_path.as_posix()}")
        with Image.open(absolute_path) as image:
            image.verify()
