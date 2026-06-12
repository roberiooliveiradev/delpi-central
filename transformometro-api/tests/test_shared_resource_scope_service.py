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
