from __future__ import annotations

import pytest

from tm_app.domain.services.shared_resource_scope_service import (
    SCOPE_EMPRESA,
    SCOPE_FILIAL,
    SCOPE_SETOR,
    filter_rateio_pool,
    normalize_escopo_recurso,
)


def _inst(filial: str, setor: str, *, filial_uuid: str | None = None, setor_uuid: str | None = None):
    return {
        "filial_id": filial_uuid or filial,
        "setor_id": setor_uuid or setor,
        "codigo_filial": filial,
        "codigo_setor": setor,
    }


def test_normalize_escopo_recurso_defaults_to_empresa():
    assert normalize_escopo_recurso("") == SCOPE_EMPRESA


def test_filter_rateio_pool_empresa_keeps_all_links():
    links = [
        {"revisao_id": "r1", "recurso_compartilhado_id": "rc1"},
        {"revisao_id": "r2", "recurso_compartilhado_id": "rc1"},
    ]
    revisoes = {
        "r1": {"revisao_id": "r1", "processo_id": "p1", "instancia_id": "i1"},
        "r2": {"revisao_id": "r2", "processo_id": "p2", "instancia_id": "i2"},
    }
    instancias = {
        "i1": {**_inst("01", "eng"), "instancia_id": "i1", "processo_id": "p1"},
        "i2": {**_inst("02", "eng"), "instancia_id": "i2", "processo_id": "p2"},
    }
    result = filter_rateio_pool(
        {"escopo_recurso": SCOPE_EMPRESA},
        links,
        anchor_revisao_id="r1",
        revisoes_by_id=revisoes,
        instancias_by_id=instancias,
        processos_by_id={},
    )
    assert len(result) == 2


def test_filter_rateio_pool_filial_scopes_to_same_filial():
    links = [
        {"revisao_id": "r1", "recurso_compartilhado_id": "rc1"},
        {"revisao_id": "r2", "recurso_compartilhado_id": "rc1"},
    ]
    revisoes = {
        "r1": {"revisao_id": "r1", "processo_id": "p1", "instancia_id": "i1"},
        "r2": {"revisao_id": "r2", "processo_id": "p2", "instancia_id": "i2"},
    }
    instancias = {
        "i1": {**_inst("01", "eng"), "instancia_id": "i1", "processo_id": "p1"},
        "i2": {**_inst("02", "eng"), "instancia_id": "i2", "processo_id": "p2"},
    }
    result = filter_rateio_pool(
        {"escopo_recurso": SCOPE_FILIAL},
        links,
        anchor_revisao_id="r1",
        revisoes_by_id=revisoes,
        instancias_by_id=instancias,
        processos_by_id={},
    )
    assert [link["revisao_id"] for link in result] == ["r1"]


def test_filter_rateio_pool_setor_requires_same_filial_and_setor():
    links = [
        {"revisao_id": "r1", "recurso_compartilhado_id": "rc1"},
        {"revisao_id": "r2", "recurso_compartilhado_id": "rc1"},
        {"revisao_id": "r3", "recurso_compartilhado_id": "rc1"},
    ]
    revisoes = {
        "r1": {"revisao_id": "r1", "processo_id": "p1", "instancia_id": "i1"},
        "r2": {"revisao_id": "r2", "processo_id": "p2", "instancia_id": "i2"},
        "r3": {"revisao_id": "r3", "processo_id": "p3", "instancia_id": "i3"},
    }
    instancias = {
        "i1": {**_inst("01", "pcp"), "instancia_id": "i1", "processo_id": "p1"},
        "i2": {**_inst("01", "eng"), "instancia_id": "i2", "processo_id": "p2"},
        "i3": {**_inst("01", "pcp"), "instancia_id": "i3", "processo_id": "p3"},
    }
    result = filter_rateio_pool(
        {"escopo_recurso": SCOPE_SETOR},
        links,
        anchor_revisao_id="r1",
        revisoes_by_id=revisoes,
        instancias_by_id=instancias,
        processos_by_id={},
    )
    assert sorted(link["revisao_id"] for link in result) == ["r1", "r3"]


def test_normalize_escopo_recurso_rejects_invalid():
    with pytest.raises(ValueError, match="escopo_recurso inválido"):
        normalize_escopo_recurso("global")


def _chain(instancias: dict, revisoes: dict | None = None, processos: dict | None = None):
    if revisoes is None:
        revisoes = {
            f"r{idx}": {"revisao_id": f"r{idx}", "processo_id": f"p{idx}", "instancia_id": iid}
            for idx, iid in enumerate(instancias, start=1)
        }
    links = [{"revisao_id": rid, "recurso_compartilhado_id": "rc1"} for rid in revisoes]
    return revisoes, links, processos or {}


def _pool(escopo, links, anchor, revisoes, instancias, processos=None):
    return filter_rateio_pool(
        {"escopo_recurso": escopo},
        links,
        anchor_revisao_id=anchor,
        revisoes_by_id=revisoes,
        instancias_by_id=instancias,
        processos_by_id=processos or {},
    )


def test_s1_setor_scope_shares_same_filial_and_setor():
    instancias = {
        "i1": {**_inst("01", "pcp"), "instancia_id": "i1"},
        "i2": {**_inst("01", "pcp"), "instancia_id": "i2"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_SETOR, links, "r1", revisoes, instancias, processos)
    assert sorted(link["revisao_id"] for link in result) == ["r1", "r2"]


def test_s2_setor_scope_excludes_different_setor_same_filial():
    instancias = {
        "i1": {**_inst("01", "pcp"), "instancia_id": "i1"},
        "i2": {**_inst("01", "eng"), "instancia_id": "i2"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_SETOR, links, "r1", revisoes, instancias, processos)
    assert [link["revisao_id"] for link in result] == ["r1"]


def test_s3_setor_scope_excludes_same_setor_code_different_filial():
    instancias = {
        "i1": {**_inst("01", "pcp"), "instancia_id": "i1"},
        "i2": {**_inst("02", "pcp"), "instancia_id": "i2"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_SETOR, links, "r1", revisoes, instancias, processos)
    assert [link["revisao_id"] for link in result] == ["r1"]


def test_s4_both_missing_setor_identity_do_not_share():
    instancias = {
        "i1": {"instancia_id": "i1", "filial_id": "01", "codigo_filial": "01"},
        "i2": {"instancia_id": "i2", "filial_id": "01", "codigo_filial": "01"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_SETOR, links, "r1", revisoes, instancias, processos)
    assert result == []


def test_s5_single_missing_setor_identity_does_not_share():
    instancias = {
        "i1": {**_inst("01", "pcp"), "instancia_id": "i1"},
        "i2": {"instancia_id": "i2", "filial_id": "01", "codigo_filial": "01"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_SETOR, links, "r1", revisoes, instancias, processos)
    assert [link["revisao_id"] for link in result] == ["r1"]


def test_s6_missing_filial_identity_does_not_prove_equality():
    instancias = {
        "i1": {"instancia_id": "i1", "setor_id": "s1", "codigo_setor": "pcp"},
        "i2": {"instancia_id": "i2", "setor_id": "s2", "codigo_setor": "pcp"},
        "i3": {"instancia_id": "i3", "filial_id": "01", "codigo_filial": "01"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_FILIAL, links, "r1", revisoes, instancias, processos)
    assert result == []


def test_s6b_unidentified_link_does_not_join_identified_anchor():
    instancias = {
        "i1": {"instancia_id": "i1", "filial_id": "f1", "codigo_filial": "01"},
        "i2": {"instancia_id": "i2"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_FILIAL, links, "r1", revisoes, instancias, processos)
    assert [link["revisao_id"] for link in result] == ["r1"]


def test_s7_missing_anchor_revisao_returns_empty_pool():
    instancias = {
        "i1": {**_inst("01", "pcp"), "instancia_id": "i1"},
        "i2": {**_inst("01", "pcp"), "instancia_id": "i2"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_FILIAL, links, "r404", revisoes, instancias, processos)
    assert result == []


def test_s8_missing_instancia_falls_back_to_processo_scope():
    instancias = {
        "i2": {**_inst("01", "pcp"), "instancia_id": "i2"},
        "i3": {**_inst("02", "pcp"), "instancia_id": "i3"},
    }
    revisoes = {
        "r1": {"revisao_id": "r1", "processo_id": "p1", "instancia_id": "i404"},
        "r2": {"revisao_id": "r2", "processo_id": "p2", "instancia_id": "i2"},
        "r3": {"revisao_id": "r3", "processo_id": "p3", "instancia_id": "i3"},
    }
    links = [{"revisao_id": rid, "recurso_compartilhado_id": "rc1"} for rid in revisoes]
    processos = {
        "p1": {"processo_id": "p1", "filial_id": "01", "setor_id": "pcp"},
        "p2": {"processo_id": "p2"},
        "p3": {"processo_id": "p3"},
    }
    result = _pool(SCOPE_FILIAL, links, "r1", revisoes, instancias, processos)
    assert sorted(link["revisao_id"] for link in result) == ["r1", "r2"]


def test_s9_todas_filiais_ativas_matches_any_filial():
    instancias = {
        "i1": {
            "instancia_id": "i1",
            "todas_filiais_ativas": True,
            "setores": [{"setor_id": "s1", "codigo_setor": "pcp"}],
        },
        "i2": {**_inst("02", "pcp"), "instancia_id": "i2"},
        "i3": {**_inst("99", "pcp"), "instancia_id": "i3"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_FILIAL, links, "r1", revisoes, instancias, processos)
    assert sorted(link["revisao_id"] for link in result) == ["r1", "r2", "r3"]


def test_s10_empresa_scope_keeps_all_links():
    instancias = {
        "i1": {**_inst("01", "pcp"), "instancia_id": "i1"},
        "i2": {**_inst("02", "eng"), "instancia_id": "i2"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_EMPRESA, links, "r1", revisoes, instancias, processos)
    assert len(result) == 2


def test_s11_empty_setores_list_preserves_top_level_setor_identity():
    instancias = {
        "i1": {"instancia_id": "i1", "filial_id": "01", "codigo_filial": "01",
               "setor_id": "s1", "codigo_setor": "pcp", "setores": []},
        "i2": {"instancia_id": "i2", "filial_id": "01", "codigo_filial": "01",
               "setores": [{"setor_id": "s1", "codigo_setor": "pcp"}]},
        "i3": {"instancia_id": "i3", "filial_id": "01", "codigo_filial": "01",
               "setores": [{"setor_id": "s9", "codigo_setor": "eng"}]},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_SETOR, links, "r1", revisoes, instancias, processos)
    assert sorted(link["revisao_id"] for link in result) == ["r1", "r2"]


def test_s12_divergent_uuid_and_code_do_not_create_equivalence():
    instancias = {
        "i1": {"instancia_id": "i1", "filial_id": "f1", "codigo_filial": "01",
               "setor_id": "s1", "codigo_setor": "pcp"},
        "i2": {"instancia_id": "i2", "filial_id": "f2", "codigo_filial": "02",
               "setor_id": "s2", "codigo_setor": "pcp"},
        "i3": {"instancia_id": "i3", "codigo_filial": "01",
               "setor_id": "s3", "codigo_setor": "pcp"},
    }
    revisoes, links, processos = _chain(instancias)
    result = _pool(SCOPE_FILIAL, links, "r1", revisoes, instancias, processos)
    assert sorted(link["revisao_id"] for link in result) == ["r1", "r3"]
