"""VAL-02 — campos do carimbo: matcher rótulo→valor, proveniência,
histórico embutido, tipagem de identificadores, identidade
documental e domínios de revisão (RQ-02-01..07).

Fixtures modeladas nas geometrias reais observadas nos PDFs
oficiais 90264135, 90264302, 90264161 e 90263554 (Doc 119 §91).
"""

from __future__ import annotations

from engineering_app.application.drawing.understanding import (
    build_document_understanding,
    build_understanding,
)


def _tok(text, x, y, w=40, h=10, conf=0.9, page=1):
    return {
        "text": text,
        "bounding_box_px": [x, y, x + w, y, x + w, y + h, x, y + h],
        "confidence": conf,
        "page": page,
    }


def _tb_like_90264302():
    """Carimbo real 90264302 p1 (topo-direito, ~2300x1680).

    Título + código grande; linha COD/DES/REV; CLIENTE; histórico
    embutido REV|DATA|LMP|OV|RESUMO|EXECUTADO|LIBERADO com 1 linha.
    """
    return [
        _tok("CHICOTE", 1300, 40, 120), _tok("DE", 1430, 40, 30),
        _tok("LIGAÇÃO", 1470, 40, 100),
        _tok("90264302", 1900, 30, 250, 50),
        _tok("COD:", 1300, 100), _tok("18702881", 1360, 100, 80),
        _tok("DES:", 1650, 100), _tok("10013396831", 1700, 100, 110),
        _tok("REV:", 1950, 100), _tok("00", 2000, 100, 25),
        _tok("CLIENTE:", 1300, 140, 70),
        _tok("WEG", 1390, 140, 50), _tok("INDUSTRIA", 1450, 140, 90),
        # histórico embutido
        _tok("REV", 1300, 190), _tok("DATA", 1360, 190),
        _tok("LMP", 1420, 190), _tok("OV", 1470, 190),
        _tok("RESUMO", 1520, 190, 70), _tok("DAS", 1600, 190, 35),
        _tok("MODIFICAÇÕES", 1640, 190, 120),
        _tok("EXECUTADO", 1800, 190, 80), _tok("LIBERADO", 1900, 190, 70),
        _tok("00", 1305, 210, 25), _tok("26/10/26", 1355, 210, 60),
        _tok("167 26", 1415, 210, 45), _tok("003086", 1465, 210, 50),
        _tok("CRIAÇÃO", 1520, 210, 60), _tok("DE", 1590, 210, 20),
        _tok("DESENHO", 1620, 210, 70),
        _tok("WILLIAM", 1800, 210, 60), _tok("GABRIELLA", 1900, 210, 70),
    ]


def _table_tokens():
    return [
        _tok("ITEM", 100, 500), _tok("QTD", 200, 500),
        _tok("COMPONENTE", 300, 500),
        _tok("1", 100, 540), _tok("2", 200, 540),
        _tok("50226113", 300, 540, 70),
        _tok("2", 100, 570), _tok("1", 200, 570),
        _tok("50226114", 300, 570, 70),
    ]


def test_admin_fields_label_right_same_row():
    out = build_understanding(
        _tb_like_90264302() + _table_tokens(), document_hash="x",
        product_code="90264302",
    )
    fields = {
        f["field_type"]: f
        for f in out["title_block"]["fields"]
    }
    assert fields["document_code"]["raw_value"] == "18702881"
    assert fields["customer_name"]["raw_value"].startswith("WEG")
    assert fields["drawing_reference"]["raw_value"] == "10013396831"
    rev = fields["revision_printed"]
    assert rev["raw_value"] == "00"
    assert rev["interpretation_state"] == "FIELD_IDENTIFIED"
    for f in fields.values():
        assert f["page"] == 1 and f["bounding_box_px"]


def test_revision_candidate_page_and_domain():
    out = build_understanding(
        _tb_like_90264302() + _table_tokens(), document_hash="x",
        product_code="90264302", page=1,
    )
    revs = [
        r for r in out["revision_candidates"]
        if r.get("value_text")
    ]
    assert revs and all(
        r["page"] == 1
        and r["revision_domain"] == "ENGINEERING_DRAWING"
        for r in revs
    )


def test_embedded_revision_history_entries():
    out = build_understanding(
        _tb_like_90264302() + _table_tokens(), document_hash="x",
        product_code="90264302",
    )
    rh = out["revision_history"]
    assert rh["candidate"] is True
    assert rh.get("embedded_in") == "title_block"
    entries = rh.get("entries") or []
    assert len(entries) >= 1
    e = entries[0]
    assert e["revision_value"] == "00"
    assert e["date"] == "26/10/26"
    assert e["lmp"] == "167 26"
    assert e["ov"] == "003086"
    assert "CRIA" in (e["summary"] or "").upper()
    assert e["executado"] == "WILLIAM"
    assert e["liberado"] == "GABRIELLA"
    assert e["page"] == 1


def test_history_codes_get_revision_history_region_not_table():
    tokens = _tb_like_90264302() + _table_tokens() + [
        _tok("ALTERAÇÃO", 1520, 240, 70),
        _tok("10080972", 1600, 240, 70),  # código dentro do resumo
        _tok("P/", 1680, 240, 20),
        _tok("10080192", 1710, 240, 70),
        _tok("01", 1305, 240, 25), _tok("29/10/25", 1355, 240, 60),
        _tok("001 25", 1415, 240, 45),
        _tok("WILLIAM", 1800, 240, 60), _tok("GABRIELLA", 1900, 240, 70),
    ]
    out = build_understanding(
        tokens, document_hash="x", product_code="90264302"
    )
    ctx = {
        (c["code"], c["page"]): c["region"]
        for c in out["code_contexts"]
    }
    assert ctx[("10080972", 1)] == "revision_history"
    assert ctx[("10080192", 1)] == "revision_history"
    codes = {
        o["component_code"]
        for o in out["component_table"]["structure_occurrences"]
    }
    assert "10080972" not in codes and "10080192" not in codes


def test_identifier_roles():
    out = build_understanding(
        _tb_like_90264302() + _table_tokens(), document_hash="x",
        product_code="90264302",
    )
    ids = {
        i["text"]: i
        for i in out["identifier_candidates"]
    }
    assert ids["90264302"]["role"] == "product_code"
    assert ids["18702881"]["role"] == "document_code"
    assert ids["10013396831"]["role"] == "drawing_code_candidate"
    assert ids["003086"]["role"] == "history_mention"
    for i in ids.values():
        assert i.get("role_basis")


def test_punctuated_and_alphanumeric_values():
    tokens = [
        _tok("COD:", 1300, 100), _tok("5101.5561", 1360, 100, 80),
        _tok("DES.:", 1650, 100), _tok("2200.3396", 1700, 100, 90),
        _tok("REV:", 1950, 100), _tok("M", 2000, 100, 20),
        _tok("DATA", 1420, 190), _tok("LMP", 1470, 190),
        _tok("MODIFICAÇÕES", 1520, 190, 120),
        _tok("01", 1305, 210, 25), _tok("19/12/25", 1355, 210, 60),
    ]
    out = build_understanding(tokens, document_hash="x")
    fields = {f["field_type"]: f for f in out["title_block"]["fields"]}
    assert fields["document_code"]["raw_value"] == "5101.5561"
    assert fields["drawing_reference"]["raw_value"] == "2200.3396"
    assert fields["revision_printed"]["raw_value"] == "M"


def test_rev_unpaired_nonstandard_value_recorded():
    """'REV: NA CAPA' — valor presente mas fora do padrão de revisão.

    Evidência preservada sem promover a revisão: TEXT_ONLY + dica
    de valor não pareado, nunca value_text='NA CAPA'."""
    tokens = [
        _tok("COD:", 1300, 100), _tok("P34", 1360, 100, 40),
        _tok("DES.:", 1600, 100), _tok("P34", 1650, 100, 40),
        _tok("REV:", 1900, 100), _tok("NA", 1950, 100, 30),
        _tok("CAPA", 1990, 100, 45),
    ]
    out = build_understanding(tokens, document_hash="x")
    revs = [
        r for r in out["revision_candidates"]
        if r["region"] == "title_block"
    ]
    assert all(r["value_text"] is None for r in revs)
    assert any(r.get("unpaired_value_text") == "NA CAPA" for r in revs)


def test_label_value_merged_in_single_token():
    """OCR de célula inteira funde rótulo+valor ('des:10013396831',
    'cliente:wegindustrias...') — geometria real de 90264302."""
    tokens = [
        _tok("cod:", 1211, 102), _tok("18702881", 1325, 104, 80),
        _tok("des:10013396831", 1605, 104, 160),
        _tok("rev:", 1880, 102), _tok("00", 1949, 104, 25),
        _tok("cliente:wegindustrias.a-linhares", 1300, 150, 320),
        # cabeçalho do histórico embutido — ancora o cluster
        _tok("rev", 1214, 218), _tok("data", 1304, 219),
        _tok("lmp", 1390, 218), _tok("ov", 1476, 220),
        _tok("resumodasmodificacöes", 1700, 219, 300),
        _tok("executado", 2106, 219, 90), _tok("liberado", 2229, 219, 70),
    ]
    out = build_understanding(tokens, document_hash="x")
    fields = {f["field_type"]: f for f in out["title_block"]["fields"]}
    dr = fields["drawing_reference"]
    assert dr["raw_value"] == "10013396831"
    assert dr["association"] == "label_value:label_embedded_same_token"
    assert dr["interpretation_state"] == "FIELD_IDENTIFIED"
    assert fields["customer_name"]["raw_value"].startswith("weg")
    assert fields["revision_printed"]["raw_value"] == "00"


def test_embedded_history_merged_summary_header():
    """RESUMO DAS MODIFICAÇÕES fundido ('resumodasmodificacöes')
    ainda habilita a detecção do histórico embutido — 90264302."""
    tokens = [
        _tok("cod:", 1211, 102), _tok("18702881", 1325, 104, 80),
        _tok("rev:", 1880, 102), _tok("00", 1949, 104, 25),
        _tok("rev", 1214, 218), _tok("data", 1304, 219),
        _tok("lmp", 1390, 218), _tok("ov", 1476, 220),
        _tok("resumodasmodificacöes", 1700, 219, 300),
        _tok("executado", 2106, 219, 90), _tok("liberado", 2229, 219, 70),
        _tok("00", 1214, 248, 25), _tok("26/10/26", 1304, 248, 60),
        _tok("16726", 1391, 249, 50), _tok("003086", 1477, 249, 55),
        _tok("criaçäodedesenho", 1600, 249, 200),
        _tok("william", 2108, 250, 70), _tok("gabriella", 2232, 248, 80),
    ]
    out = build_understanding(tokens, document_hash="x")
    rh = out["revision_history"]
    assert rh["candidate"] is True
    assert rh.get("embedded_in") == "title_block"
    e = (rh.get("entries") or [None])[0]
    assert e and e["revision_value"] == "00"
    assert e["date"] == "26/10/26"
    assert e["ov"] == "003086"
    assert (e["executado"] or "").upper() == "WILLIAM"


def test_label_without_value_is_text_only():
    tokens = [
        _tok("COD:", 1300, 100), _tok("DES.:", 1440, 100),
        _tok("12345678", 1360, 100, 70),
        # DES.: sem valor à direita nem abaixo
    ]
    out = build_understanding(tokens, document_hash="x")
    fields = {
        f["field_type"]: f for f in out["title_block"]["fields"]
    }
    assert fields["drawing_reference"]["interpretation_state"] == (
        "TEXT_ONLY"
    )
    assert fields["drawing_reference"]["raw_value"] is None


def test_document_identity_populated():
    out = build_understanding(
        _tb_like_90264302() + _table_tokens(), document_hash="abc",
        product_code="90264302",
    )
    di = out["document_identity"]
    assert di["product_code"] == "90264302"
    assert di["customer_name"]["value"].startswith("WEG")
    assert di["printed_revision"]["value"] == "00"
    assert di["printed_revision"]["domain"] == "ENGINEERING_DRAWING"
    assert di["document_code"]["value"] == "18702881"
    # campos legados do report passam a receber os valores
    assert out["customer"].startswith("WEG")
    assert out["revision"] == "00"
    assert out["document"] == "18702881"


def test_multipage_revision_conflicts_not_overwritten():
    p1 = _tb_like_90264302()
    p3 = [
        _tok("COD:", 1300, 100, page=3), _tok("18702881", 1360, 100, 80, page=3),
        _tok("DES:", 1650, 100, page=3), _tok("10013396831", 1700, 100, 110, page=3),
        _tok("REV:", 1950, 100, page=3), _tok("02", 2000, 100, 25, page=3),
        _tok("DATA", 1420, 190, page=3), _tok("LMP", 1470, 190, page=3),
    ]
    out = build_document_understanding(
        p1 + p3, document_hash="x", product_code="90264302"
    )
    di = out["document_identity"]
    assert di["printed_revision"]["value"] == "00"
    conflicts = di["printed_revision"].get("conflicts") or []
    assert any(c.get("value") == "02" and c.get("page") == 3
               for c in conflicts)
    fields = out["title_block"]["fields"]
    assert {f["page"] for f in fields} == {1, 3}
    revs = out["revision_candidates"]
    assert {r["page"] for r in revs if r.get("value_text")} == {1, 3}
