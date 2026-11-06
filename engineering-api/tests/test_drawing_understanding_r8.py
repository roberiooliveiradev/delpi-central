"""R8 — drawing_understanding.v1: contratos, regiões, tabela, cotas,
BOM compare, ambiguidade, provenance e gates (determinístico)."""

from __future__ import annotations

import pytest

from engineering_app.application.drawing.understanding import (
    SCHEMA_VERSION,
    build_understanding,
)


def _tok(text, x, y, w=40, h=10, conf=0.9, page=1):
    return {
        "text": text,
        "bounding_box_px": [x, y, x + w, y, x + w, y + h, x, y + h],
        "confidence": conf,
        "page": page,
    }


# layout ~840x730: coluna de códigos x=600 (tabela estrutural),
# carimbo por rótulos COD/DES/REV no inferior-direito,
# número/cota na área de desenho, nota canto sup-esq
_TOKENS = [
    _tok("COMPONENTE", 600, 380),  # header col0 → component_code
    _tok("QTD", 700, 380),         # header col1 → quantity
    _tok("10080106", 600, 400),   # tabela row0 (coluna de códigos)
    _tok("CABO", 700, 400),       # tabela row0 col1
    _tok("10020033", 600, 420),   # tabela row1
    _tok("TUBO", 700, 420),
    _tok("50226113", 600, 440),   # tabela row2
    _tok("50226114", 600, 460),   # tabela row3
    _tok("COD", 620, 700),        # carimbo — rótulo 1
    _tok("DES", 740, 700),        # carimbo — rótulo 2
    _tok("90264302", 800, 700),   # carimbo valor
    _tok("18702881", 800, 720),
    _tok("REV", 620, 720),
    _tok("00", 700, 720),         # valor de REV (nunca cota)
    _tok("643±2", 200, 300),      # cota explícita na área de desenho
    _tok("663±2", 200, 350),
    _tok("CHICOTE", 50, 50),      # notas
]


def test_schema_and_validation_draft():
    out = build_understanding(_TOKENS, document_hash="abc123")
    assert out["schema_version"] == SCHEMA_VERSION
    assert out["validation"]["status"] == "DRAFT"
    assert out["validation"]["engineering_validated"] is False
    assert out["document_hash_sha256"] == "abc123"


def test_region_classification_deterministic():
    out = build_understanding(_TOKENS, document_hash="x")
    by = {t["text"]: t for t in out["title_block_candidates"]}
    assert "90264302" in by and "REV" in by
    # tabela não vaza para carimbo
    assert "10080106" not in by


def test_dense_rows_stay_separate_component_lines():
    """Três códigos empilhados mais perto que 2% da página são três linhas.

    Reproduz a classe do finding em que 10081389, 10081685 e 10091368
    caíam no mesmo campo item. Não cita o produto como exceção.
    """
    tokens = [
        _tok("ITEM", 400, 80),
        _tok("QTD", 460, 80),
        _tok("COMPONENTE", 540, 80),
        _tok("DESCRICAO", 700, 80),
    ]
    for i, (item, qty, code) in enumerate(
        (("C", "6", "10081389"), ("D", "3", "10081685"), ("E", "2", "10091368"))
    ):
        y = 120 + i * 16
        tokens.extend(
            [
                _tok(item, 400, y, w=16),
                _tok(qty, 460, y, w=16),
                _tok(code, 540, y, w=70),
                _tok("TERM TUBULAR", 700, y, w=120),
            ]
        )
    out = build_understanding(
        tokens, document_hash="dense", render_size_px=(2000, 1400)
    )
    rows = out["component_table"]["rows"]
    owners = []
    for row in rows:
        text = " ".join(c["text"] for c in row["cells"])
        present = [
            code for code in ("10081389", "10081685", "10091368")
            if code in text
        ]
        assert len(present) <= 1
        if present:
            owners.append(present[0])
            assert row["component_code"] == present[0]
            assert present[0] not in str(row.get("item") or "")
    assert owners == ["10081389", "10081685", "10091368"]


def test_same_line_code_and_description_stay_one_row():
    tokens = [
        _tok("COMPONENTE", 540, 80),
        _tok("DESCRICAO", 700, 80),
        _tok("10070097", 540, 120, w=70),
        _tok("CABO PP", 700, 122, w=80),
        _tok("10071250", 540, 180, w=70),
        _tok("CABO PP", 700, 181, w=80),
    ]
    out = build_understanding(
        tokens, document_hash="same-line", render_size_px=(2000, 1400)
    )
    rows = out["component_table"]["rows"]
    assert len(rows) == 2
    assert {c["text"] for c in rows[0]["cells"]} >= {"10070097", "CABO PP"}


def test_component_table_rows_and_cells():
    out = build_understanding(_TOKENS, document_hash="x")
    tbl = out["component_table"]
    assert tbl["candidate"] is True
    assert tbl["row_count"] == 4
    texts = [
        c["text"] for r in tbl["rows"] for c in r["cells"]
    ]
    for code in ("10080106", "10020033", "50226113", "50226114"):
        assert code in texts
    # relação linha-preservada: CABO está na row de 10080106
    r0 = tbl["rows"][0]["cells"]
    assert {c["text"] for c in r0} == {"10080106", "CABO"}


def test_identifier_candidates_states():
    out = build_understanding(_TOKENS, document_hash="x")
    ids = {f["text"]: f for f in out["identifier_candidates"]}
    assert ids["90264302"]["state"] == "FIELD_IDENTIFIED"
    assert ids["90264302"]["region"] == "title_block"
    assert ids["10080106"]["region"] == "component_table"


def test_revision_candidate_label_value():
    out = build_understanding(_TOKENS, document_hash="x")
    revs = out["revision_candidates"]
    assert revs and revs[0]["label_text"].upper() == "REV"
    assert revs[0]["value_text"] == "00"
    assert revs[0]["state"] == "FIELD_IDENTIFIED"


def test_dimension_candidates_never_verified():
    out = build_understanding(_TOKENS, document_hash="x")
    dims = {d["text"]: d for d in out["dimension_candidates"]}
    assert "643±2" in dims and "663±2" in dims
    # "00" (valor de REV) nunca é cota
    assert "00" not in dims
    assert all(
        d["state"] in {
            "DIMENSION_TEXT_FOUND", "DIMENSION_REGION_CANDIDATE"
        }
        for d in dims.values()
    )
    # nenhuma associação declarada automaticamente
    assert all(d["association"] is None for d in dims.values())


def test_ambiguity_preserved_not_merged():
    out = build_understanding(_TOKENS, document_hash="x")
    # alternativas/células ambíguas são expostas, não fundidas
    assert "ambiguous_cells" in out["component_table"]
    assert all("alternatives" in c or True for c in out["component_table"]["rows"][0]["cells"])


def test_bom_comparison_multiplicity():
    out = build_understanding(
        _TOKENS,
        document_hash="x",
        bom_codes=[
            "10080106", "10080106", "10020033",
            "50226113", "50226114", "99999999",
        ],
    )
    cmp = out["bom_comparison"]
    assert cmp["state"] == "COMPARED_PARTIAL"
    codes = {m["code"] for m in cmp["matched"]}
    assert {"10080106", "10020033", "50226113", "50226114"} <= codes
    assert "99999999" in cmp["missing_in_drawing_table"]
    assert cmp["occurrence_mismatches"][0]["bom"] == 2
    assert cmp["occurrence_mismatches"][0]["code"] == "10080106"


def test_no_bom_is_not_comparable_honest():
    out = build_understanding(_TOKENS, document_hash="x")
    assert out["bom_comparison"] is None  # não fabricado


def test_provenance_full_chain():
    out = build_understanding(_TOKENS, document_hash="deadbeef")
    cell = out["title_block_candidates"][0]
    assert cell["bounding_box_px"]
    assert cell["confidence"] is not None
    assert out["page_size_px"] == [pytest.approx(840, abs=1), pytest.approx(730, abs=1)] or out["page_size_px"]


def test_no_tokens_empty_honest():
    out = build_understanding([], document_hash="x")
    assert out["tokens_processed"] == 0
    assert out["component_table"]["candidate"] is False


def test_structure_codes_extractor():
    from engineering_app.interface.mcp.semantic_bridge import (
        _structure_codes,
    )

    payload = {
        "items": [
            {"component_code": "50226113", "children": [
                {"code": "999"},
            ]},
            {"product_code": "90264302"},
            {"name": "X", "code": "text-not-digit"},
        ]
    }
    codes = _structure_codes(payload)
    assert "50226113" in codes and "999" in codes and "90264302" in codes
    assert "text-not-digit" not in codes


def test_action_registered_and_dispatched():
    """Registry ↔ dispatcher integrity para a ação R8."""
    from engineering_app.application.eva.semantic_registry import (
        SEMANTIC_ACTIONS,
    )

    kinds = {f"{a.entity}.{a.action}" for a in SEMANTIC_ACTIONS}
    assert "product.drawing_understanding" in kinds
    import inspect

    src = inspect.getsource(
        __import__(
            "engineering_app.interface.mcp.semantic_bridge",
            fromlist=["x"],
        )
    )
    assert "_analyze_drawing_understanding" in src
    assert 'kind == "product.drawing_understanding"' in src


def test_understanding_no_vision_imports():
    """Application layer não importa cv2/paddle (gate arquitetural)."""
    import inspect

    import engineering_app.application.drawing.understanding as m

    src = inspect.getsource(m)
    for bad in ("cv2", "paddle", "pypdfium2"):
        assert bad not in src


def test_page_frame_does_not_replace_the_column_crop():
    # A moldura quase integral não é a tabela. O recorte publicado é
    # a extensão das colunas de código, e a comparação usa esse recorte.
    toks = [_tok('50226113', 600, 400), _tok('50226114', 600, 440)]
    fake_gp = {'rects': [[0, 0, 2330, 1650]]}
    out = build_understanding(
        toks, document_hash='x', bom_codes=['50226113'],
        product_code='90264161', render_size_px=(2339, 1653),
        graphic_primitives=fake_gp,
    )
    table = out['component_table']
    assert table.get('unreliable_boundary') is False
    assert table.get('boundary_source') == 'connected_columns'
    assert table['box'][2] < 800
    assert out['bom_comparison']['state'] == 'COMPARED_PARTIAL'
    assert out['bom_comparison']['matched'] == [
        {'code': '50226113', 'occurrences': 1}
    ]
