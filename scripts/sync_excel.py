"""Single safe entry point for Excel → JSON + generated image synchronization."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import traceback
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from excel_reader import (
    clean_text,
    header_map,
    localized_zh,
    normalize_id_part,
    open_excel,
    row_is_blank,
    snapshot_excel,
    stable_hash,
)
from image_extractor import ImageAnchor, deduplicate_anchors, extract_image_anchors, save_as_png
from validators import (
    Issues,
    validate_enter1,
    validate_enter2,
    validate_enter3,
    validate_generated_files,
    validate_headers,
)


E1_FILE = "ENTER 1-Basic Information.xlsx"
E2_FILE = "ENTER 20-Certification Mark.xlsx"
E3_FILE = "ENTER 3-Reference Link.xlsx"
E1_SHEET = "铭牌信息"
E2_SHEET = "Certification Mark"
E3_SHEET = "Reference Link"

E1_HEADERS = [
    "国家", "产品类别", "产品名称", "Corded/Cordless", "示例", "型号", "裸机号", "参数",
    "生产年月", "认证标志", "环保标志", "原产地信息", "Class II 标志", "制造商/生产者信息",
    "WEEE标志", "阅读说明书", "IP等级", "防护标志", "其他特殊标签",
]
E1_IMAGE_HEADERS = {
    "示例": "example",
    "认证标志": "cert",
    "环保标志": "eco",
    "原产地信息": "origin",
    "Class II 标志": "class2",
    "制造商/生产者信息": "manufacturer",
    "WEEE标志": "weee",
    "阅读说明书": "manual",
    "防护标志": "protect",
    "其他特殊标签": "other",
}
E2_HEADERS = ["国家", "标志", "图纸编号", "标志示意图", "关键备注", "适用产品"]
E2_IMAGE_HEADERS = {"标志示意图": "image"}


def resolve_excel_dir(project_root: Path, cli_excel_dir: Path | None) -> tuple[Path, str]:
    """Resolve the one Excel source directory from CLI or project configuration."""
    if cli_excel_dir is not None:
        return cli_excel_dir.expanduser().resolve(), "--excel-dir"

    local_config = project_root / "config.local.json"
    legacy_config = project_root / "config.json"
    if local_config.is_file():
        config_path = local_config
    elif legacy_config.is_file():
        config_path = legacy_config
    else:
        return (project_root / "excel").resolve(), "default ./excel"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read Excel source configuration {config_path.name}: {exc}") from exc
    value = config.get("excelSource") if isinstance(config, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f'{config_path.name} must contain a non-empty string field "excelSource"')
    configured = Path(value.strip()).expanduser()
    if not configured.is_absolute():
        configured = project_root / configured
    return configured.resolve(), config_path.name


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def get_sheet(workbook, name: str, file_name: str, issues: Issues):
    if name not in workbook.sheetnames:
        issues.error(file_name, name, None, "Sheet", "Required sheet not found")
        return None
    return workbook[name]


def build_enter1(path: Path, output_root: Path, issues: Issues) -> tuple[list[dict], dict, list[Path]]:
    workbook = open_excel(path)
    worksheet = get_sheet(workbook, E1_SHEET, E1_FILE, issues)
    if worksheet is None:
        return [], {"objects": 0, "logical": 0, "duplicates": 0}, []
    headers = header_map(worksheet, 2)
    validate_headers(headers, E1_HEADERS, issues, E1_FILE, E1_SHEET)
    if any(header not in headers for header in E1_HEADERS):
        return [], {"objects": 0, "logical": 0, "duplicates": 0}, []

    records: list[dict] = []
    by_row: dict[int, dict] = {}
    source_rows: dict[str, int] = {}
    for row in range(3, worksheet.max_row + 1):
        if row_is_blank(worksheet, row, headers.values()):
            continue
        value = lambda header: clean_text(worksheet.cell(row, headers[header]).value)
        record_id = "e1_" + stable_hash(
            [value("国家"), value("产品类别"), value("产品名称"), value("Corded/Cordless"), value("型号")]
        )
        record = {
            "id": record_id,
            "country": localized_zh(value("国家")),
            "category": localized_zh(value("产品类别")),
            "product": localized_zh(value("产品名称")),
            "powerType": value("Corded/Cordless"),
            "example": [],
            "model": value("型号"),
            "bareModel": value("裸机号"),
            "specs": value("参数"),
            "dateCode": value("生产年月"),
            "cert": [],
            "eco": [],
            "origin": [],
            "class2": [],
            "manufacturer": [],
            "weee": [],
            "manual": [],
            "ip": value("IP等级"),
            "protect": [],
            "other": [],
        }
        records.append(record)
        by_row[row] = record
        source_rows[record_id] = row

    validate_enter1(records, source_rows, issues, E1_FILE)
    try:
        anchors = [anchor for anchor in extract_image_anchors(path) if anchor.sheet == E1_SHEET]
    except Exception as exc:
        issues.error(E1_FILE, E1_SHEET, None, "图片", str(exc))
        anchors = []

    def duplicate_warning(anchor: ImageAnchor) -> None:
        issues.warning(
            E1_FILE,
            anchor.sheet,
            anchor.row,
            anchor.cell,
            "Duplicate image object at the same anchor with identical content; kept once",
        )

    logical, duplicate_count = deduplicate_anchors(anchors, duplicate_warning)
    column_to_header = {column: header for header, column in headers.items()}
    grouped: dict[tuple[int, str], list[ImageAnchor]] = defaultdict(list)
    for anchor in logical:
        header = column_to_header.get(anchor.column)
        field = E1_IMAGE_HEADERS.get(header or "")
        if anchor.row not in by_row:
            issues.error(E1_FILE, anchor.sheet, anchor.row, anchor.cell, "Image points to no data record")
        elif not field:
            issues.error(E1_FILE, anchor.sheet, anchor.row, header or anchor.cell, "Image is anchored to an unsupported field")
        else:
            grouped[(anchor.row, field)].append(anchor)

    generated: list[Path] = []
    for (row, field), field_anchors in sorted(grouped.items()):
        record = by_row[row]
        for index, anchor in enumerate(field_anchors, start=1):
            relative = Path("assets") / "generated" / "enter1" / f"{record['id']}_{field}_{index:02}.png"
            save_as_png(anchor.content, output_root / relative)
            record[field].append(relative.as_posix())
            generated.append(relative)

    return records, {
        "objects": len(anchors),
        "logical": len(logical),
        "duplicates": duplicate_count,
        "uniqueMedia": len({anchor.content_hash for anchor in anchors}),
    }, generated


def e2_id(country: str, name: str, drawing: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "", normalize_id_part(drawing))
    return "e2_" + (slug or stable_hash([country, name], 12))


def build_enter2(path: Path, output_root: Path, issues: Issues) -> tuple[list[dict], dict, list[Path]]:
    workbook = open_excel(path)
    worksheet = get_sheet(workbook, E2_SHEET, E2_FILE, issues)
    if worksheet is None:
        return [], {"objects": 0, "logical": 0, "duplicates": 0}, []
    headers = header_map(worksheet, 1)
    validate_headers(headers, E2_HEADERS, issues, E2_FILE, E2_SHEET)
    if any(header not in headers for header in E2_HEADERS):
        return [], {"objects": 0, "logical": 0, "duplicates": 0}, []

    records: list[dict] = []
    by_row: dict[int, dict] = {}
    source_rows: dict[str, int] = {}
    for row in range(2, worksheet.max_row + 1):
        if row_is_blank(worksheet, row, headers.values()):
            continue
        value = lambda header: clean_text(worksheet.cell(row, headers[header]).value)
        record_id = e2_id(value("国家"), value("标志"), value("图纸编号"))
        record = {
            "id": record_id,
            "country": localized_zh(value("国家")),
            "name": value("标志"),
            "drawing": value("图纸编号"),
            "image": [],
            "notes": localized_zh(value("关键备注")),
            "products": localized_zh(value("适用产品")),
        }
        records.append(record)
        by_row[row] = record
        source_rows[record_id] = row

    try:
        anchors = [anchor for anchor in extract_image_anchors(path) if anchor.sheet == E2_SHEET]
    except Exception as exc:
        issues.error(E2_FILE, E2_SHEET, None, "标志示意图", str(exc))
        anchors = []

    def duplicate_warning(anchor: ImageAnchor) -> None:
        issues.warning(
            E2_FILE,
            anchor.sheet,
            anchor.row,
            anchor.cell,
            "Duplicate image object at the same anchor with identical content; kept once",
        )

    logical, duplicate_count = deduplicate_anchors(anchors, duplicate_warning)
    column_to_header = {column: header for header, column in headers.items()}
    grouped: dict[int, list[ImageAnchor]] = defaultdict(list)
    for anchor in logical:
        header = column_to_header.get(anchor.column)
        field = E2_IMAGE_HEADERS.get(header or "")
        if anchor.row not in by_row:
            issues.error(E2_FILE, anchor.sheet, anchor.row, anchor.cell, "Image points to no data record")
        elif field != "image":
            issues.error(E2_FILE, anchor.sheet, anchor.row, header or anchor.cell, "Image is anchored to an unsupported field")
        else:
            grouped[anchor.row].append(anchor)

    generated: list[Path] = []
    for row, row_anchors in sorted(grouped.items()):
        record = by_row[row]
        for index, anchor in enumerate(row_anchors, start=1):
            relative = Path("assets") / "generated" / "enter2" / f"{record['id']}_{index:02}.png"
            save_as_png(anchor.content, output_root / relative)
            record["image"].append(relative.as_posix())
            generated.append(relative)

    validate_enter2(records, source_rows, issues, E2_FILE)
    return records, {
        "objects": len(anchors),
        "logical": len(logical),
        "duplicates": duplicate_count,
        "uniqueMedia": len({anchor.content_hash for anchor in anchors}),
    }, generated


def link_key(title: str, record_id: str) -> str:
    known = {"pt/ecs": "PT", "news": "News", "eudoc": "EUDoC"}
    normalized = normalize_id_part(title)
    if normalized in known:
        return known[normalized]
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
    return slug[:40] or "link_" + record_id.removeprefix("e3_")[:8]


def build_enter3(path: Path, issues: Issues) -> list[dict]:
    workbook = open_excel(path)
    worksheet = get_sheet(workbook, E3_SHEET, E3_FILE, issues)
    if worksheet is None:
        return []
    records: list[dict] = []
    source_rows: dict[str, int] = {}
    first_nonblank_seen = False
    for row in range(1, worksheet.max_row + 1):
        title = clean_text(worksheet.cell(row, 1).value)
        url = clean_text(worksheet.cell(row, 2).value)
        if not title and not url:
            continue
        if not first_nonblank_seen:
            first_nonblank_seen = True
            if normalize_id_part(title) in ("名称", "name", "title") and normalize_id_part(url) == "url":
                continue
        record_id = "e3_" + stable_hash([title, url])
        record = {"id": record_id, "key": link_key(title, record_id), "title": title, "url": url}
        records.append(record)
        source_rows[record_id] = row
    validate_enter3(records, source_rows, issues, E3_FILE)
    return records


def check_lock_files(excel_dir: Path) -> None:
    locks = [excel_dir / ("~$" + name) for name in (E1_FILE, E2_FILE, E3_FILE)]
    existing = [path.name for path in locks if path.exists()]
    if existing:
        raise RuntimeError("Excel lock file detected; close and save the workbook before syncing: " + ", ".join(existing))


def assert_publish_targets(project_root: Path) -> None:
    expected_data = (project_root / "data").resolve()
    expected_generated = (project_root / "assets" / "generated").resolve()
    if expected_data.parent != project_root.resolve():
        raise RuntimeError("Unsafe data publish target")
    if expected_generated.parent.parent != project_root.resolve():
        raise RuntimeError("Unsafe generated image publish target")


def publish(build_root: Path, project_root: Path) -> None:
    """Replace generated outputs with rollback if either directory move fails."""
    assert_publish_targets(project_root)
    new_data = build_root / "data"
    new_generated = build_root / "assets" / "generated"
    target_data = project_root / "data"
    target_generated = project_root / "assets" / "generated"
    backup_root = build_root / "rollback"
    backup_data = backup_root / "data"
    backup_generated = backup_root / "generated"
    backup_root.mkdir(parents=True, exist_ok=True)
    (project_root / "assets").mkdir(parents=True, exist_ok=True)

    moved_old_data = False
    moved_old_generated = False
    moved_new_data = False
    moved_new_generated = False
    try:
        if target_data.exists():
            os.replace(target_data, backup_data)
            moved_old_data = True
        if target_generated.exists():
            os.replace(target_generated, backup_generated)
            moved_old_generated = True
        os.replace(new_data, target_data)
        moved_new_data = True
        os.replace(new_generated, target_generated)
        moved_new_generated = True
    except Exception:
        if moved_new_generated and target_generated.exists():
            shutil.rmtree(target_generated)
        if moved_new_data and target_data.exists():
            shutil.rmtree(target_data)
        if moved_old_generated and backup_generated.exists():
            os.replace(backup_generated, target_generated)
        if moved_old_data and backup_data.exists():
            os.replace(backup_data, target_data)
        raise


def format_issue(issue) -> str:
    row = f" Row {issue.row}" if issue.row is not None else ""
    return f"[{issue.level.upper()}] {issue.file} | {issue.sheet}{row} | {issue.field} | {issue.reason}"


def write_report(logs_dir: Path, report: dict) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    write_json(logs_dir / f"sync-{stamp}.json", report)
    latest_tmp = logs_dir / ".sync-report.tmp"
    write_json(latest_tmp, report)
    os.replace(latest_tmp, logs_dir / "sync-report.json")


def run_sync(project_root: Path, excel_dir: Path, source_config: str = "--excel-dir") -> int:
    started_at = now_iso()
    issues = Issues()
    run_root = project_root / ".build" / f"sync-{uuid.uuid4().hex}"
    snapshot_dir = run_root / "excel"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "startedAt": started_at,
        "completedAt": None,
        "status": "failed",
        "sourceConfig": source_config,
        "snapshotCreated": False,
        "sourceFiles": {},
        "records": {"enter1": 0, "enter2": 0, "enter3": 0},
        "images": {
            "enter1": {"objects": 0, "logical": 0, "duplicates": 0, "uniqueMedia": 0},
            "enter2": {"objects": 0, "logical": 0, "duplicates": 0, "uniqueMedia": 0},
            "total": 0,
        },
        "warnings": [],
        "errors": [],
        "issueCounts": {"warnings": 0, "errors": 0},
    }
    try:
        check_lock_files(excel_dir)
        snapshots: dict[str, Path] = {}
        source_key = {E1_FILE: "basicInformation", E2_FILE: "certificationMarks", E3_FILE: "referenceLinks"}
        for file_name in (E1_FILE, E2_FILE, E3_FILE):
            source = excel_dir / file_name
            if not source.is_file():
                raise RuntimeError(f"Required Excel file not found: {source}")
            destination = snapshot_dir / file_name
            report["sourceFiles"][source_key[file_name]] = snapshot_excel(source, destination)
            snapshots[file_name] = destination
        report["snapshotCreated"] = True

        basic, e1_images, e1_paths = build_enter1(snapshots[E1_FILE], run_root, issues)
        certs, e2_images, e2_paths = build_enter2(snapshots[E2_FILE], run_root, issues)
        links = build_enter3(snapshots[E3_FILE], issues)
        report["records"] = {"enter1": len(basic), "enter2": len(certs), "enter3": len(links)}
        report["images"] = {
            "enter1": e1_images,
            "enter2": e2_images,
            "total": e1_images["logical"] + e2_images["logical"],
        }
        report.update(issues.as_dict())
        report["issueCounts"] = {
            "warnings": len(issues.warnings),
            "errors": len(issues.errors),
        }
        if issues.errors:
            raise RuntimeError(f"Validation failed with {len(issues.errors)} error(s)")

        data_dir = run_root / "data"
        write_json(data_dir / "basic_information.json", basic)
        write_json(data_dir / "certification_marks.json", certs)
        write_json(data_dir / "reference_links.json", links)
        generated_at = now_iso()
        source_meta = {}
        for key, info in report["sourceFiles"].items():
            source_meta[key] = {**info, "records": report["records"][{
                "basicInformation": "enter1",
                "certificationMarks": "enter2",
                "referenceLinks": "enter3",
            }[key]]}
        meta = {
            "generatedAt": generated_at,
            "status": "success",
            "sources": source_meta,
            "images": {
                "enter1Objects": e1_images["objects"],
                "enter1Logical": e1_images["logical"],
                "enter1DuplicatesRemoved": e1_images["duplicates"],
                "enter2Objects": e2_images["objects"],
                "enter2Logical": e2_images["logical"],
                "enter2DuplicatesRemoved": e2_images["duplicates"],
                "totalLogical": e1_images["logical"] + e2_images["logical"],
            },
            "warnings": len(issues.warnings),
        }
        write_json(data_dir / "meta.json", meta)
        validate_generated_files(
            run_root,
            [
                data_dir / "basic_information.json",
                data_dir / "certification_marks.json",
                data_dir / "reference_links.json",
                data_dir / "meta.json",
            ],
            e1_paths + e2_paths,
        )
        publish(run_root, project_root)
        report["status"] = "success"
        report["completedAt"] = now_iso()
        write_report(project_root / "logs", report)

        print("=" * 43)
        print("Bosch Certification Website Sync")
        print("=" * 43)
        print(f"Excel source: {source_config}")
        print("Source snapshot: CREATED AND VERIFIED")
        print("ENTER1")
        print(f"  Records: {len(basic)}")
        print(f"  Image objects: {e1_images['objects']}")
        print(f"  Logical images: {e1_images['logical']}")
        print(f"  Duplicates removed: {e1_images['duplicates']}")
        print(f"  Warnings: {sum(issue.file == E1_FILE for issue in issues.warnings)}  Errors: 0")
        print("ENTER2")
        print(f"  Records: {len(certs)}")
        print(f"  Image objects: {e2_images['objects']}")
        print(f"  Logical images: {e2_images['logical']}")
        print(f"  Duplicates removed: {e2_images['duplicates']}")
        print(f"  Warnings: {sum(issue.file == E2_FILE for issue in issues.warnings)}  Errors: 0")
        print("ENTER3")
        print(f"  Records: {len(links)}")
        print(f"  Warnings: {sum(issue.file == E3_FILE for issue in issues.warnings)}  Errors: 0")
        for issue in issues.warnings:
            print(format_issue(issue))
        print("Validation: PASSED")
        print("JSON generated successfully.")
        print("Formal data replaced successfully.")
        print("=" * 43)
        return 0
    except Exception as exc:
        if not issues.errors:
            issues.error("sync", "", None, "runtime", str(exc))
        report.update(issues.as_dict())
        report["issueCounts"] = {
            "warnings": len(issues.warnings),
            "errors": len(issues.errors),
        }
        report["completedAt"] = now_iso()
        try:
            write_report(project_root / "logs", report)
        except Exception:
            pass
        print("Validation: FAILED", file=sys.stderr)
        print("Formal data NOT changed.", file=sys.stderr)
        for issue in issues.errors:
            print(format_issue(issue), file=sys.stderr)
        if os.environ.get("SYNC_DEBUG") == "1":
            traceback.print_exc()
        return 1
    finally:
        if run_root.exists():
            shutil.rmtree(run_root, ignore_errors=True)
        build_parent = project_root / ".build"
        if build_parent.exists() and not any(build_parent.iterdir()):
            build_parent.rmdir()


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Synchronize Bosch certification Excel data")
    parser.add_argument(
        "--excel-dir",
        type=Path,
        default=None,
        help="Override the configured directory containing the three source workbooks",
    )
    return parser.parse_args()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        excel_source, source_config_name = resolve_excel_dir(root, args.excel_dir)
    except Exception as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run_sync(root, excel_source, source_config_name))
