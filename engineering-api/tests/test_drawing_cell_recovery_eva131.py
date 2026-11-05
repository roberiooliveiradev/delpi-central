"""EVA#131 — recuperação de células de tabela densa (DEC-VAL-033
evolução, segunda revisão).

Cobre: quadriláteros de 8 pontos, expansão de região por tokens na
faixa da tabela, dpi de referência por página, dpi adaptativo ao
orçamento, falha de render sem derrubar a análise e parentesco de
DRAWING_ONLY sem raiz fabricada.
"""

from engineering_app.application.drawing.bom_structure_comparator import (
    compare_bom_to_drawing,
)
from engineering_app.application.drawing.drawing_investigation import (
    _rect_of,
    recover_absent_table_cells,
)


# --------------------------------------------------------------------------
# fakes
# --------------------------------------------------------------------------

class _FakeRenderer:
    """Captura os parâmetros do último render_region."""

    def __init__(self, fail=False):
        self.calls = []
        self._fail = fail

    def render_region(self, pdf, *, page, region_px, reference_dpi,
                      dpi, margin_px):
        self.calls.append({
            "page": page, "region_px": list(region_px),
            "reference_dpi": reference_dpi, "dpi": dpi,
        })
        if self._fail:
            raise RuntimeError("render_boom")

        class _R:
            image_bytes = b"png"
            offset_px = (0.0, 0.0)

        r = _R()
        r.width, r.height, r.page, r.dpi = 100, 50, page, dpi
        return r


class _FakeOcr:
    def __init__(self, tokens):
        # tokens: list[(text, confidence)]
        self._tokens = tokens

    def extract_text(self, image):
        class _T:
            def __init__(self, text, conf):
                self.text = text
                self.confidence = conf
                self.bounding_box_px = [0, 0, 10, 0, 10, 5, 0, 5]

        class _Res:
            def __init__(self, toks):
                self.tokens = [_T(t, c) for t, c in toks]

        return _Res(self._tokens)


def _cell(text, col=0, box=None, col_type="component_code"):
    return {
        "col": col, "col_type": col_type, "text": text,
        "bounding_box_px": box or [10, 10, 60, 10, 60, 20, 10, 20],
    }


def _table(rows, page=2):
    return {
        "candidate": True,
        "rows": [
            {"row": i, "page": page, "cells": cells}
            for i, cells in enumerate(rows)
        ],
    }


def _opts(**kw):
    base = {
        "pdf_bytes": b"%PDF-fake",
        "budget": {"max_crops": 8, "max_dpi": 300,
                   "max_pixels": 4_000_000},
        "reference_dpi": 200,
    }
    base.update(kw)
    return base


# --------------------------------------------------------------------------
# _rect_of
# --------------------------------------------------------------------------

def test_rect_of_quad_uses_full_extent():
    quad = [40, 100, 80, 102, 78, 120, 38, 118]
    assert _rect_of(quad) == [38, 100, 80, 120]


def test_rect_of_four_and_short():
    assert _rect_of([1, 2, 3, 4]) == [1.0, 2.0, 3.0, 4.0]
    assert _rect_of([1, 2]) is None
    assert _rect_of(None) is None


# --------------------------------------------------------------------------
# região: expansão por tokens na faixa + quad cells
# --------------------------------------------------------------------------

def test_recovery_expands_region_to_tokens_in_table_band():
    """Bloco denso à direita fora das células tipadas entra no crop."""
    table = _table([
        [_cell("50213142", box=[20, 248, 73, 248, 73, 269, 20, 266])],
        [_cell("50224688", box=[20, 990, 73, 990, 73, 1022, 20, 1020])],
    ])
    # token do bloco direito dentro da mesma faixa vertical
    tokens = [{
        "normalized_text": "10080032", "page": 2,
        "bounding_box_px": [350, 260, 397, 260, 397, 284, 350, 284],
    }]
    renderer = _FakeRenderer()
    ocr = _FakeOcr([("10080004", 1.0)])
    found = recover_absent_table_cells(
        missing_codes=["10080004"], component_table=table,
        opts=_opts(renderer=renderer, ocr=ocr,
                   reference_dpi_by_page={2: 110}),
        tokens=tokens,
    )
    assert len(renderer.calls) == 1
    call = renderer.calls[0]
    assert call["page"] == 2
    assert call["reference_dpi"] == 110          # dpi por página, não 200
    assert call["region_px"][2] >= 397           # bloco direito coberto
    assert call["region_px"][0] <= 20
    assert found and found[0]["code"] == "10080004"
    assert found[0]["page"] == 2
    assert found[0]["confidence"] == 1.0
    assert found[0]["method"] == "localized_ocr_recheck"


def test_recovery_tokens_outside_band_do_not_expand():
    """Token fora da faixa vertical da tabela não expande a região."""
    table = _table([
        [_cell("50213142", box=[20, 248, 73, 248, 73, 269, 20, 266])],
    ])
    tokens = [{
        "normalized_text": "99999999", "page": 2,
        "bounding_box_px": [800, 1100, 890, 1100, 890, 1150, 800, 1150],
    }]
    renderer = _FakeRenderer()
    ocr = _FakeOcr([])
    recover_absent_table_cells(
        missing_codes=["10080004"], component_table=table,
        opts=_opts(renderer=renderer, ocr=ocr,
                   reference_dpi_by_page={2: 110}),
        tokens=tokens,
    )
    assert renderer.calls[0]["region_px"][2] < 100


def test_recovery_render_failure_degrades_not_raises():
    table = _table([[_cell("50213142")]])
    found = recover_absent_table_cells(
        missing_codes=["10080004"], component_table=table,
        opts=_opts(renderer=_FakeRenderer(fail=True),
                   ocr=_FakeOcr([])),
    )
    assert found == []


def test_recovery_adaptive_dpi_fits_pixel_budget():
    """Região enorme reduz dpi — nunca abaixo do espaço da página."""
    table = _table([
        [_cell("a", box=[0, 0, 900, 0, 900, 1200, 0, 1200])],
    ])
    renderer = _FakeRenderer()
    recover_absent_table_cells(
        missing_codes=["x"], component_table=table,
        opts=_opts(renderer=renderer, ocr=_FakeOcr([]),
                   reference_dpi=150,
                   budget={"max_crops": 8, "max_dpi": 300,
                           "max_pixels": 1_000_000}),
    )
    call = renderer.calls[0]
    # w*h=1_080_000@150dpi → fit = 150*sqrt(1e6/1.08e6) ≈ 144 →
    # piso = ref_dpi(150) — nunca renderiza abaixo da leitura original
    assert call["dpi"] == 150


def test_recovery_code_not_found_returns_empty():
    table = _table([[_cell("50213142")]])
    found = recover_absent_table_cells(
        missing_codes=["10080004"], component_table=table,
        opts=_opts(renderer=_FakeRenderer(), ocr=_FakeOcr([("abc", 0.9)])),
    )
    assert found == []


# --------------------------------------------------------------------------
# comparador — DRAWING_ONLY sem raiz fabricada
# --------------------------------------------------------------------------

def test_drawing_only_does_not_fabricate_root_parent():
    """Ocorrência tipada sem pai comprovado → parent_code=None, não a raiz."""
    component_table = {
        "candidate": True,
        "row_count": 1,
        "rows": [
            {
                "row": 0, "page": 9,
                "cells": [
                    {"col": 1, "col_type": "component_code",
                     "text": "10080535",
                     "bounding_box_px": [1, 1, 2, 1, 2, 2, 1, 2],
                     "page": 9},
                ],
            },
        ],
        "col_types": {},
    }
    bom = [
        {"occurrence_id": "O0001", "component_code": "50225512",
         "parent_code": "90264030", "depth": 1, "path": "x"},
    ]
    # cobertura completa simulada: 1 ocorrência BOM que casa + 1 drawing-only
    component_table["rows"].append({
        "row": 1, "page": 9,
        "cells": [
            {"col": 0, "col_type": "component_code", "text": "50225512",
             "bounding_box_px": [1, 3, 2, 3, 2, 4, 1, 4], "page": 9},
        ],
    })
    out = compare_bom_to_drawing(
        product_code="90264030",
        bom_occurrences=bom,
        component_table=component_table,
        tokens=[
            {"normalized_text": "10080535", "page": 9},
            {"normalized_text": "50225512", "page": 9},
        ],
        drawing_pages=1,
        code_contexts=None,
        page_coverage={"pdf_page_count": 1, "pages_attempted": [1],
                       "pages_ocr_ok": [1]},
    )
    do = [f for f in out["findings"] if f["type"] == "DRAWING_ONLY"]
    assert do, "DRAWING_ONLY 10080535 esperado"
    f = do[0]
    assert f["item_code"] == "10080535"
    assert f["parent_code"] is None
    assert f["parent_code"] != "90264030"
    assert f["evidence"]["drawing_parent"] is None
    assert f["evidence"]["parent_verified"] is False
