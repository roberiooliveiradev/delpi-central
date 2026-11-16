"""G20 — extração de atributos da tabela de estrutura (caminho OCR).

Fixture real: 95 tokens do pipeline `pdfium_render_paddleocr` sobre o
PDF oficial do produto 90263680 (SHA-256
496e25797c8e62fc0f98bd82179846d8b7712078665e58116b68f32a84613417),
capturados na execução G19 e reutilizados no G20. Nenhum valor vem da
BOM/TOTVS: os atributos observados são sempre os do desenho.

Cobertura RQ01–RQ05:
- descrição do PI extraída da coluna de descrição do bloco-pai;
- descrição da MP extraída da coluna de descrição do componente;
- letras de item A–F na ocorrência correta (C/D repetidos em PIs
  distintos preservam contexto);
- quantidade impressa como observação do desenho;
- hierarquia PI→MP por âncora column_span com expansão simétrica
  evidenciada pela sequência de itens.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engineering_app.application.drawing.understanding import (
    build_understanding,
    drawing_structure_occurrences,
)

FIXTURE = (
    Path(__file__).parent / "fixtures" / "g20_90263680_ocr_tokens.json"
)
PDF_SHA256 = (
    "496e25797c8e62fc0f98bd82179846d8b7712078665e58116b68f32a84613417"
)


@pytest.fixture(scope="module")
def tokens() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def understanding(tokens: list[dict]) -> dict:
    return build_understanding(
        tokens,
        document_hash=PDF_SHA256[:16],
        page=1,
        product_code="90263680",
    )


@pytest.fixture(scope="module")
def occurrences(understanding: dict) -> list[dict]:
    return drawing_structure_occurrences(
        understanding["component_table"]["rows"],
        product_code="90263680",
        document_hash=PDF_SHA256[:16],
    )


EXPECTED_TREE = {
    "10380040": "50213206",
    "10380035": "50213207",
    "10380042": "50233507",
    "10380111": "50233508",
}


def test_headers_and_typed_columns(understanding: dict) -> None:
    ct = understanding["component_table"]
    headers = set(ct.get("headers") or [])
    assert {"código", "descrição", "item", "qtd.", "comp."} <= headers
    roles = set((ct.get("col_types") or {}).values())
    assert {
        "parent_code",
        "parent_description",
        "component_code",
        "description",
        "quantity",
    } <= roles


def test_mp_descriptions_extracted_from_drawing(
    occurrences: list[dict],
) -> None:
    assert len(occurrences) == 8
    for occ in occurrences:
        desc = occ.get("description") or ""
        assert desc, f"occ {occ.get('component_code')} sem descrição"
        assert not desc.isdigit()


def test_item_labels_with_parent_context(
    occurrences: list[dict],
) -> None:
    by_key = {
        (occ.get("parent_code"), occ.get("item")): occ
        for occ in occurrences
    }
    assert ("50233507", "c") in by_key
    assert ("50233508", "c") in by_key
    assert by_key[("50233507", "c")]["component_code"] == "10080136"
    assert by_key[("50233508", "c")]["component_code"] == "10080136"
    items = {occ.get("item") for occ in occurrences}
    assert items == {"a", "b", "c", "d", "e", "f"}


def test_drawing_quantities_observed(occurrences: list[dict]) -> None:
    for occ in occurrences:
        assert occ.get("quantity") == "1"


def test_pi_mp_hierarchy(occurrences: list[dict]) -> None:
    multi = {}
    for occ in occurrences:
        multi.setdefault(occ["component_code"], []).append(
            occ.get("parent_code")
        )
    for code, parents in multi.items():
        if code in EXPECTED_TREE:
            assert EXPECTED_TREE[code] in parents
        else:
            assert set(parents) <= {"50233507", "50233508"}
    for occ in occurrences:
        assert occ.get("parent_state") == "IDENTIFIED"


def test_pi_descriptions_are_drawing_observations(
    occurrences: list[dict],
) -> None:
    pdescs = {
        occ.get("parent_code"): occ.get("parent_description")
        for occ in occurrences
    }
    # Valores CA18* são os impressos no desenho; o TOTVS vigente usa
    # CB18* — a diferença prova que o valor veio do PDF, não da BOM.
    assert pdescs["50233507"] == "ca18marr-00152/10/06-0000-0110"
    assert pdescs["50233508"] == "ca18mabr-00242/10/06-0000-0110"
    assert pdescs["50213206"] == "ca18bran-00512/10/10-0000-0000"
    assert pdescs["50213207"] == "ca18pret-00512/10/10-0000-0000"


def _tok(text: str, x: float, y: float) -> dict:
    return {
        "raw_text": text,
        "normalized_text": text.lower(),
        "bounding_box_px": [x, y, x + 40, y, x + 40, y + 20, x, y + 20],
        "confidence": 0.99,
        "page": 1,
    }


def test_negative_no_header_no_parent_role() -> None:
    """Coluna de códigos sem rótulos: papéis de pai não são inventados.

    Sem faixa de cabeçalho a tipagem recai no pivô esparso×denso; se a
    prova falhar, a coluna permanece component_code — fail-closed.
    """
    toks = [
        _tok("50111111", 100, 200), _tok("10222222", 400, 200),
        _tok("50222222", 100, 240), _tok("10333333", 400, 240),
        _tok("50333333", 100, 280), _tok("10444444", 400, 280),
        _tok("50444444", 100, 320), _tok("10555555", 400, 320),
        _tok("50555555", 100, 360), _tok("10666666", 400, 360),
        _tok("50666666", 100, 400), _tok("10777777", 400, 400),
    ]
    u = build_understanding(
        toks, document_hash="neg1", page=1, product_code="90000000"
    )
    ct = u.get("component_table") or {}
    for row in ct.get("rows") or []:
        src = row.get("parent_group_source")
        assert src != "column_span" or row.get(
            "parent_group_candidate"
        ), "âncora declarada sem código"


def test_ambiguous_anchor_claim_stays_conflict() -> None:
    """Duas âncoras disputando a mesma linha no mesmo rank →
    conflito explícito, nunca pai inventado."""
    from engineering_app.application.drawing.understanding import (
        _apply_token_group_anchors,
    )

    rows = [
        {"cells": [{"col": 0, "text": "50111111"},
                   {"col": 3, "text": "10111111"}], "item": "a"},
        {"cells": [{"col": 3, "text": "10222222"}], "item": "b"},
        {"cells": [{"col": 0, "text": "50222222"},
                   {"col": 3, "text": "10333333"}], "item": "c"},
        {"cells": [{"col": 3, "text": "10444444"}], "item": "a"},
    ]
    _apply_token_group_anchors(rows, [0])
    # Âncora 0 cobre unilateral 0–1; âncora 2 cobre unilateral 1–2 —
    # a linha 1 é reivindicada por dois pais no mesmo rank.
    assert rows[1].get("association_conflict") is True
    assert not rows[1].get("parent_group_candidate")
    assert rows[0].get("parent_group_candidate") == "50111111"
    assert rows[2].get("parent_group_candidate") == "50222222"


def test_g18_comparator_integration(occurrences: list[dict]) -> None:
    """RQ-07: os atributos extraídos alimentam o comparador G18 —
    diferenças candidatas segmentadas, relações verificadas e
    abstenções de quantidade preservadas."""
    from engineering_app.application.drawing.bom_structure_comparator import (
        compare_bom_to_drawing,
    )

    bom = [
        {
            "component_code": "50233507",
            "component_description": "CB18MARR-00152/10/06-0000-3610",
            "parent_code": "90263680",
            "quantity_raw": 1.0,
            "unit_raw": "MI",
            "component_type": "PI",
        },
        {
            "component_code": "10380042",
            "component_description": "CABO EPR 125/150°C 18AWG MR 600V",
            "parent_code": "50233507",
            "quantity_raw": 152.0,
            "unit_raw": "MT",
            "component_type": "MP",
        },
    ]
    toks = json.loads(FIXTURE.read_text(encoding="utf-8"))
    u = build_understanding(
        toks,
        document_hash=PDF_SHA256[:16],
        page=1,
        product_code="90263680",
    )
    cmp = compare_bom_to_drawing(
        product_code="90263680",
        bom_occurrences=bom,
        component_table=u["component_table"],
        tokens=toks,
        pa_unit="MI",
    )
    vr = cmp["validation_report"]
    assert vr["automatic_nc"] is False
    assert vr["engineering_approval"] == "NOT_APPROVED"
    pi_attrs = [
        a
        for r in vr["occurrence_records"]
        for a in r["attributes"]
        if a["attribute"] == "pi_description"
        and a["result"] == "CONFLICT_CANDIDATE"
        and a.get("observed_value") == "ca18marr-00152/10/06-0000-0110"
        and a.get("expected_value")
        == "CB18MARR-00152/10/06-0000-3610"
    ]
    assert pi_attrs, "pi_description obs CA18* × exp CB18* ausente"
    segs = {
        s["segment"]: (s["observed"], s["expected"])
        for s in pi_attrs[0]["segment_differences"]
    }
    assert segs["isolation_prefix"] == ("CA", "CB")
    assert segs["terminal_right"] == ("01", "36")
    rec_mp = [
        r for r in vr["occurrence_records"]
        if r["component_code"] == "10380042"
    ]
    attrs_mp = {a["attribute"]: a for a in rec_mp[0]["attributes"]}
    assert attrs_mp["quantity"]["result"] == "NOT_COMPARABLE"


def test_negative_table_without_descriptions_no_fill() -> None:
    """Tabela só com códigos: descrições ficam vazias — nunca
    preenchidas por fonte externa."""
    toks = [
        _tok("Código", 100, 160), _tok("Comp.", 400, 160),
        _tok("50111111", 100, 200), _tok("10222222", 400, 200),
        _tok("50222222", 100, 240), _tok("10333333", 400, 240),
        _tok("50333333", 100, 280), _tok("10444444", 400, 280),
        _tok("50444444", 100, 320), _tok("10555555", 400, 320),
    ]
    u = build_understanding(
        toks, document_hash="neg2", page=1, product_code="90000000"
    )
    occs = drawing_structure_occurrences(
        (u.get("component_table") or {}).get("rows") or [],
        product_code="90000000",
    )
    for occ in occs:
        assert not occ.get("description")
        assert not occ.get("parent_description")
