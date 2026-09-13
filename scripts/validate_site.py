"""Validate the generated static-site inputs before a Pages deployment."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Cannot read {path.as_posix()}: {exc}") from exc


def validate_image_path(root: Path, value: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeError(f"Unsafe image path: {value}")
    if path.parts[:2] != ("assets", "generated"):
        raise RuntimeError(f"Image is outside assets/generated: {value}")
    if not (root / Path(*path.parts)).is_file():
        raise RuntimeError(f"Referenced image does not exist: {value}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    required = [
        root / "index.html",
        root / "logo.png",
        root / "data" / "basic_information.json",
        root / "data" / "certification_marks.json",
        root / "data" / "reference_links.json",
        root / "data" / "meta.json",
    ]
    missing = [path.relative_to(root).as_posix() for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Missing required site files: " + ", ".join(missing))

    basic = load_json(required[2])
    marks = load_json(required[3])
    links = load_json(required[4])
    meta = load_json(required[5])
    if not all(isinstance(value, list) for value in (basic, marks, links)):
        raise RuntimeError("The three core JSON root values must be arrays")
    if not isinstance(meta, dict) or meta.get("status") != "success":
        raise RuntimeError("meta.json must report status=success")

    images: list[str] = []
    for record in basic:
        for value in record.values():
            if isinstance(value, list):
                images.extend(item for item in value if isinstance(item, str))
    for record in marks:
        value = record.get("image", [])
        if not isinstance(value, list):
            raise RuntimeError(f"Certification image field is not an array: {record.get('id', '?')}")
        images.extend(item for item in value if isinstance(item, str))
    for value in images:
        validate_image_path(root, value)

    html = required[0].read_text(encoding="utf-8")
    root_relative = re.findall(r"(?:src|href)=[\"']/(?!/)|fetchJson\([\"']/", html)
    if root_relative:
        raise RuntimeError("index.html contains repository-subpath-incompatible root-relative URLs")

    print(
        "Site validation PASSED: "
        f"ENTER1={len(basic)}, ENTER2={len(marks)}, ENTER3={len(links)}, images={len(images)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Site validation FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
