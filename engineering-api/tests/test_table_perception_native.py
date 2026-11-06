"""Percepção tabular nativa — página, spans e consumo pelo Understanding."""
import hashlib
import inspect

from engineering_app.application.drawing.perception_contract import (
    cells_from_html_structure,
    resolve_requested_page,
    validate_crop_box,
    render_matches_tokens,
)
from engineering_app.application.drawing.understanding import (
    apply_native_table_observations,
    rows_from_native_cells,
)


HTML = (
    "<table><tr><td>Item</td><td>Qtd</td><td>Codigo</td><td>Descricao</td></tr>"
    "<tr><td>C</td><td>6</td><td>10081389</td><td>TERM. TUBULAR</td></tr>"
    "<tr><td>D</td><td>3</td><td>10081685</td>"
    "<td>TERM. TUBULAR DUPLO 1,50MM2</td></tr>"
    "<tr><td>E</td><td>2</td><td>10091368</td><td>CONECTOR STOCK</td></tr>"
    "</table>"
)


def _boxes(count):
    return [[i, 0, i + 1, 1] for i in range(count)]


def test_html_keeps_native_rows_and_spans():
    html = (
        '<table><tr><td></td><td></td></tr>'
        '<tr><td rowspan="2"></td><td></td></tr>'
        "<tr><td></td></tr></table>"
    )
    parsed = cells_from_html_structure(html, _boxes(5))
    assert parsed["consistent"] is True
    assert [c["row"] for c in parsed["cells"]] == [0, 0, 1, 1, 2]
    assert parsed["cells"][2]["rowspan"] == 2
    assert parsed["cells"][4]["col"] == 1
    assert parsed["cells"][4]["row"] != 4 // 8


def test_bbox_mismatch_and_span_conflict_stay_limitations():
    parsed = cells_from_html_structure(HTML, _boxes(3))
    assert parsed["consistent"] is False
    assert "bbox_count_mismatch" in parsed["limitations"]
    conflict = cells_from_html_structure(
        '<table><tr><td></td><td rowspan="2"></td></tr>'
        '<tr><td colspan="2"></td></tr></table>',
        _boxes(3),
    )
    assert "span_conflict" in conflict["limitations"]


def test_page_and_crop_rejects():
    assert resolve_requested_page([9], 14) == (9, None)
    assert resolve_requested_page([0], 14)[1] == "PAGE_NOT_IN_DOCUMENT"
    assert resolve_requested_page([15], 14)[1] == "PAGE_NOT_IN_DOCUMENT"
    assert validate_crop_box(None, 100, 80) == "NO_TABLE_REGION"
    assert validate_crop_box([10, 10, 5, 20], 100, 80) == "INVALID_CROP"
    assert validate_crop_box([-5, 0, 10, 10], 100, 80) == "INVALID_CROP"
    assert validate_crop_box([0, 0, 10, 10], 100, 80) is None
    assert render_matches_tokens((100, 80), (10, 10)) is False
    assert render_matches_tokens((100, 80), (101, 80)) is True


def test_parser_has_no_product_semantics():
    assert "product_code" not in inspect.signature(
        cells_from_html_structure
    ).parameters
    source = inspect.getsource(cells_from_html_structure)
    assert "title_block" not in source
    assert "70260008" not in source


def test_three_native_rows_stay_separate():
    parsed = cells_from_html_structure(HTML, _boxes(16))
    cells = []
    texts = [
        "Item", "Qtd", "Codigo", "Descricao",
        "C", "6", "10081389", "TERM. TUBULAR",
        "D", "3", "10081685", "TERM. TUBULAR DUPLO 1,50MM2",
        "E", "2", "10091368", "CONECTOR STOCK",
    ]
    for spec, text in zip(parsed["cells"], texts):
        cells.append({**spec, "text": text})
    rows, _types = rows_from_native_cells(cells, page=9)
    assert [row["item"] for row in rows] == ["C", "D", "E"]
    assert [row["quantity"] for row in rows] == ["6", "3", "2"]
    assert [row["component_code"] for row in rows] == [
        "10081389", "10081685", "10091368",
    ]
    assert all(row["page"] == 9 for row in rows)
    joined = " ".join(row["component_code"] for row in rows)
    assert joined.count("10081389") == 1


def test_mixed_cell_is_inconclusive_and_multiline_stays_one_row():
    cells = [
        {"row": 0, "col": 0, "text": "Codigo", "rowspan": 1, "colspan": 1},
        {"row": 0, "col": 1, "text": "Descricao", "rowspan": 1, "colspan": 1},
        {
            "row": 1, "col": 0, "rowspan": 1, "colspan": 1,
            "text": "6 10081389",
        },
        {
            "row": 1, "col": 1, "rowspan": 1, "colspan": 1,
            "text": "TERM. TUBULAR DUPLO 1,50MM2",
        },
    ]
    rows, _types = rows_from_native_cells(cells, page=9)
    assert len(rows) == 1
    assert rows[0]["association_status"] == "INCONCLUSIVE"
    assert rows[0]["quantity"] is None
    assert "TERM. TUBULAR DUPLO" in rows[0]["description"]


def test_rowspan_text_is_not_copied_and_missing_parent_is_not_invented():
    cells = [
        {"row": 0, "col": 0, "text": "Codigo", "rowspan": 1, "colspan": 1},
        {"row": 0, "col": 1, "text": "Conjunto", "rowspan": 1, "colspan": 1},
        {"row": 1, "col": 0, "text": "10081389", "rowspan": 1, "colspan": 1},
        {
            "row": 1, "col": 1, "text": "70260008",
            "rowspan": 2, "colspan": 1,
        },
        {"row": 2, "col": 0, "text": "10081685", "rowspan": 1, "colspan": 1},
    ]
    rows, _types = rows_from_native_cells(cells, page=9)
    by_code = {row["component_code"]: row for row in rows}
    anchor = by_code["10081389"]
    child = by_code["10081685"]
    assert any(cell["text"] == "70260008" for cell in anchor["cells"])
    assert all(cell["text"] != "70260008" for cell in child["cells"])
    assert child.get("parent") is None


def test_failed_observation_keeps_clustered_row_and_stamp_stays_neutral():
    fused = {
        "page": 9,
        "item": "D C E 6 3 2 10081389 10081685 10091368",
        "component_code": None,
        "cells": [],
    }
    understanding = {
        "component_table": {"rows": [fused], "row_count": 1, "col_types": {}},
        "limitations": [],
    }
    kept = apply_native_table_observations(
        understanding,
        [{
            "region_type": "component_table",
            "page": 9,
            "result": {"error_kind": "COORDINATE_MISMATCH", "cells": []},
        }],
    )
    assert kept["component_table"]["rows"] == [fused]
    stamp_cells = [
        {"row": 0, "col": 0, "text": "REV", "rowspan": 1, "colspan": 1},
        {"row": 1, "col": 0, "text": "02", "rowspan": 1, "colspan": 1},
    ]
    reused = apply_native_table_observations(
        kept,
        [{
            "region_type": "title_block",
            "page": 1,
            "result": {
                "tables": [{"structure_consistent": True}],
                "cells": stamp_cells,
                "processed_pages": [1],
                "render": {"processed_page": 1, "requested_page": 1},
            },
        }],
    )
    assert reused["component_table"]["rows"] == [fused]
    assert reused["table_perception"][-1]["region_type"] == "title_block"
    assert reused["table_perception"][-1]["cells"] == stamp_cells


def test_engine_renders_requested_page_and_preserves_span(monkeypatch):
    from engineering_app.infrastructure.extraction import engine_adapters

    log = []

    class FakeBitmap:
        def to_pil(self):
            from PIL import Image
            return Image.new("RGB", (120, 80), "white")

    class FakePage:
        def __init__(self, index):
            self.index = index

        def render(self, scale):
            log.append(("render", self.index, round(scale, 4)))
            return FakeBitmap()

    class FakePdf:
        def __len__(self):
            return 14

        def __getitem__(self, index):
            log.append(("page", index))
            return FakePage(index)

        def close(self):
            log.append("close")

    def open_pdf(_pdf_bytes):
        return FakePdf(), "unused"

    def predict(_crop):
        html = (
            '<table><tr><td rowspan="2"></td><td></td></tr>'
            "<tr><td></td></tr></table>"
        )
        return [{
            "structure": [html],
            "bbox": [[0, 0, 10, 20], [10, 0, 20, 10], [10, 10, 20, 20]],
            "structure_score": 0.91,
        }]

    monkeypatch.setattr(engine_adapters, "_open_pdf_document", open_pdf)
    monkeypatch.setattr(engine_adapters, "_predict_table_structure", predict)
    pdf = b"page-nine"
    digest = hashlib.sha256(pdf).hexdigest()
    result = engine_adapters.TableStructureEngine().run(
        pdf,
        document_hash_sha256=digest,
        pages=[9],
        crop_box=[0, 0, 40, 40],
        ocr_tokens=[{
            "raw_text": "10081389",
            "bounding_box_px": [12, 12, 18, 18],
            "page": 9,
        }],
        expected_render_px=(120, 80),
    )
    assert result["error_kind"] is None
    assert result["render"]["requested_page"] == 9
    assert result["render"]["processed_page"] == 9
    assert result["render"]["page_index"] == 8
    assert result["pdf_sha_match"] is True
    assert ("page", 8) in log
    assert all(entry[1] != 0 for entry in log if entry[0] == "page")
    assert result["cells"][0]["rowspan"] == 2
    assert result["cells"][0]["row"] == 0
    assert result["cells"][2]["row"] == 1
    assert result["cells"][2]["col"] == 1
    assert "10081389" in result["cells"][2]["text"]


def test_engine_rejects_missing_page_invalid_crop_and_scale(monkeypatch):
    from engineering_app.infrastructure.extraction import engine_adapters

    class FakeBitmap:
        def to_pil(self):
            from PIL import Image
            return Image.new("RGB", (120, 80), "white")

    class FakePdf:
        def __len__(self):
            return 2

        def __getitem__(self, _index):
            class Page:
                def render(self, scale):
                    return FakeBitmap()
            return Page()

        def close(self):
            return None

    monkeypatch.setattr(
        engine_adapters, "_open_pdf_document", lambda _b: (FakePdf(), "t")
    )
    called = {}

    def predict(_crop):
        called["yes"] = True
        return []

    monkeypatch.setattr(engine_adapters, "_predict_table_structure", predict)
    engine = engine_adapters.TableStructureEngine()
    missing = engine.run(b"x", document_hash_sha256="a" * 64, pages=[9])
    assert missing["error_kind"] == "PAGE_NOT_IN_DOCUMENT"
    assert "yes" not in called
    invalid = engine.run(
        b"x", document_hash_sha256="a" * 64, pages=[1],
        crop_box=[30, 10, 10, 20],
    )
    assert invalid["error_kind"] == "INVALID_CROP"
    mismatch = engine.run(
        b"x", document_hash_sha256="a" * 64, pages=[1],
        crop_box=[0, 0, 10, 10], expected_render_px=(10, 10),
    )
    assert mismatch["error_kind"] == "COORDINATE_MISMATCH"
    assert "yes" not in called


def _tok(text, x, y, w=40, h=12):
    return {
        "raw_text": text,
        "normalized_text": text,
        "bounding_box_px": [x, y, x + w, y, x + w, y + h, x, y + h],
        "page": 1,
    }


def _component_region(result):
    for region in result["regions"]:
        if region["type"] == "component_table":
            return region
    return None


def test_table_crop_excludes_admin_text_beyond_the_column_gap():
    from engineering_app.application.drawing.understanding import (
        build_understanding,
    )

    tokens = []
    for index, (item, qty, code) in enumerate(
        (("A", "1", "11111111"), ("C", "6", "22222222"), ("D", "3", "33333333"))
    ):
        y = 100 + index * 30
        tokens.extend((
            _tok(item, 200, y, 16),
            _tok(qty, 250, y, 16),
            _tok(code, 300, y, 70),
            _tok("CABO", 420, y, 80),
        ))
    tokens.append(_tok("CLIENTE: BUHLER", 900, 130, 140))
    result = build_understanding(
        tokens, document_hash="x", page=1, render_size_px=(1100, 800),
        graphic_primitives={"rects": [[0, 0, 1050, 280]]},
    )
    region = _component_region(result)
    assert region is not None
    assert region["box_px"][2] < 900
    assert result["component_table"]["boundary_source"] == "connected_columns"


def test_nearby_code_column_remains_inside_the_crop():
    from engineering_app.application.drawing.understanding import (
        build_understanding,
    )

    tokens = []
    for index, (left, right) in enumerate(
        (("11111111", "44444444"), ("22222222", "55555555"))
    ):
        y = 80 + index * 28
        tokens.extend((
            _tok(left, 200, y, 70),
            _tok(right, 320, y, 70),
        ))
    result = build_understanding(
        tokens, document_hash="x", page=1, render_size_px=(1000, 600),
    )
    region = _component_region(result)
    assert region is not None
    assert region["box_px"][0] < 220
    assert region["box_px"][2] > 380


def test_title_labels_alone_do_not_create_a_component_crop():
    from engineering_app.application.drawing.understanding import (
        build_understanding,
    )

    tokens = [
        _tok("COD", 800, 100, 30),
        _tok("REV", 800, 140, 30),
        _tok("CLIENTE", 800, 180, 60),
    ]
    result = build_understanding(
        tokens, document_hash="x", page=1, render_size_px=(1000, 600),
    )
    assert _component_region(result) is None


def test_predict_failure_discards_cached_ocr_engine(monkeypatch):
    from engineering_app.infrastructure.extraction import (
        paddleocr_adapter as mod,
    )

    if mod.np is None or mod.cv2 is None:
        return
    adapter = mod.PaddleOcrAdapter()

    class Dead:
        def predict(self, _image):
            raise RuntimeError("predictor")

    adapter._engine = Dead()
    monkeypatch.setattr(mod, "_CV2_AVAILABLE", True)
    monkeypatch.setattr(mod, "_PADDLEOCR_AVAILABLE", True)
    monkeypatch.setattr(mod.np, "frombuffer", lambda *_a, **_k: object())
    monkeypatch.setattr(
        mod.cv2, "imdecode", lambda *_a, **_k: mod.np.zeros((4, 4, 3))
    )
    try:
        adapter.extract_text(b"png")
        raised = False
    except mod.PdfExtractionError as exc:
        raised = True
        assert "RuntimeError" in str(exc)
    assert raised
    assert adapter._engine is None
