from __future__ import annotations

import pytest

from tm_app.application.services.dashboard_view_scope_service import (
    DashboardView,
    DashboardViewScopeService,
)
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService


def test_resolve_consolidated_by_default():
    scope = DashboardViewScopeService().resolve()
    assert scope.view == DashboardView.CONSOLIDATED
    assert scope.filial_id is None
    assert scope.setor_id is None


def test_resolve_filial_from_filial_id_param():
    scope = DashboardViewScopeService().resolve(filial_id="01")
    assert scope.view == DashboardView.FILIAL
    assert scope.filial_id == "01"
    assert scope.setor_id is None


def test_resolve_department_from_filial_and_setor():
    scope = DashboardViewScopeService().resolve(filial_id="01", setor_id="engenharia")
    assert scope.view == DashboardView.DEPARTMENT
    assert scope.filial_id == "01"
    assert scope.setor_id == "engenharia"


def test_explicit_view_consolidated_clears_filters():
    scope = DashboardViewScopeService().resolve(view="consolidated", filial_id="01")
    assert scope.view == DashboardView.CONSOLIDATED
    assert scope.filial_id is None


def test_view_filial_rejects_setor():
    with pytest.raises(ValueError, match="visão filial não aceita setor_id"):
        DashboardViewScopeService().resolve(view="filial", filial_id="01", setor_id="eng")


def test_filter_raw_preserves_empresa_resource_pool():
    raw = TransformometroRawData(
        processos=[
            {
                "processo_id": "p1",
                "filial_id": "01",
                "setor_id": "engenharia",
            },
            {
                "processo_id": "p2",
                "filial_id": "02",
                "setor_id": "producao",
            },
        ],
        revisoes=[
            {"revisao_id": "r1", "processo_id": "p1", "deletado": False},
            {"revisao_id": "r2", "processo_id": "p2", "deletado": False},
        ],
        revisao_recursos_compartilhados=[
            {
                "revisao_id": "r1",
                "recurso_compartilhado_id": "rc1",
                "deletado": False,
            },
            {
                "revisao_id": "r2",
                "recurso_compartilhado_id": "rc1",
                "deletado": False,
            },
        ],
        recursos_compartilhados=[
            {
                "recurso_compartilhado_id": "rc1",
                "escopo_recurso": "empresa",
                "deletado": False,
            }
        ],
    )
    scope = DashboardViewScopeService().resolve(filial_id="01")
    filtered = DashboardViewScopeService().filter_raw_preserving_resource_rateio(
        raw,
        scope,
        DashboardCalculatorService(),
    )
    assert len(filtered.processos) == 1
    assert filtered.processos[0]["processo_id"] == "p1"
    assert len(filtered.recursos_compartilhados) == 1
    assert len(filtered.revisao_recursos_compartilhados) == 2
