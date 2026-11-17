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
    tokens = [_tok("A1", 600, 400, 630, 430)]
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
        _tok("1", 600, 400, 620, 430),
        _tok("A", 700, 500, 720, 530),
        _tok("B", 800, 300, 820, 330),
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
        _tok("B", 600, 400, 620, 430),
        _tok("B", 800, 600, 820, 630),
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
    tokens = [_tok("C", 3, 395, 26, 425)]
    prims = {"circles": [_circle(0, 388, 36, 434)]}
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
        _tok("A1", 600, 400, 630, 430, page=1),
        _tok("B", 700, 500, 720, 530, page=2),
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
    tokens = [_tok("B", 95, 75, 125, 105)]
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


def test_b1_oversized_circle_excluded():
    """Círculo grande com glifo pequeno (marcador de zona/carimbo —
    caso real '01'/'00' do 90261731 e zonas '10'/'A' do 90264311) é
    excluído: o glifo do balão preenche quase todo o círculo."""
    tokens = [
        _tok("01", 300, 1910, 350, 1947),   # carimbo circulado
        _tok("A", 30, 40, 50, 67),          # marcador de zona
        _tok("B", 605, 405, 652, 460),      # balão real
    ]
    prims = {"circles": [
        _circle(249, 1867, 365, 1983),
        _circle(10, 26, 116, 132),
        _circle(595, 395, 665, 465),
    ]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 2339), graphic_primitives=prims,
    )
    labels = [b["normalized_label"] for b in u["balloon_candidates"]]
    assert labels == ["B"]
    reasons = [e["excluded_reason"] for e in u["balloon_excluded"]]
    assert reasons.count("circle_oversized_for_label") == 2


def _enclosure(x1, y1, x2, y2):
    return {"type": "enclosure",
            "bounding_box_px": [x1, y1, x2, y2],
            "identification_method": "colored_outline_enclosure"}


def test_b1r1_colored_enclosure_candidate():
    """Interior fechado por contorno colorido (balão anotado a cor —
    caso real A1–A4 do 90264311) gera candidato com fonte registrada."""
    tokens = [_tok("A4", 732, 567, 829, 645)]
    prims = {"circles": [], "enclosures": [_enclosure(715, 505, 840, 618)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(2339, 1653), graphic_primitives=prims,
    )
    assert len(u["balloon_candidates"]) == 1
    b = u["balloon_candidates"][0]
    assert b["normalized_label"] == "A4"
    assert b["primitive_source"] == "enclosure"
    # caixa OCR excede o interior do contorno (~27px abaixo) — centro
    # + overlap ≥50% ainda qualificam a evidência real
    assert b["bounding_box_px"] == [715, 505, 840, 618]


def test_b1r1_center_containment_partial_token_overlap():
    """Token com centro dentro do círculo e overlap ≥50% — box OCR
    maior que a primitiva não derruba o candidato."""
    tokens = [_tok("A1", 605, 405, 640, 455)]
    prims = {"circles": [_circle(595, 395, 650, 445)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert [b["normalized_label"] for b in u["balloon_candidates"]] == [
        "A1"]


def test_b1r1_center_outside_no_candidate():
    """Centro do token fora da primitiva → sem candidato mesmo com
    interseção parcial de bordas."""
    tokens = [_tok("A1", 700, 400, 740, 450)]
    prims = {"circles": [_circle(600, 395, 705, 455)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert u["balloon_candidates"] == []


def test_b1r1_glyph_bowl_not_balloon():
    """Microcírculo do bowl de um glifo ('o'/'0') não é balão."""
    tokens = [_tok("o", 605, 405, 615, 420)]
    prims = {"circles": [_circle(603, 403, 617, 422)]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert u["balloon_candidates"] == []
    reasons = [e["excluded_reason"] for e in u["balloon_excluded"]]
    assert "circle_too_small_for_label" in reasons


def test_b1r1_enclosure_via_adapter_dict_shape():
    """A chave 'enclosures' do adapter real alimenta o detector."""
    tokens = [_tok("A3", 605, 405, 645, 445)]
    prims = {"enclosures": [{"bounding_box_px": [595, 395, 655, 455]}]}
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(1000, 700), graphic_primitives=prims,
    )
    assert len(u["balloon_candidates"]) == 1


# ---------- E1/VAL-01 B2 — linhas indicadoras (RQ-B2-01..05) ----------

_B2_BALLOON = (100, 100, 160, 160)


def _b2_u(h=None, v=None, rects=None, enc=None, extra_toks=None):
    """Understanding com 1 balão A1 + primitivas geométricas B2."""
    tokens = [_tok("A1", 105, 110, 155, 150)] + list(extra_toks or [])
    prims = {
        "circles": [_circle(*_B2_BALLOON)],
        "enclosures": enc or [],
        "rects": rects or [],
        "h_lines": h or [],
        "v_lines": v or [],
    }
    return build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(2000, 1400), graphic_primitives=prims,
    )


def test_b2_vertical_leader_to_single_rect_target():
    """RQ-B2-01/03: segmento anexado à borda → caminho + destino único."""
    u = _b2_u(v=[[130, 161, 130, 220]], rects=[[80, 210, 400, 240]])
    b = u["balloon_candidates"][0]
    ll = b["leader_line"]
    assert ll["state"] == "CANDIDATE"
    assert ll["endpoint_px"] == [130.0, 220.0]
    assert ll["target_state"] == "SINGLE_REGION"
    assert ll["target_region_px"] == [80, 210, 400, 240]
    assert b["target_region"] == "uleadtgt:0"
    assert u["geometry_regions"][0]["box_px"] == [80, 210, 400, 240]
    assert u["geometry_regions"][0]["type"] == "leader_target"


def test_b2_parallel_strokes_merge_into_one_leader():
    """Traço de 2–3 px emite runs paralelos — fundem num único líder."""
    u = _b2_u(
        v=[[130, 162, 130, 220], [131, 162, 131, 220],
           [132, 170, 132, 200]],
        rects=[[80, 210, 400, 240]],
    )
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["state"] == "CANDIDATE"
    assert ll["target_state"] == "SINGLE_REGION"


def test_b2_no_attached_segment_not_found():
    """Balão sem segmento anexado → NOT_FOUND, sem linha inventada."""
    u = _b2_u(v=[[500, 600, 500, 700]])
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["state"] == "NOT_FOUND"
    assert ll["endpoint_px"] is None


def test_b2_contour_stroke_not_leader():
    """Traço do próprio anel (duas pontas dentro) não é líder."""
    u = _b2_u(v=[[140, 110, 140, 150]])
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["state"] == "NOT_FOUND"


def test_b2_two_attached_leaders_ambiguous():
    """Dois líderes anexados → AMBIGUOUS, caminho não escolhido."""
    u = _b2_u(v=[[130, 161, 130, 220], [130, 40, 130, 99]])
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["state"] == "AMBIGUOUS"
    assert len(ll["segments_px"]) == 2
    assert ll["endpoint_px"] is None


def test_b2_bent_leader_chained_by_endpoint():
    """RQ-B2-02: dobra encadeada por proximidade de ponta."""
    u = _b2_u(
        v=[[130, 161, 130, 220]],
        h=[[130, 220, 250, 220]],
        rects=[[240, 210, 300, 230]],
    )
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["state"] == "CANDIDATE"
    assert len(ll["segments_px"]) == 2
    assert ll["endpoint_px"] == [250.0, 220.0]
    assert ll["target_state"] == "SINGLE_REGION"


def test_b2_crossing_line_does_not_connect():
    """Cruzamento no meio do traço não conecta segmentos."""
    u = _b2_u(
        v=[[130, 161, 130, 220]],
        h=[[60, 180, 200, 180]],  # cruza o líder em y=180, sem junção
    )
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["state"] == "CANDIDATE"
    assert len(ll["segments_px"]) == 1
    assert ll["endpoint_px"] == [130.0, 220.0]
    assert ll["target_state"] == "NOT_IDENTIFIED"


def test_b2_disconnected_line_not_leader():
    """Linha próxima sem ponta na fronteira não é líder."""
    u = _b2_u(v=[[130, 190, 130, 260]])  # começa 30px abaixo do anel
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["state"] == "NOT_FOUND"


def test_b2_leader_to_empty_space_target_not_identified():
    """Extremidade sem região → endpoint registrado, destino nulo."""
    u = _b2_u(v=[[130, 161, 130, 900]])
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["state"] == "CANDIDATE"
    assert ll["endpoint_px"] == [130.0, 900.0]
    assert ll["target_state"] == "NOT_IDENTIFIED"
    assert "target_region" not in u["balloon_candidates"][0]


def test_b2_page_frame_not_target():
    """Moldura da folha (>60% da página) nunca é destino."""
    u = _b2_u(
        v=[[130, 161, 130, 900]],
        rects=[[10, 10, 1990, 1390]],
    )
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["target_state"] == "NOT_IDENTIFIED"


def test_b2_multiple_target_regions_ambiguous():
    """Duas regiões na extremidade → alternativas, sem vínculo."""
    u = _b2_u(
        v=[[130, 161, 130, 220]],
        rects=[[80, 215, 400, 240], [90, 190, 140, 235]],
    )
    b = u["balloon_candidates"][0]
    ll = b["leader_line"]
    assert ll["target_state"] == "AMBIGUOUS_REGIONS"
    assert len(ll["alternative_target_regions_px"]) == 2
    assert "target_region" not in b


def test_b2_dimension_line_not_leader():
    """Linha de cota cruzando a caixa de um token de cota não é líder."""
    # balão [100,100,160,160]; cota '10±1' logo abaixo com seta
    # horizontal que tocaria a borda — deve ser rejeitada.
    u = _b2_u(
        h=[[105, 165, 175, 165]],
        extra_toks=[_tok("10±1", 118, 162, 170, 185)],
    )
    ll = u["balloon_candidates"][0]["leader_line"]
    assert ll["state"] == "NOT_FOUND"


def test_b2_repeated_label_distinct_targets():
    """RQ-B2-05: A3×2 — cada ocorrência segue seu próprio caminho."""
    tokens = [
        _tok("A3", 105, 110, 155, 150),
        _tok("A3", 605, 110, 655, 150),
    ]
    prims = {
        "circles": [_circle(100, 100, 160, 160),
                    _circle(600, 100, 660, 160)],
        "enclosures": [], "rects": [[80, 215, 400, 240],
                                    [580, 215, 900, 240]],
        "h_lines": [],
        "v_lines": [[130, 161, 130, 220], [630, 161, 630, 220]],
    }
    u = build_understanding(
        tokens, document_hash=SHA, page=1,
        render_size_px=(2000, 1400), graphic_primitives=prims,
    )
    assert len(u["balloon_candidates"]) == 2
    r1, r2 = (b["leader_line"]["target_region_px"]
              for b in u["balloon_candidates"])
    assert r1 == [80, 215, 400, 240]
    assert r2 == [580, 215, 900, 240]
    assert len(u["geometry_regions"]) == 2


def test_b2_points_to_per_occurrence_not_by_label():
    """Mapper: POINTS_TO por ocorrência — labels iguais não misturam
    alvos (correção do casamento por item_label)."""
    u = _u(balloons=[
        {**_balloon("A3", 100, 100, 160, 160),
         "target_region": "uleadtgt:0"},
        {**_balloon("A3", 600, 100, 660, 160),
         "target_region": "uleadtgt:1"},
    ])
    u["geometry_regions"] = [
        {"id": "uleadtgt:0", "type": "leader_target",
         "box_px": [80, 215, 400, 240], "page": 1},
        {"id": "uleadtgt:1", "type": "leader_target",
         "box_px": [580, 215, 900, 240], "page": 1},
    ]
    out = build_object_profiles(
        bom_occurrences=[], visual_observations=[], understanding=u,
        document_sha=SHA, official_source_ref=SRC,
        official_source_state="AVAILABLE", product_code="90264302",
        include_investigations=True,
    )
    pts = [
        r for r in out["relations"]
        if r["relation_type"] == "POINTS_TO"
    ]
    targets = sorted(r["target_object_id"] for r in pts)
    assert len(pts) == 2
    assert len(set(targets)) == 2
    assert all(
        r["verification_state"] == "NOT_CHECKED" for r in pts
    )


def test_b2_leader_line_echoed_in_validation():
    """Investigation: leader_line presente por balão; verificado=F."""
    u = _b2_u(v=[[130, 161, 130, 220]], rects=[[80, 210, 400, 240]])
    v = build_balloon_table_validation(u)
    ll = v["balloons"][0]["leader_line"]
    assert ll["state"] == "CANDIDATE"
    assert v["balloons"][0]["leader_target_verified"] is False
    assert v["leader_lines_verified"] is False
