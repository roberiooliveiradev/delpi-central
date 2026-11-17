"""E1/VAL-01 B1 — identificação de balões e associação com a tabela.

Cobre RQ-B1-01..05: detecção por primitiva circular (somente
drawing_area), guards de falso balão, associação candidata por rótulo,
multiplicidade legítima, estados MATCH_CANDIDATE/AMBIGUOUS/NOT_LOCATED/
NOT_COMPARABLE e a seção aditiva ``balloon_table_validation``.
"""
from engineering_app.application.drawing.drawing_investigation import (
    build_balloon_table_validation,
    identify_balloon_candidates,
)
from engineering_app.application.drawing.object_profiles_builder import (
    build_object_profiles,
)
from engineering_app.application.drawing.understanding import (
    build_document_understanding,
    build_understanding,
)

SHA = "sha-b1"
SRC = "api-delpi:/products/90264302/structure"


def _tok(text, x1, y1, x2, y2, page=1):
    """Token OCR quad (8 coords), como produzido pelo pipeline real."""
    return {
        "text": text,
        "normalized_text": text,
        "bounding_box_px": [x1, y1, x2, y1, x2, y2, x1, y2],
        "confidence": 0.95,
        "page": page,
    }


def _circle(x1, y1, x2, y2):
    return {"type": "circle", "bounding_box_px": [x1, y1, x2, y2]}


def _row(i, code, item=None, qty="1", desc=None):
    fields = {"component_code": {"normalized_value": code}}
    if item is not None:
        fields["item"] = {"normalized_value": item}
    if qty is not None:
        fields["quantity"] = {"normalized_value": qty}
    if desc is not None:
        fields["description"] = {"raw_text": desc}
    return {
        "row": i, "page": 1, "fields": fields,
        "association_status": "FIELD_IDENTIFIED", "cells": [],
    }


def _balloon(label, x1=10, y1=10, x2=30, y2=30, page=1):
    return {
        "item_label": label,
        "normalized_label": label.upper(),
        "page": page,
        "bounding_box_px": [x1, y1, x2, y2],
        "token_bounding_box_px": [x1 + 4, y1 + 4, x2 - 4, y2 - 4],
        "coordinate_system": "pixels_pdfium_top_left",
        "identification_method": "primitive_containment",
    }


def _u(rows=None, balloons=None):
    return {
        "schema_version": "drawing_understanding.v1",
        "document_hash_sha256": SHA,
        "page": 1,
        "component_table": {
            "candidate": True, "rows": rows or [],
            "row_count": len(rows or []),
        },
        "balloon_candidates": balloons or [],
        "regions": [],
        "dimension_candidates": [],
        "identifier_candidates": [],
    }


# ---------- RQ-B1-01 — detecção por primitiva circular -------------------


def test_b1_detects_balloon_in_drawing_area():
    """Token curto contido em círculo na área gráfica → candidato."""
    tokens = [_tok("A1", 605, 405, 625, 425)]
    prims = {"circles": [_circle(595, 395, 635, 435)], "rects": [],
             "h_lines": [], "v_lines": []}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert len(u["balloon_candidates"]) == 1
    b = u["balloon_candidates"][0]
    assert b["item_label"] == "A1"
    assert b["normalized_label"] == "A1"
    assert b["page"] == 1
    assert b["bounding_box_px"] == [595, 395, 635, 435]
    assert b["identification_method"] == "primitive_containment"
    assert b["coordinate_system"] == "pixels_pdfium_top_left"


def test_b1_numeric_and_letter_labels():
    """Rótulos '1', 'A', 'B' (casos 90261723/90261731) são detectados."""
    tokens = [
        _tok("1", 605, 405, 615, 425),
        _tok("A", 705, 505, 715, 525),
        _tok("B", 805, 305, 815, 325),
    ]
    prims = {"circles": [
        _circle(595, 395, 625, 435),
        _circle(695, 495, 725, 535),
        _circle(795, 295, 825, 335),
    ]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    labels = {b["normalized_label"] for b in u["balloon_candidates"]}
    assert labels == {"1", "A", "B"}


def test_b1_multiplicity_preserved_two_same_label():
    """Dois balões 'B' nas duas extremidades do cabo são preservados."""
    tokens = [
        _tok("B", 605, 405, 615, 425),
        _tok("B", 805, 605, 815, 625),
    ]
    prims = {"circles": [_circle(595, 395, 625, 435),
                         _circle(795, 595, 825, 635)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert [b["normalized_label"] for b in u["balloon_candidates"]] == [
        "B", "B"]
    # posições distintas — não colapsa em duplicata
    boxes = {tuple(b["bounding_box_px"]) for b in u["balloon_candidates"]}
    assert len(boxes) == 2


def test_b1_no_primitives_no_balloons():
    """Sem primitiva circular → zero balões (nunca fabricados)."""
    tokens = [_tok("A1", 605, 405, 625, 425)]
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700),
        graphic_primitives={"circles": [], "rects": [[0, 0, 50, 50]]},
    )
    assert u["balloon_candidates"] == []
    assert u["balloon_excluded"] == []


def test_b1_token_outside_circle_ignored():
    tokens = [_tok("A1", 900, 600, 920, 620)]
    prims = {"circles": [_circle(595, 395, 635, 435)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert u["balloon_candidates"] == []


def test_b1_margin_zone_circle_excluded():
    """Marcador de zona da folha (círculo na borda) é excluído com razão."""
    tokens = [_tok("C", 5, 400, 15, 420)]
    prims = {"circles": [_circle(0, 390, 25, 430)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert u["balloon_candidates"] == []
    reasons = [e["excluded_reason"] for e in u["balloon_excluded"]]
    assert "circle_in_page_margin_zone" in reasons


def test_b1_table_region_token_never_balloon():
    """Rótulo dentro da tabela de materiais não vira balão."""
    # Tabela âncora: ≥2 códigos de componente na mesma coluna.
    tokens = [
        _tok("90264061", 700, 100, 760, 115),
        _tok("50222487", 700, 140, 760, 155),
        _tok("A1", 640, 100, 655, 115),
        _tok("B", 640, 140, 655, 155),
    ]
    prims = {"circles": [_circle(632, 95, 662, 122),
                         _circle(632, 135, 662, 162)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    labels = {b["normalized_label"] for b in u["balloon_candidates"]}
    assert "A1" not in labels and "B" not in labels


def test_b1_title_block_token_never_balloon():
    """Número circulado no carimbo não vira balão."""
    tb_tokens = [
        _tok("DESENHO", 800, 640, 860, 655),
        _tok("ESCALA", 800, 660, 850, 675),
        _tok("02", 870, 660, 890, 675),
    ]
    prims = {"circles": [_circle(860, 652, 898, 682)]}
    u = build_understanding(
        tb_tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    labels = {b["normalized_label"] for b in u["balloon_candidates"]}
    assert "02" not in labels


def test_b1_long_token_rejected():
    """Identificador > 3 chars ou não-alfanumérico não é rótulo."""
    tokens = [_tok("A100", 605, 405, 640, 425),
              _tok("A-1", 705, 505, 740, 525)]
    prims = {"circles": [_circle(595, 395, 650, 435),
                         _circle(695, 495, 750, 535)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert u["balloon_candidates"] == []


def test_b1_document_level_merges_pages():
    """Multipágina: candidatos propagam com a página de origem."""
    tokens = [
        _tok("A1", 605, 405, 625, 425, page=1),
        _tok("B", 705, 505, 715, 525, page=2),
    ]
    prims = {
        1: {"circles": [_circle(595, 395, 635, 435)]},
        2: {"circles": [_circle(695, 495, 725, 535)]},
    }
    u = build_document_understanding(
        tokens, document_hash=SHA,
        render_size_by_page={1: (1000, 700), 2: (1000, 700)},
        graphic_primitives_by_page=prims,
    )
    labels = {(b["normalized_label"], b["page"])
              for b in u["balloon_candidates"]}
    assert labels == {("A1", 1), ("B", 2)}


def test_b1_legacy_dict_and_list_primitive_shapes():
    """identify_balloon_candidates aceita dict real e lista tipada."""
    toks = [{"normalized_text": "7", "region": "drawing_area",
             "bounding_box_px": [50, 58, 60, 58, 60, 70, 50, 70]}]
    u_dict = {"graphic_primitives": {"circles": [_circle(
        40, 50, 70, 80)]}, "_tokens": toks}
    u_list = {"graphic_primitives": [_circle(40, 50, 70, 80)],
              "_tokens": toks}
    for u in (u_dict, u_list):
        out = identify_balloon_candidates(u)
        assert len(out) == 1 and out[0]["item_label"] == "7"


# ---------- RQ-B1-03/04/05 — associação balão × tabela -------------------


def test_b1_validation_single_match_candidate():
    u = _u(rows=[_row(0, "50224110", item="A1", qty="1")],
           balloons=[_balloon("A1")])
    v = build_balloon_table_validation(u)
    assert v["status"] == "CANDIDATE"
    e = v["balloons"][0]
    assert e["state"] == "BALLOON_LABEL_IDENTIFIED"
    assert e["association"] == "MATCH_CANDIDATE"
    assert e["table_item"]["component_code_candidate"] == "50224110"
    assert e["leader_target_verified"] is False
    assert e["review_required"] is True
    assert v["summary"]["match_candidates"] == 1


def test_b1_validation_case_insensitive_label():
    u = _u(rows=[_row(0, "50224110", item="A1")],
           balloons=[_balloon("a1")])
    e = build_balloon_table_validation(u)["balloons"][0]
    assert e["association"] == "MATCH_CANDIDATE"


def test_b1_validation_duplicate_balloon_not_error():
    """Item 'B' com 2 balões (terminais nas 2 extremidades) — legítimo."""
    u = _u(rows=[_row(0, "10080105", item="B", qty="2")],
           balloons=[_balloon("B", 10, 10, 30, 30),
                     _balloon("B", 200, 300, 220, 320)])
    v = build_balloon_table_validation(u)
    states = [b["state"] for b in v["balloons"]]
    assert states == ["BALLOON_LABEL_IDENTIFIED",
                      "BALLOON_LABEL_IDENTIFIED"]
    ti = v["table_items"][0]
    assert ti["item_label"] == "B"
    assert ti["balloon_occurrences"] == 2
    assert ti["state"] == "TABLE_ITEM_FOUND"
    assert v["summary"]["match_candidates"] == 2
    assert v["summary"]["ambiguous"] == 0


def test_b1_validation_ambiguous_two_items_same_label():
    u = _u(rows=[_row(0, "10080105", item="A"),
                 _row(1, "10080106", item="A")],
           balloons=[_balloon("A")])
    v = build_balloon_table_validation(u)
    e = v["balloons"][0]
    assert e["state"] == "AMBIGUOUS"
    assert e["association"] == "AMBIGUOUS"
    assert len(e["table_items"]) == 2
    assert v["summary"]["ambiguous"] == 1


def test_b1_validation_balloon_not_located():
    """Balão sem item correspondente → NOT_LOCATED (não prova erro)."""
    u = _u(rows=[_row(0, "50224110", item="A1")],
           balloons=[_balloon("Z9")])
    v = build_balloon_table_validation(u)
    e = v["balloons"][0]
    assert e["state"] == "NOT_LOCATED"
    assert v["unassociated_balloon_labels"] == ["Z9"]
    assert v["summary"]["not_located"] == 1


def test_b1_validation_item_without_balloon_not_located():
    """Item sem balão identificado → NOT_LOCATED (≠ ausência física)."""
    u = _u(rows=[_row(0, "50224110", item="A1"),
                 _row(1, "10080105", item="A2")],
           balloons=[_balloon("A1")])
    v = build_balloon_table_validation(u)
    states = {t["item_label"]: t["state"] for t in v["table_items"]}
    assert states == {"A1": "TABLE_ITEM_FOUND", "A2": "NOT_LOCATED"}
    assert v["table_items_without_balloon"] == ["A2"]


def test_b1_validation_not_comparable_no_table():
    u = _u(rows=None, balloons=[_balloon("A1")])
    v = build_balloon_table_validation(u)
    assert v["balloons"][0]["state"] == "NOT_COMPARABLE"
    assert v["summary"]["not_comparable"] == 1


def test_b1_validation_empty_understanding():
    v = build_balloon_table_validation({})
    assert v["balloons_identified"] == 0
    assert v["balloons"] == [] and v["table_items"] == []


def test_b1_validation_full_family_90264311():
    """Caso 90264311: A1/A2/A3/A4 ↔ itens da tabela — família completa."""
    rows = [
        _row(0, "10300001", item="A1", desc="PROTETOR TERMICO"),
        _row(1, "10300002", item="A2", desc="LUVA"),
        _row(2, "10030102", item="A3", desc="CABO PP VM/VERM"),
        _row(3, "10080106", item="A4", desc="TERMINAL"),
    ]
    balloons = [_balloon(l, x1=i * 60) for i, l in
                enumerate(("A1", "A2", "A3", "A4"))]
    v = build_balloon_table_validation(_u(rows=rows, balloons=balloons))
    pairs = {
        (b["normalized_label"], (b.get("table_item") or {}).get(
            "item_label")) for b in v["balloons"]
    }
    assert pairs == {("A1", "A1"), ("A2", "A2"), ("A3", "A3"),
                     ("A4", "A4")}
    assert v["summary"]["match_candidates"] == 4
    assert v["leader_lines_verified"] is False


# ---------- integração — object profiles + investigação ----------------


def _build(rows=None, balloons=None, **kw):
    return build_object_profiles(
        bom_occurrences=[
            {"occurrence_id": "O1", "component_code": "10080105",
             "parent_code": "90264302", "depth": 0, "path": "O1",
             "quantity_raw": "2", "unit_raw": "PC"},
        ],
        visual_observations=[],
        understanding=_u(rows=rows, balloons=balloons),
        document_sha=SHA, official_source_ref=SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        include_investigations=True, **kw,
    )


def test_b1_profiles_balloon_objects_and_referenced_by():
    out = _build(rows=[_row(0, "10080105", item="B", qty="2")],
                 balloons=[_balloon("B"), _balloon("B", 200, 300, 220, 320)])
    assert out["objects_by_type"].get("balloon") == 2
    assert out["relations_by_type"].get("REFERENCED_BY") == 2
    gi = out["guided_investigations"]
    assert gi["balloon_candidates"][0]["item_label"] == "B"
    assert gi["balloon_table_validation"]["summary"][
        "match_candidates"] == 2


def test_b1_validation_section_in_investigations():
    out = _build(rows=[_row(0, "10080105", item="A4")],
                 balloons=[_balloon("A4"), _balloon("XX")])
    btv = out["guided_investigations"]["balloon_table_validation"]
    assert btv["schema_version"] == "balloon_table_validation.v1"
    assert btv["status"] == "CANDIDATE"
    assert btv["automatic_approval"] is False
    states = {b["normalized_label"]: b["state"] for b in btv["balloons"]}
    assert states == {"A4": "BALLOON_LABEL_IDENTIFIED",
                      "XX": "NOT_LOCATED"}


def test_b1_no_balloons_section_still_present():
    """Sem evidência → seção presente, vazia, sem fabricar balões."""
    out = _build(rows=[_row(0, "10080105", item="A1")])
    btv = out["guided_investigations"]["balloon_table_validation"]
    assert btv["balloons_identified"] == 0
    assert btv["table_items"][0]["state"] == "NOT_LOCATED"
    assert btv["summary"]["match_candidates"] == 0


def test_b1_understanding_candidates_feed_mapper():
    """Seção tipada do understanding → objetos BALLOON com evidência."""
    u = _u(rows=[_row(0, "10080105", item="A1")],
           balloons=[_balloon("A1")])
    out = _build.__wrapped__(rows=None) if False else build_object_profiles(
        bom_occurrences=[], visual_observations=[], understanding=u,
        document_sha=SHA, official_source_ref=SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        include_investigations=True,
    )
    assert out["objects_by_type"].get("balloon") == 1
    assert out["relations_by_type"].get("REFERENCED_BY") == 1


def test_b1_circled_glyph_not_balloon():
    """Glifo circulado não-ASCII (①) não é identificador de balão — caso
    real: OCR lê o item da tabela como ① e um círculo o contém."""
    tokens = [_tok("①", 605, 405, 625, 425)]
    prims = {"circles": [_circle(595, 395, 635, 435)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert u["balloon_candidates"] == []
    assert u["balloon_excluded"] == []


def test_b1_notes_region_circled_token_is_candidate():
    """Balão na faixa heurística 'notes' (topo-esquerda sobre a área
    gráfica) permanece elegível — o 'B' esquerdo real do 90261723 cai
    nessa região. Região fica registrada no candidato."""
    tokens = [_tok("B", 100, 80, 120, 100)]
    prims = {"circles": [_circle(90, 70, 130, 110)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert len(u["balloon_candidates"]) == 1
    b = u["balloon_candidates"][0]
    assert b["normalized_label"] == "B"
    assert b["region"] == "notes"


def test_b1_validation_item_label_cell_shape_fallback():
    """Tabela curta sem coluna 'item' tipada: única célula item-shaped à
    esquerda do código resolve o rótulo com fonte registrada — caso real
    90261723 (rows A/B com col_types sem 'item')."""
    row = {
        "row": 0, "page": 1,
        "fields": {"component_code": {"normalized_value": "10420256"}},
        "association_status": "FIELD_IDENTIFIED",
        "cells": [
            {"text": "ca18vdar-00786", "col": 0, "col_type": None},
            {"text": "a", "col": 1, "col_type": None},
            {"text": "10420256", "col": 3,
             "col_type": "component_code"},
            {"text": "cabo", "col": 4, "col_type": "cable"},
            {"text": "ul", "col": 10, "col_type": None},
        ],
    }
    u = {
        "balloon_candidates": [_balloon("A")],
        "component_table": {"rows": [row]},
    }
    v = build_balloon_table_validation(u)
    b = v["balloons"][0]
    assert b["state"] == "BALLOON_LABEL_IDENTIFIED"
    assert b["association"] == "MATCH_CANDIDATE"
    assert b["table_item"]["item_label"] == "a"
    assert b["table_item"]["item_label_source"] == "cell_item_shape"
    # 'ul' (col 10) é item-shaped, mas fica à direita do código → não conta


def test_b1_validation_cell_shape_ambiguous_abstains():
    """Duas células item-shaped à esquerda do código → rótulo não
    resolvido → NOT_LOCATED (abstenção, nunca chute)."""
    row = {
        "row": 0, "page": 1,
        "fields": {"component_code": {"normalized_value": "10420256"}},
        "association_status": "FIELD_IDENTIFIED",
        "cells": [
            {"text": "a1", "col": 0, "col_type": None},
            {"text": "b", "col": 1, "col_type": None},
            {"text": "10420256", "col": 3,
             "col_type": "component_code"},
        ],
    }
    u = {
        "balloon_candidates": [_balloon("B")],
        "component_table": {"rows": [row]},
    }
    v = build_balloon_table_validation(u)
    b = v["balloons"][0]
    assert b["state"] == "NOT_LOCATED"
    assert v["table_items_with_label"] == 0
