"""Regressions: open vigencia (data_fim_vigencia) for GPT Actions / packages.

Live incident PROC-0025 / revision 2.1.0 received CURRENT_DATE as end date
even though the validated package omitted data_fim_vigencia.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tm_app.application.gpt_actions.improvement_package_service import (
    GuidedImprovementPackageService,
)
from tm_app.application.gpt_actions.openapi_builder import build_gpt_actions_openapi
from tm_app.infrastructure.persistence.repositories.revision_repository import (
    RevisaoRepository,
)


class _FakeConnection:
    def commit(self) -> None:
        return None


def _inactive_scenario_row(**overrides):
    row = {
        "revisao_id": "rev-new",
        "processo_id": "proc-1",
        "instancia_id": "inst-1",
        "cenario_tipo": "melhoria",
        "revisao_ativa": False,
        "data_inicio_vigencia": "2026-09-14",
        "data_implantacao": "2026-09-14",
        "data_fim_vigencia": None,
        "versao_revisao": "2.1.0",
        "revisao_referencia_id": "rev-base",
    }
    row.update(overrides)
    return row


def test_lifecycle_inactive_revision_does_not_invent_current_date_end():
    """Root cause of PROC-0025: inactive + NULL fim must stay NULL."""
    repo = RevisaoRepository(connection=_FakeConnection())  # type: ignore[arg-type]
    executed: list[str] = []

    def _execute(sql, params=None, auto_commit=True):
        executed.append(" ".join(str(sql).split()))
        return None

    repo.execute = _execute  # type: ignore[method-assign]
    repo.get = lambda _rid: _inactive_scenario_row()  # type: ignore[method-assign]

    out = repo._apply_revision_lifecycle(_inactive_scenario_row(), auto_commit=False)
    assert out.get("data_fim_vigencia") is None
    assert not any("CURRENT_DATE" in sql for sql in executed)
    assert not any("COALESCE(data_fim_vigencia" in sql for sql in executed)


def test_lifecycle_explicit_end_date_keeps_inactive():
    repo = RevisaoRepository(connection=_FakeConnection())  # type: ignore[arg-type]
    executed: list[str] = []

    def _execute(sql, params=None, auto_commit=True):
        executed.append(" ".join(str(sql).split()))
        return None

    repo.execute = _execute  # type: ignore[method-assign]
    repo.get = lambda _rid: _inactive_scenario_row(data_fim_vigencia="2026-12-31")  # type: ignore[method-assign]

    repo._apply_revision_lifecycle(
        _inactive_scenario_row(data_fim_vigencia="2026-12-31"),
        auto_commit=False,
    )
    assert any("revisao_ativa = FALSE" in sql for sql in executed)
    assert not any("CURRENT_DATE" in sql for sql in executed)


def test_create_record_omitted_fim_passes_null_to_repository():
    dispatch = GptActionsDispatchService()
    captured: dict = {}

    with patch(
        "tm_app.application.gpt_actions.dispatch_service.RevisaoRepository"
    ) as repo_cls, patch(
        "tm_app.application.gpt_actions.dispatch_service.MedicaoRepository"
    ), patch.object(dispatch, "_audit"), patch.object(
        dispatch._recalc_hook, "after_revisao"
    ):
        repo = repo_cls.return_value

        def _create(payload):
            captured["payload"] = dict(payload)
            return {**payload, "revisao_id": "r1"}

        repo.create.side_effect = _create
        request = MagicMock()
        dispatch.create_record(
            request,
            "revision",
            {
                "data": {
                    "processo_id": "p1",
                    "instancia_id": "i1",
                    "versao_revisao": "2.1.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-09-14",
                    "revisao_referencia_id": "b1",
                    "beneficio_calculo_categoria": "automatico",
                    # data_fim_vigencia intentionally omitted
                }
            },
        )
    assert "data_fim_vigencia" in captured["payload"]
    assert captured["payload"]["data_fim_vigencia"] is None


def test_create_record_explicit_null_fim_passes_null():
    dispatch = GptActionsDispatchService()
    captured: dict = {}

    with patch(
        "tm_app.application.gpt_actions.dispatch_service.RevisaoRepository"
    ) as repo_cls, patch(
        "tm_app.application.gpt_actions.dispatch_service.MedicaoRepository"
    ), patch.object(dispatch, "_audit"), patch.object(
        dispatch._recalc_hook, "after_revisao"
    ):
        repo = repo_cls.return_value

        def _create(payload):
            captured["payload"] = dict(payload)
            return {**payload, "revisao_id": "r1"}

        repo.create.side_effect = _create
        dispatch.create_record(
            MagicMock(),
            "revision",
            {
                "data": {
                    "processo_id": "p1",
                    "instancia_id": "i1",
                    "versao_revisao": "2.0.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-09-02",
                    "data_implantacao": "2026-09-02",
                    "revisao_referencia_id": "658d40a0-7b8d-43c6-ba9a-fd3cfe1d58c6",
                    "beneficio_calculo_categoria": "automatico",
                    "data_fim_vigencia": None,
                }
            },
        )
    assert captured["payload"]["data_fim_vigencia"] is None


def test_create_record_explicit_date_fim_persists():
    dispatch = GptActionsDispatchService()
    captured: dict = {}

    with patch(
        "tm_app.application.gpt_actions.dispatch_service.RevisaoRepository"
    ) as repo_cls, patch.object(dispatch, "_audit"), patch.object(
        dispatch._recalc_hook, "after_revisao"
    ):
        repo = repo_cls.return_value

        def _create(payload):
            captured["payload"] = dict(payload)
            return {**payload, "revisao_id": "r1"}

        repo.create.side_effect = _create
        dispatch.create_record(
            MagicMock(),
            "revision",
            {
                "data": {
                    "processo_id": "p1",
                    "instancia_id": "i1",
                    "versao_revisao": "2.2.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-01-01",
                    "revisao_referencia_id": "b1",
                    "data_fim_vigencia": "2026-12-31",
                }
            },
        )
    assert captured["payload"]["data_fim_vigencia"] == "2026-12-31"


def test_update_omitted_fim_keeps_existing():
    dispatch = GptActionsDispatchService()
    existing = {
        "revisao_id": "r1",
        "processo_id": "p1",
        "instancia_id": "i1",
        "versao_revisao": "2.1.0",
        "cenario_tipo": "melhoria",
        "data_inicio_vigencia": "2026-09-14",
        "data_fim_vigencia": "2026-09-14",
        "revisao_ativa": False,
        "revisao_referencia_id": "b1",
        "beneficio_calculo_categoria": "automatico",
    }
    captured: dict = {}

    with patch(
        "tm_app.application.gpt_actions.dispatch_service.RevisaoRepository"
    ) as repo_cls, patch(
        "tm_app.application.gpt_actions.dispatch_service.MedicaoRepository"
    ) as med_cls, patch.object(dispatch, "_audit"), patch.object(
        dispatch._recalc_hook, "after_revisao"
    ):
        repo = repo_cls.return_value
        repo.get.return_value = existing
        med_cls.return_value.get_by_revisao.return_value = None

        def _update(_rid, payload):
            captured["payload"] = dict(payload)
            return {**existing, **payload}

        repo.update.side_effect = _update
        dispatch.update_record(
            MagicMock(),
            "revision",
            "r1",
            {
                "data": {
                    "motivo_revisao": "ajuste textual",
                    # data_fim_vigencia omitted → keep 2026-09-14
                }
            },
        )
    assert captured["payload"]["data_fim_vigencia"] == "2026-09-14"
    assert captured["payload"]["motivo_revisao"] == "ajuste textual"


def test_update_explicit_null_clears_fim():
    dispatch = GptActionsDispatchService()
    existing = {
        "revisao_id": "r1",
        "processo_id": "p1",
        "instancia_id": "i1",
        "versao_revisao": "2.1.0",
        "cenario_tipo": "melhoria",
        "data_inicio_vigencia": "2026-09-14",
        "data_fim_vigencia": "2026-09-14",
        "revisao_ativa": False,
        "revisao_referencia_id": "b1",
        "beneficio_calculo_categoria": "automatico",
        "descricao_revisao": "keep",
        "motivo_revisao": "keep",
        "observacoes": "keep",
    }
    captured: dict = {}

    with patch(
        "tm_app.application.gpt_actions.dispatch_service.RevisaoRepository"
    ) as repo_cls, patch(
        "tm_app.application.gpt_actions.dispatch_service.MedicaoRepository"
    ) as med_cls, patch.object(dispatch, "_audit"), patch.object(
        dispatch._recalc_hook, "after_revisao"
    ):
        repo = repo_cls.return_value
        repo.get.return_value = existing
        med_cls.return_value.get_by_revisao.return_value = None

        def _update(_rid, payload):
            captured["payload"] = dict(payload)
            return {**existing, **payload, "data_fim_vigencia": payload.get("data_fim_vigencia")}

        repo.update.side_effect = _update
        dispatch.update_record(
            MagicMock(),
            "revision",
            "r1",
            {"data": {"data_fim_vigencia": None}},
        )
    assert captured["payload"]["data_fim_vigencia"] is None
    assert captured["payload"]["versao_revisao"] == "2.1.0"
    assert captured["payload"]["descricao_revisao"] == "keep"


def test_update_new_date_replaces_fim():
    dispatch = GptActionsDispatchService()
    existing = {
        "revisao_id": "r1",
        "processo_id": "p1",
        "instancia_id": "i1",
        "versao_revisao": "2.1.0",
        "cenario_tipo": "melhoria",
        "data_inicio_vigencia": "2026-09-14",
        "data_fim_vigencia": "2026-09-14",
        "revisao_ativa": False,
        "revisao_referencia_id": "b1",
        "beneficio_calculo_categoria": "automatico",
    }
    captured: dict = {}

    with patch(
        "tm_app.application.gpt_actions.dispatch_service.RevisaoRepository"
    ) as repo_cls, patch(
        "tm_app.application.gpt_actions.dispatch_service.MedicaoRepository"
    ) as med_cls, patch.object(dispatch, "_audit"), patch.object(
        dispatch._recalc_hook, "after_revisao"
    ):
        repo = repo_cls.return_value
        repo.get.return_value = existing
        med_cls.return_value.get_by_revisao.return_value = None

        def _update(_rid, payload):
            captured["payload"] = dict(payload)
            return {**existing, **payload}

        repo.update.side_effect = _update
        dispatch.update_record(
            MagicMock(),
            "revision",
            "r1",
            {"data": {"data_fim_vigencia": "2026-12-31"}},
        )
    assert captured["payload"]["data_fim_vigencia"] == "2026-12-31"


def test_validate_omitted_fim_ready_when_rest_ok():
    result = GuidedImprovementPackageService(MagicMock()).validate(
        MagicMock(),
        {
            "process": {"processo_id": "6e50eaa9-fe70-47a0-b91a-ec707cf05f59"},
            "instance": {"instancia_id": "59f3c049-a8b6-4fe2-87d7-3c7b40a06434"},
            "scenario": {
                "revision": {
                    "revisao_referencia_id": "8e51468d-44e0-4c13-b7f3-e12a76d55f83",
                    "versao_revisao": "2.1.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-09-14",
                    # no data_fim_vigencia
                },
                "measurement": {
                    "volume_mensal": 100,
                    "tempo_medio_execucao_min": 20,
                },
                "investments": [],
            },
        },
    )
    assert result["ready"] is True
    assert result["missing"] == []


def test_validate_explicit_null_fim_ready():
    result = GuidedImprovementPackageService(MagicMock()).validate(
        MagicMock(),
        {
            "process": {"processo_id": "p1"},
            "instance": {"instancia_id": "i1"},
            "scenario": {
                "revision": {
                    "revisao_referencia_id": "b1",
                    "versao_revisao": "2.1.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-09-14",
                    "data_fim_vigencia": None,
                },
                "measurement": {
                    "volume_mensal": 10,
                    "tempo_medio_execucao_min": 5,
                },
                "investments": [],
            },
        },
    )
    assert result["ready"] is True


def test_validate_never_writes_with_null_fim():
    dispatch = MagicMock()
    GuidedImprovementPackageService(dispatch).validate(
        MagicMock(),
        {
            "process": {"processo_id": "p1"},
            "instance": {"instancia_id": "i1"},
            "scenario": {
                "revision": {
                    "revisao_referencia_id": "b1",
                    "versao_revisao": "2.1.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-09-14",
                    "data_fim_vigencia": None,
                },
                "measurement": {
                    "volume_mensal": 10,
                    "tempo_medio_execucao_min": 5,
                },
                "investments": [],
            },
        },
    )
    dispatch.create_record.assert_not_called()
    dispatch.update_record.assert_not_called()


def test_commit_proc0025_like_does_not_invent_fim():
    """Synthetic twin of live PROC-0025 package (no real write)."""
    dispatch = MagicMock()
    dispatch.get_record.side_effect = lambda _req, entity, rid: {
        "process": {"processo_id": rid, "nome_processo": "x", "status_processo": "ativo"},
        "instance": {"instancia_id": rid, "status_instancia": "ativo"},
        "revision": {
            "revisao_id": rid,
            "processo_id": "6e50eaa9-fe70-47a0-b91a-ec707cf05f59",
            "instancia_id": "59f3c049-a8b6-4fe2-87d7-3c7b40a06434",
            "versao_revisao": "2.0.0",
            "cenario_tipo": "baseline",
        },
    }[entity]
    created_payloads: list[dict] = []

    def _create(_req, entity, body):
        payload = body.get("data") or {}
        if entity == "revision":
            created_payloads.append(dict(payload))
            return {"revisao_id": "c3123469-synthetic"}, "ok", 201
        if entity == "measurement":
            return {"medicao_id": "m1"}, "ok", 200
        raise AssertionError(entity)

    dispatch.create_record.side_effect = _create
    result = GuidedImprovementPackageService(dispatch).commit(
        MagicMock(),
        {
            "dry_run": False,
            "process": {"id": "6e50eaa9-fe70-47a0-b91a-ec707cf05f59"},
            "instance": {"id": "59f3c049-a8b6-4fe2-87d7-3c7b40a06434"},
            "scenario": {
                "revision": {
                    "revisao_referencia_id": "8e51468d-44e0-4c13-b7f3-e12a76d55f83",
                    "versao_revisao": "2.1.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-09-14",
                    "motivo_revisao": "teste",
                },
                "measurement": {
                    "volume_mensal": 100,
                    "tempo_medio_execucao_min": 20,
                },
                "investments": [],
            },
        },
    )
    assert result["ids"]["scenario_revisao_id"] == "c3123469-synthetic"
    assert created_payloads
    assert "data_fim_vigencia" not in created_payloads[0] or created_payloads[0].get(
        "data_fim_vigencia"
    ) is None


def test_commit_proc0008_like_does_not_invent_fim():
    dispatch = MagicMock()
    created_payloads: list[dict] = []

    def _create(_req, entity, body):
        payload = body.get("data") or {}
        if entity == "process":
            return {"processo_id": "801f161a-71e6-4591-865c-eff294525420"}, "ok", 201
        if entity == "instance":
            return {"instancia_id": "i-new"}, "ok", 201
        if entity == "revision":
            created_payloads.append(dict(payload))
            return {"revisao_id": "r-new"}, "ok", 201
        if entity == "measurement":
            return {"medicao_id": "m1"}, "ok", 200
        raise AssertionError(entity)

    dispatch.create_record.side_effect = _create
    dispatch.get_record.side_effect = lambda _req, entity, rid: {
        "process": {
            "processo_id": "801f161a-71e6-4591-865c-eff294525420",
            "nome_processo": "Acompanhamentos",
            "status_processo": "ativo",
        },
        "revision": {
            "revisao_id": rid,
            "cenario_tipo": "baseline",
            "versao_revisao": "1.0.0",
        },
    }[entity]

    GuidedImprovementPackageService(dispatch).commit(
        MagicMock(),
        {
            "dry_run": False,
            "process": {"id": "801f161a-71e6-4591-865c-eff294525420"},
            "instance": {
                "todas_filiais_ativas": True,
                "setor_ids": ["293ebdef-16f5-4691-bac0-627f8e55c7bf"],
                "resumo_melhoria": "Nova melhoria",
            },
            "scenario": {
                "revision": {
                    "revisao_referencia_id": "658d40a0-7b8d-43c6-ba9a-fd3cfe1d58c6",
                    "versao_revisao": "2.0.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-09-02",
                    "data_implantacao": "2026-09-02",
                },
                "measurement": {
                    "volume_mensal": 50,
                    "tempo_medio_execucao_min": 15,
                },
                "investments": [],
            },
        },
    )
    assert created_payloads
    assert created_payloads[0].get("data_fim_vigencia") is None
    assert created_payloads[0]["versao_revisao"] == "2.0.0"


def test_package_update_explicit_null_clears_fim_via_dispatch():
    dispatch = MagicMock()
    dispatch.get_record.side_effect = lambda _req, entity, rid: {
        "process": {"processo_id": rid},
        "instance": {"instancia_id": rid},
        "revision": {
            "revisao_id": rid,
            "processo_id": "p1",
            "instancia_id": "i1",
            "versao_revisao": "2.1.0",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-09-14",
            "data_fim_vigencia": "2026-09-14",
            "revisao_referencia_id": "b1",
            "beneficio_calculo_categoria": "automatico",
        },
    }[entity]

    GuidedImprovementPackageService(dispatch)._resolve_revision_block(
        MagicMock(),
        processo_id="p1",
        instancia_id="i1",
        block={
            "revision": {
                "id": "c3123469-e681-44af-b857-b54a4422895f",
                "data_fim_vigencia": None,
            }
        },
        force_cenario=None,
        allow_reference=True,
    )
    args = dispatch.update_record.call_args
    assert args[0][1] == "revision"
    assert args[0][3]["data"]["data_fim_vigencia"] is None
    assert args[0][3]["data"]["versao_revisao"] == "2.1.0"


def test_openapi_data_fim_vigencia_nullable():
    doc = build_gpt_actions_openapi()
    rev = doc["components"]["schemas"]["GptPackageRevision"]["properties"][
        "data_fim_vigencia"
    ]
    assert rev["type"] == ["string", "null"] or (
        rev.get("nullable") is True and rev.get("type") == "string"
    )
    record_data = doc["components"]["schemas"]["GptRecordBody"]["properties"]["data"][
        "properties"
    ]["data_fim_vigencia"]
    assert "null" in str(record_data.get("type"))
    examples = doc["paths"]["/transformometro/gpt-actions/v1/records/{entity}"]["post"][
        "requestBody"
    ]["content"]["application/json"]["examples"]
    assert "revision_clear_end_date" in examples
    assert examples["revision_clear_end_date"]["value"]["data"]["data_fim_vigencia"] is None


def test_package_hints_document_omit_vs_null():
    from tm_app.application.gpt_actions.improvement_package_contract import (
        build_package_hints,
    )

    rules = build_package_hints()["nesting_rules"]
    assert any("omitted" in r and "null" in r for r in rules)
