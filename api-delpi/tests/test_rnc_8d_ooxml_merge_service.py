from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from app.domain.services.quality_action_plans.rnc_8d_ooxml_merge_service import (
    merge_template_visual_assets,
)

_TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "content"
    / "templates"
    / "quality"
    / "weg_wfr20997_template.xlsx"
)


@pytest.mark.skipif(not _TEMPLATE.is_file(), reason="Template WEG ausente")
def test_merge_template_visual_assets_restores_drawings():
    with zipfile.ZipFile(_TEMPLATE, "r") as template_zip:
        template_names = set(template_zip.namelist())
        content_types = template_zip.read("[Content_Types].xml")

    minimal_bytes = io.BytesIO()
    with zipfile.ZipFile(minimal_bytes, "w") as minimal_zip:
        minimal_zip.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"></worksheet>',
        )
        minimal_zip.writestr("[Content_Types].xml", content_types)

    merged = merge_template_visual_assets(
        template_path=_TEMPLATE,
        filled_bytes=minimal_bytes.getvalue(),
    )
    with zipfile.ZipFile(io.BytesIO(merged)) as merged_zip:
        names = set(merged_zip.namelist())
        assert "xl/drawings/drawing1.xml" in names
        assert "xl/media/image1.png" in names
        sheet1 = merged_zip.read("xl/worksheets/sheet1.xml").decode()
        assert 'drawing r:id="rId2"' in sheet1
        assert "xl/worksheets/_rels/sheet1.xml.rels" in names
        template_drawings = [n for n in template_names if n.startswith("xl/drawings/")]
        merged_drawings = [n for n in names if n.startswith("xl/drawings/")]
        assert len(merged_drawings) >= len(template_drawings)
