"""Append a local audit record only after a successful production Git push."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def git_value(project_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def safe_source_files(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    allowed = ("file", "size", "modifiedAt", "snapshotAt", "sha256")
    return {
        key: {field: item[field] for field in allowed if field in item}
        for key, item in value.items()
        if isinstance(item, dict)
    }


def append_history(project_root: Path, sync_report: Path, history_path: Path) -> dict[str, Any]:
    report = json.loads(sync_report.read_text(encoding="utf-8-sig"))
    if report.get("status") != "success":
        raise RuntimeError("Latest local synchronization was not successful")
    if report.get("mode") != "production":
        raise RuntimeError("Latest synchronization was not a production-mode run")

    commit = git_value(project_root, "rev-parse", "HEAD")
    remote_commit = git_value(project_root, "rev-parse", "origin/main")
    if commit != remote_commit:
        raise RuntimeError("Local HEAD does not match origin/main; publish history was not written")

    archive = report.get("archive") if isinstance(report.get("archive"), dict) else {}
    entry = {
        "publishedAt": now_iso(),
        "publishedBy": "manual",
        "sourceConfig": report.get("sourceConfig"),
        "sourceFiles": safe_source_files(report.get("sourceFiles")),
        "sourceSnapshot": archive.get("snapshotId"),
        "records": report.get("records", {}),
        "images": report.get("images", {}),
        "gitCommit": commit,
        "result": "success",
    }
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return entry


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Record one completed production publication")
    parser.add_argument("--sync-report", type=Path, default=root / "logs" / "sync-report.json")
    parser.add_argument("--history", type=Path, default=root / "logs" / "publish-history.jsonl")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    try:
        entry = append_history(project_root, args.sync_report, args.history)
    except Exception as exc:
        print(f"Publish history error: {exc}")
        raise SystemExit(1)
    print(f"Publish history recorded for commit {entry['gitCommit']}")
