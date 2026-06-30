from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CONTENT_TYPES_NS = {"t": "http://schemas.openxmlformats.org/package/2006/content-types"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
DRAWING_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing"
)

TEMPLATE_VISUAL_PREFIXES = (
    "xl/drawings/",
    "xl/media/",
    "xl/printerSettings/",
)

SHEET_DRAWING_REL_FILES = (
    "xl/worksheets/_rels/sheet1.xml.rels",
    "xl/worksheets/_rels/sheet2.xml.rels",
)


def _merge_content_types(
    template_xml: bytes,
    output_xml: bytes,
    *,
    output_names: frozenset[str],
) -> bytes:
    template_root = ET.fromstring(template_xml)
    output_root = ET.fromstring(output_xml)
    tag_default = f"{{{CONTENT_TYPES_NS['t']}}}Default"
    tag_override = f"{{{CONTENT_TYPES_NS['t']}}}Override"

    def _key(node: ET.Element) -> tuple[str, str]:
        if node.tag == tag_default:
            return ("default", node.attrib.get("Extension", ""))
        return ("override", node.attrib.get("PartName", ""))

    merged: dict[tuple[str, str], ET.Element] = {}
    for node in list(output_root):
        merged[_key(node)] = node

    existing_parts = {f"/{name}" for name in output_names}
    template_default_extensions = {"png", "jpeg", "bin"}

    for node in list(template_root):
        if node.tag == tag_default:
            extension = node.attrib.get("Extension", "")
            if extension in template_default_extensions and _key(node) not in merged:
                merged[_key(node)] = node
            continue
        if node.tag != tag_override:
            continue
        part_name = node.attrib.get("PartName", "")
        if part_name in existing_parts and _key(node) not in merged:
            merged[_key(node)] = node

    for node in list(output_root):
        output_root.remove(node)
    for node in sorted(merged.values(), key=lambda item: ET.tostring(item)):
        output_root.append(node)
    return ET.tostring(output_root, encoding="utf-8", xml_declaration=True)


RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SHEET_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _ensure_sheet_drawing_reference(sheet_xml: bytes) -> bytes:
    text = sheet_xml.decode("utf-8")
    if re.search(r"<drawing\s+r:id=", text):
        return sheet_xml
    if 'xmlns:r="' not in text:
        text = re.sub(
            rf'(<worksheet xmlns="{re.escape(SHEET_MAIN_NS)}")',
            rf'\1 xmlns:r="{RELATIONSHIPS_NS}"',
            text,
            count=1,
        )
    return text.replace("</worksheet>", '<drawing r:id="rId2"/></worksheet>').encode("utf-8")


def _sheet_has_drawing_relationship(sheet_rels_xml: bytes) -> bool:
    root = ET.fromstring(sheet_rels_xml)
    for rel in root.findall("r:Relationship", REL_NS):
        if rel.attrib.get("Type") == DRAWING_REL_TYPE:
            return True
    return False


def merge_template_visual_assets(*, template_path: Path, filled_bytes: bytes) -> bytes:
    """Preserva setas, imagens e printerSettings do template WEG após openpyxl.save()."""
    with zipfile.ZipFile(template_path, "r") as template_zip:
        template_files = {name: template_zip.read(name) for name in template_zip.namelist()}

    with zipfile.ZipFile(io.BytesIO(filled_bytes), "r") as output_zip:
        output_files = {name: output_zip.read(name) for name in output_zip.namelist()}

    for name, data in template_files.items():
        if name.startswith(TEMPLATE_VISUAL_PREFIXES):
            output_files[name] = data

    for rel_file in SHEET_DRAWING_REL_FILES:
        template_rels = template_files.get(rel_file)
        if template_rels is None:
            continue
        output_rels = output_files.get(rel_file)
        if output_rels is None or not _sheet_has_drawing_relationship(output_rels):
            output_files[rel_file] = template_rels

    for sheet_file in ("xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"):
        if sheet_file in output_files:
            output_files[sheet_file] = _ensure_sheet_drawing_reference(output_files[sheet_file])

    if "[Content_Types].xml" in template_files and "[Content_Types].xml" in output_files:
        output_files["[Content_Types].xml"] = _merge_content_types(
            template_files["[Content_Types].xml"],
            output_files["[Content_Types].xml"],
            output_names=frozenset(output_files),
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as merged_zip:
        for name, data in output_files.items():
            merged_zip.writestr(name, data)
    return buffer.getvalue()
