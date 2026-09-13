"""Extract Excel drawing images with exact worksheet anchor relationships."""

from __future__ import annotations

import hashlib
import io
import posixpath
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from PIL import Image, ImageOps


REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XDR_NS = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


@dataclass(frozen=True)
class ImageAnchor:
    sheet: str
    row: int
    column: int
    row_offset: int
    column_offset: int
    sequence: int
    media_path: str
    content_hash: str
    content: bytes

    @property
    def cell(self) -> str:
        number = self.column
        letters = ""
        while number:
            number, remainder = divmod(number - 1, 26)
            letters = chr(65 + remainder) + letters
        return f"{letters}{self.row}"


def _xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        return ET.fromstring(archive.read(name))
    except KeyError as exc:
        raise RuntimeError(f"Missing OOXML part: {name}") from exc


def _relationships(archive: zipfile.ZipFile, rel_path: str, base_path: str) -> dict[str, str]:
    root = _xml(archive, rel_path)
    result: dict[str, str] = {}
    for rel in root.findall(f"{{{PKG_REL_NS}}}Relationship"):
        target = rel.attrib["Target"]
        if target.startswith("/"):
            resolved = target.lstrip("/")
        else:
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(base_path), target))
        result[rel.attrib["Id"]] = resolved
    return result


def extract_image_anchors(workbook_path: Path) -> list[ImageAnchor]:
    anchors: list[ImageAnchor] = []
    with zipfile.ZipFile(workbook_path) as archive:
        workbook = _xml(archive, "xl/workbook.xml")
        workbook_rels = _relationships(
            archive, "xl/_rels/workbook.xml.rels", "xl/workbook.xml"
        )
        sheets = workbook.find(f"{{{MAIN_NS}}}sheets")
        if sheets is None:
            raise RuntimeError("Workbook contains no sheets")

        for sheet in sheets:
            sheet_name = sheet.attrib["name"]
            relation_id = sheet.attrib[f"{{{REL_NS}}}id"]
            sheet_path = workbook_rels[relation_id]
            worksheet = _xml(archive, sheet_path)
            drawing = worksheet.find(f"{{{MAIN_NS}}}drawing")
            if drawing is None:
                continue

            sheet_rel_path = posixpath.join(
                posixpath.dirname(sheet_path), "_rels", posixpath.basename(sheet_path) + ".rels"
            )
            sheet_rels = _relationships(archive, sheet_rel_path, sheet_path)
            drawing_path = sheet_rels[drawing.attrib[f"{{{REL_NS}}}id"]]
            drawing_rel_path = posixpath.join(
                posixpath.dirname(drawing_path),
                "_rels",
                posixpath.basename(drawing_path) + ".rels",
            )
            drawing_rels = _relationships(archive, drawing_rel_path, drawing_path)
            drawing_root = _xml(archive, drawing_path)

            for sequence, anchor in enumerate(list(drawing_root), start=1):
                from_node = anchor.find(f"{{{XDR_NS}}}from")
                if from_node is None:
                    # Absolute anchors cannot be mapped safely to a business row/column.
                    raise RuntimeError(f"Unmappable absolute image anchor in sheet {sheet_name}")
                row_node = from_node.find(f"{{{XDR_NS}}}row")
                col_node = from_node.find(f"{{{XDR_NS}}}col")
                if row_node is None or col_node is None:
                    raise RuntimeError(f"Incomplete image anchor in sheet {sheet_name}")
                row_offset_node = from_node.find(f"{{{XDR_NS}}}rowOff")
                col_offset_node = from_node.find(f"{{{XDR_NS}}}colOff")
                blip = anchor.find(f".//{{{A_NS}}}blip")
                if blip is None:
                    continue
                embed_id = blip.attrib.get(f"{{{REL_NS}}}embed")
                if not embed_id or embed_id not in drawing_rels:
                    raise RuntimeError(f"Broken image relationship in sheet {sheet_name}")
                media_path = drawing_rels[embed_id]
                try:
                    content = archive.read(media_path)
                except KeyError as exc:
                    raise RuntimeError(f"Missing embedded image: {media_path}") from exc
                anchors.append(
                    ImageAnchor(
                        sheet=sheet_name,
                        row=int(row_node.text or "0") + 1,
                        column=int(col_node.text or "0") + 1,
                        row_offset=int(row_offset_node.text or "0") if row_offset_node is not None else 0,
                        column_offset=int(col_offset_node.text or "0") if col_offset_node is not None else 0,
                        sequence=sequence,
                        media_path=media_path,
                        content_hash=hashlib.sha256(content).hexdigest(),
                        content=content,
                    )
                )
    return sorted(
        anchors,
        key=lambda item: (
            item.sheet,
            item.row,
            item.column,
            item.row_offset,
            item.column_offset,
            item.sequence,
        ),
    )


def deduplicate_anchors(
    anchors: Iterable[ImageAnchor], warning_callback
) -> tuple[list[ImageAnchor], int]:
    result: list[ImageAnchor] = []
    seen: set[tuple[str, int, int, str]] = set()
    duplicate_count = 0
    for anchor in anchors:
        key = (anchor.sheet, anchor.row, anchor.column, anchor.content_hash)
        if key in seen:
            duplicate_count += 1
            warning_callback(anchor)
            continue
        seen.add(key)
        result.append(anchor)
    return result, duplicate_count


def save_as_png(content: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(io.BytesIO(content)) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            image.save(destination, format="PNG", optimize=True)
    except Exception as exc:
        raise RuntimeError(f"Cannot decode embedded image for {destination.name}: {exc}") from exc
