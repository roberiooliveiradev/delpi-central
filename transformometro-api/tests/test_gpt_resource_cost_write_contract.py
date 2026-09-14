from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tm_app.application.gpt_actions.record_write_contract import (
    REQUIRED_GPT_RECORD_WRITE_FIELDS,
    openapi_record_data_properties,
)
from tm_app.application.gpt_actions.openapi_builder import build_gpt_actions_openapi


def test_record_write_contract_exposes_required_fields():
    props = openapi_record_data_properties()
    missing = sorted(REQUIRED_GPT_RECORD_WRITE_FIELDS - set(props))
    assert not missing


def test_openapi_gpt_record_body_includes_valor_mensal():
    doc = build_gpt_actions_openapi()
    props = doc["components"]["schemas"]["GptRecordBody"]["properties"]["data"][
        "properties"
    ]
    assert "valor_mensal" in props
    assert "recurso_compartilhado_id" in props
    assert "nome_recurso" in props


def test_update_resource_cost_accepts_partial_valor_mensal():
    dispatch = GptActionsDispatchService()
    captured: dict = {}
    with (
        patch.object(dispatch, "_require_capability"),
        patch.object(dispatch, "_audit"),
        patch.object(dispatch, "_recalc_hook"),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.RecursoCustoRepository"
        ) as repo_cls,
    ):
        repo = repo_cls.return_value
        repo.get.return_value = {
            "recurso_custo_id": "7f17e65c-1461-487a-ad6c-8504bc05a206",
            "recurso_compartilhado_id": "rc-1",
            "valor_mensal": 5428.30,
            "data_inicio_vigencia": "2026-07-06",
            "data_fim_vigencia": None,
            "observacoes": "linha ativa",
        }

        def _update(rid, payload):
            captured["rid"] = rid
            captured["payload"] = dict(payload)
            return {"recurso_custo_id": rid, **payload}

        repo.update.side_effect = _update
        row, msg = dispatch.update_record(
            MagicMock(),
            "resource_cost",
            "7f17e65c-1461-487a-ad6c-8504bc05a206",
            {"data": {"valor_mensal": 6051.61}},
        )

    assert captured["payload"]["valor_mensal"] == 6051.61
    assert captured["payload"]["data_inicio_vigencia"] == "2026-07-06"
    assert captured["payload"]["data_fim_vigencia"] is None
    assert captured["payload"]["observacoes"] == "linha ativa"
    assert row["valor_mensal"] == 6051.61
    assert "atualizado" in msg.lower()


def test_update_shared_resource_merges_omitted_fields():
    dispatch = GptActionsDispatchService()
    captured: dict = {}
    with (
        patch.object(dispatch, "_require_capability"),
        patch.object(dispatch, "_audit"),
        patch.object(dispatch, "_recalc_hook"),
        patch.object(dispatch, "_validate_recurso"),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.RecursoRepository"
        ) as repo_cls,
    ):
        repo = repo_cls.return_value
        repo.get.return_value = {
            "recurso_compartilhado_id": "rc-1",
            "nome_recurso": "Embaixador",
            "tipo_custo": "mao_obra",
            "recorrencia": "mensal",
            "valor_total_recorrente": 0,
            "criterio_rateio": "igualitario",
            "escopo_recurso": "empresa",
            "base_competencia": "mensal_cheio",
            "status_recurso": "ativo",
            "categoria_recurso": None,
            "fornecedor": None,
            "data_inicio_vigencia": None,
            "data_fim_vigencia": None,
            "centro_custo": None,
            "observacoes": None,
            "codigo_recurso": "RC-0001",
        }

        def _update(rid, payload):
            captured["payload"] = dict(payload)
            return {"recurso_compartilhado_id": rid, **payload}

        repo.update.side_effect = _update
        dispatch.update_record(
            MagicMock(),
            "shared_resource",
            "rc-1",
            {"data": {"observacoes": "ajuste GPT"}},
        )

    assert captured["payload"]["nome_recurso"] == "Embaixador"
    assert captured["payload"]["codigo_recurso"] == "RC-0001"
    assert captured["payload"]["observacoes"] == "ajuste GPT"
