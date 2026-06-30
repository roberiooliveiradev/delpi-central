from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

SHEET_DATA_PATTERN = re.compile(r"<sheetData\b[^>]*>.*?</sheetData>", re.DOTALL)
DRAWING_REFERENCE_PATTERN = re.compile(r"<drawing\s+r:id=\"[^\"]+\"\s*/>")
RELATIONSHIP_PATTERN = re.compile(
    r"<Relationship\b[^>]*Target=\"(?P<target>[^\"]+)\"[^>]*/>\s*",
    re.IGNORECASE,
)
CONTENT_TYPE_OVERRIDE_PATTERN = re.compile(
    r"<Override\b[^>]*PartName=\"(?P<part>[^\"]+)\"[^>]*/>\s*",
    re.IGNORECASE,
)

STALE_WORKBOOK_PARTS = ("calcChain.xml", "sharedStrings.xml")
STALE_CONTENT_TYPE_PARTS = ("/xl/calcChain.xml", "/xl/sharedStrings.xml")

SHEET1_DRAWING_ASSET_MARKERS = ("drawing1", "image1.png")


def _replace_sheet_data(*, template_sheet: bytes, filled_sheet: bytes) -> bytes:
    filled_text = filled_sheet.decode("utf-8")
    template_text = template_sheet.decode("utf-8")
    filled_data = SHEET_DATA_PATTERN.search(filled_text)
    if filled_data is None:
        return template_sheet
    if SHEET_DATA_PATTERN.search(template_text) is None:
        return filled_sheet
    merged = SHEET_DATA_PATTERN.sub(filled_data.group(0), template_text, count=1)
    return merged.encode("utf-8")


def _sheet_has_drawing(sheet_xml: bytes | None) -> bool:
    if not sheet_xml:
        return False
    return DRAWING_REFERENCE_PATTERN.search(sheet_xml.decode("utf-8")) is not None


def _remove_relationships(rels_xml: bytes, *, targets: tuple[str, ...]) -> bytes:
    text = rels_xml.decode("utf-8")
    for target in targets:
        text = RELATIONSHIP_PATTERN.sub(
            lambda match: "" if match.group("target") == target else match.group(0),
            text,
        )
    return text.encode("utf-8")


def _remove_content_type_overrides(content_types: bytes, *, parts: tuple[str, ...]) -> bytes:
    text = content_types.decode("utf-8")
    for part in parts:
        text = CONTENT_TYPE_OVERRIDE_PATTERN.sub(
            lambda match: "" if match.group("part") == part else match.group(0),
            text,
        )
    return text.encode("utf-8")


def _is_sheet1_drawing_asset(name: str) -> bool:
    lowered = name.lower()
    return any(marker in lowered for marker in SHEET1_DRAWING_ASSET_MARKERS)


def _collect_annex_overlay(
    *,
    filled_files: dict[str, bytes],
    template_files: dict[str, bytes],
) -> dict[str, bytes]:
    sheet2 = filled_files.get("xl/worksheets/sheet2.xml")
    if not _sheet_has_drawing(sheet2):
        return {}

    overlay: dict[str, bytes] = {"xl/worksheets/sheet2.xml": sheet2}
    sheet2_rels = filled_files.get("xl/worksheets/_rels/sheet2.xml.rels")
    if sheet2_rels:
        overlay["xl/worksheets/_rels/sheet2.xml.rels"] = sheet2_rels

    for name, data in filled_files.items():
        if not name.startswith(("xl/drawings/", "xl/media/")):
            continue
        if _is_sheet1_drawing_asset(name):
            continue
        if template_files.get(name) == data:
            continue
        overlay[name] = data
    return overlay


def _zip_entry_order(*, template_path: Path, output_names: set[str]) -> list[str]:
    with zipfile.ZipFile(template_path, "r") as template_zip:
        ordered = [name for name in template_zip.namelist() if name in output_names]
    for name in sorted(output_names):
        if name not in ordered:
            ordered.append(name)
    return ordered


def merge_template_visual_assets(*, template_path: Path, filled_bytes: bytes) -> bytes:
    """Mescla valores preenchidos no template WEG preservando desenhos e OOXML válido."""
    with zipfile.ZipFile(template_path, "r") as template_zip:
        template_files = {name: template_zip.read(name) for name in template_zip.namelist()}

    with zipfile.ZipFile(io.BytesIO(filled_bytes), "r") as filled_zip:
        filled_files = {name: filled_zip.read(name) for name in filled_zip.namelist()}

    output = dict(template_files)

    filled_sheet1 = filled_files.get("xl/worksheets/sheet1.xml")
    template_sheet1 = template_files.get("xl/worksheets/sheet1.xml")
    if filled_sheet1 and template_sheet1:
        output["xl/worksheets/sheet1.xml"] = _replace_sheet_data(
            template_sheet=template_sheet1,
            filled_sheet=filled_sheet1,
        )

    filled_sheet2 = filled_files.get("xl/worksheets/sheet2.xml")
    template_sheet2 = template_files.get("xl/worksheets/sheet2.xml")
    if filled_sheet2 and template_sheet2 and not _sheet_has_drawing(filled_sheet2):
        output["xl/worksheets/sheet2.xml"] = _replace_sheet_data(
            template_sheet=template_sheet2,
            filled_sheet=filled_sheet2,
        )

    output.update(
        _collect_annex_overlay(
            filled_files=filled_files,
            template_files=template_files,
        )
    )

    for meta_part in ("docProps/core.xml", "docProps/app.xml", "xl/styles.xml"):
        if meta_part in filled_files:
            output[meta_part] = filled_files[meta_part]

    for stale_part in STALE_WORKBOOK_PARTS:
        output.pop(f"xl/{stale_part}", None)

    workbook_rels = output.get("xl/_rels/workbook.xml.rels")
    if workbook_rels:
        output["xl/_rels/workbook.xml.rels"] = _remove_relationships(
            workbook_rels,
            targets=STALE_WORKBOOK_PARTS,
        )

    content_types = output.get("[Content_Types].xml")
    if content_types:
        output["[Content_Types].xml"] = _remove_content_type_overrides(
            content_types,
            parts=STALE_CONTENT_TYPE_PARTS,
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as merged_zip:
        for name in _zip_entry_order(template_path=template_path, output_names=set(output)):
            merged_zip.writestr(name, output[name])
    return buffer.getvalue()
