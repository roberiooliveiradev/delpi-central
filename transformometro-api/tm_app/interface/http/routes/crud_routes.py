from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request

from tm_app.core.auth_actor import actor_from_request
from tm_app.core.errors import format_api_error

from tm_app.core.catalogs import (
    CENARIO_TIPO,
    CATEGORIAS,
    CRITERIO_RATEIO,
    RECORRENCIAS,
    SETORES,
    STATUS_PROCESSO,
    STATUS_RECURSO,
    TIPO_CUSTO_RECURSO,
    TIPO_INVESTIMENTO,
    assert_in,
    options_payload,
)
from tm_app.core.responses import fail, ok
from tm_app.core.serialize import row_to_json, rows_to_json
from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository
from tm_app.infrastructure.persistence.repositories.investimento_repository import (
    InvestimentoRepository,
)
from tm_app.infrastructure.persistence.repositories.medicao_repository import MedicaoRepository
from tm_app.infrastructure.persistence.repositories.processo_repository import ProcessoRepository
from tm_app.infrastructure.persistence.repositories.recurso_repository import (
    RecursoRepository,
    VinculoRepository,
)
from tm_app.application.services.process_revision_compare_service import (
    ProcessRevisionCompareService,
)
from tm_app.application.services.revisao_rateio_diagnostic_service import (
    RevisaoRateioDiagnosticService,
)
from tm_app.application.services.revisao_workflow_notification_service import (
    RevisaoWorkflowNotificationService,
)
from tm_app.application.services.revisao_workflow_service import (
    RevisaoWorkflowError,
    RevisaoWorkflowService,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository
from tm_app.interface.http.schemas.crud_schemas import (
    InvestimentoBody,
    MedicaoBody,
    ProcessoCreateBody,
    ProcessoUpdateBody,
    RecursoBody,
    RevisaoBody,
    RevisaoRejeitarBody,
    VinculoBody,
    VinculoUpdateBody,
)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro CRUD"])
logger = logging.getLogger(__name__)


def _audit(request: Request, entity_type: str, entity_id: str, action: str, payload: dict):
    user_id, user_email = actor_from_request(request)
    try:
        AuditRepository().log(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            user_email=user_email,
            payload=payload,
        )
    except Exception as exc:
        logger.warning(
            "audit_log_failed entity=%s id=%s action=%s err=%s",
            entity_type,
            entity_id,
            action,
            format_api_error(exc),
        )


def _validate_processo_body(body: ProcessoCreateBody):
    assert_in(body.filial_id, ("01", "02"), "filial_id")
    assert_in(body.setor_id, SETORES, "setor_id")
    assert_in(body.status_processo, STATUS_PROCESSO, "status_processo")


# --- Processos ---


@router.get("/processos")
def list_processos(
    filial_id: str | None = None,
    setor_id: str | None = None,
    status: str | None = None,
    familia_processo: str | None = None,
    q: str | None = None,
):
    rows = ProcessoRepository().list(
        filial_id=filial_id,
        setor_id=setor_id,
        status_processo=status,
        familia_processo=familia_processo,
        q=q,
    )
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.get("/processos/{processo_id}")
def get_processo(processo_id: str):
    row = ProcessoRepository().get(processo_id)
    if not row:
        return fail("Processo não encontrado.", 404)
    return ok(row_to_json(row))


@router.post("/processos")
def create_processo(body: ProcessoCreateBody, request: Request):
    try:
        _validate_processo_body(body)
        row = ProcessoRepository().create(body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("create_processo_failed")
        return fail(format_api_error(exc), 500)

    pid = str(row["processo_id"])
    _audit(request, "processo", pid, "create", body.model_dump())
    return ok(row_to_json(row), "Processo criado.", 201)


@router.put("/processos/{processo_id}")
def update_processo(processo_id: str, body: ProcessoUpdateBody, request: Request):
    try:
        _validate_processo_body(body)
        row = ProcessoRepository().update(processo_id, body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)

    if not row:
        return fail("Processo não encontrado.", 404)

    _audit(request, "processo", processo_id, "update", body.model_dump())
    return ok(row_to_json(row), "Processo atualizado.")


@router.delete("/processos/{processo_id}")
def delete_processo(processo_id: str, request: Request):
    if not ProcessoRepository().soft_delete(processo_id):
        return fail("Processo não encontrado.", 404)
    _audit(request, "processo", processo_id, "delete", {})
    return ok(message="Processo excluído.")


# --- Revisões ---


@router.get("/processos/{processo_id}/comparativo")
def processo_comparativo_revisoes(processo_id: str):
    data = ProcessRevisionCompareService().compare(processo_id)
    if not data:
        return fail("Processo não encontrado.", 404)
    return ok(data, "Comparativo de revisões.")


@router.get("/processos/{processo_id}/revisoes")
def list_revisoes(processo_id: str):
    rows = RevisaoRepository().list_by_processo(processo_id)
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.post("/revisoes")
def create_revisao(body: RevisaoBody, request: Request):
    try:
        assert_in(body.cenario_tipo, CENARIO_TIPO, "cenario_tipo")
        row = RevisaoRepository().create(body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        return fail(str(exc), 500)

    rid = str(row["revisao_id"])
    _audit(request, "revisao", rid, "create", body.model_dump())
    return ok(row_to_json(row), "Revisão criada.", 201)


@router.put("/revisoes/{revisao_id}")
def update_revisao(revisao_id: str, body: RevisaoBody, request: Request):
    try:
        assert_in(body.cenario_tipo, CENARIO_TIPO, "cenario_tipo")
        row = RevisaoRepository().update(revisao_id, body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)

    if not row:
        return fail("Revisão não encontrada.", 404)

    _audit(request, "revisao", revisao_id, "update", body.model_dump())
    return ok(row_to_json(row), "Revisão atualizada.")


@router.post("/revisoes/{revisao_id}/workflow/submeter")
def submeter_revisao_aprovacao(revisao_id: str, request: Request):
    _, actor_email = actor_from_request(request)
    try:
        row = RevisaoWorkflowService().submeter(revisao_id)
    except RevisaoWorkflowError as exc:
        return fail(str(exc), 400)
    _audit(request, "revisao", revisao_id, "workflow_submeter", {})
    try:
        RevisaoWorkflowNotificationService().notify_submitted(row, actor_email=actor_email)
    except Exception as exc:
        logger.warning("workflow_notify_submitted_failed revisao=%s err=%s", revisao_id, exc)
    return ok(row_to_json(row), "Revisão enviada para análise.")


@router.post("/revisoes/{revisao_id}/workflow/aprovar")
def aprovar_revisao(revisao_id: str, request: Request):
    _, email = actor_from_request(request)
    try:
        row = RevisaoWorkflowService().aprovar(revisao_id, email)
    except RevisaoWorkflowError as exc:
        return fail(str(exc), 400)
    _audit(request, "revisao", revisao_id, "workflow_aprovar", {"email": email})
    try:
        RevisaoWorkflowNotificationService().notify_decision(
            row, decision="aprovada", actor_email=email
        )
    except Exception as exc:
        logger.warning("workflow_notify_aprovar_failed revisao=%s err=%s", revisao_id, exc)
    return ok(row_to_json(row), "Revisão aprovada.")


@router.post("/revisoes/{revisao_id}/workflow/rejeitar")
def rejeitar_revisao(revisao_id: str, body: RevisaoRejeitarBody, request: Request):
    _, email = actor_from_request(request)
    try:
        row = RevisaoWorkflowService().rejeitar(revisao_id, body.motivo, email)
    except RevisaoWorkflowError as exc:
        return fail(str(exc), 400)
    _audit(request, "revisao", revisao_id, "workflow_rejeitar", {"email": email, "motivo": body.motivo})
    try:
        RevisaoWorkflowNotificationService().notify_decision(
            row,
            decision="rejeitada",
            actor_email=email,
            motivo=body.motivo,
        )
    except Exception as exc:
        logger.warning("workflow_notify_rejeitar_failed revisao=%s err=%s", revisao_id, exc)
    return ok(row_to_json(row), "Revisão rejeitada.")


@router.post("/revisoes/{revisao_id}/ativar")
def activate_revisao(revisao_id: str, request: Request):
    repo = RevisaoRepository()
    current = repo.get(revisao_id)
    if not current:
        return fail("Revisão não encontrada.", 404)
    try:
        RevisaoWorkflowService.ensure_can_activate(current)
    except RevisaoWorkflowError as exc:
        return fail(str(exc), 400)
    row = repo.activate(revisao_id)
    if not row:
        return fail("Revisão não encontrada.", 404)
    _audit(request, "revisao", revisao_id, "activate", {})
    return ok(row_to_json(row), "Revisão ativada.")


@router.delete("/revisoes/{revisao_id}")
def delete_revisao(revisao_id: str, request: Request):
    if not RevisaoRepository().soft_delete(revisao_id):
        return fail("Revisão não encontrada.", 404)
    _audit(request, "revisao", revisao_id, "delete", {})
    return ok(message="Revisão excluída.")


@router.get("/revisoes/{revisao_id}/diagnostico-rateio")
def revisao_diagnostico_rateio(revisao_id: str, competencia: str | None = None):
    data = RevisaoRateioDiagnosticService().diagnose(revisao_id, competencia=competencia)
    if not data:
        return fail("Revisão não encontrada.", 404)
    return ok(data, "Diagnóstico de rateio.")


# --- Medições ---


@router.get("/revisoes/{revisao_id}/medicoes")
def get_medicao(revisao_id: str):
    row = MedicaoRepository().get_by_revisao(revisao_id)
    return ok(row_to_json(row))


@router.post("/medicoes")
def upsert_medicao(body: MedicaoBody, request: Request):
    row = MedicaoRepository().upsert(body.model_dump())
    mid = str(row["medicao_id"])
    _audit(request, "medicao", mid, "upsert", body.model_dump())
    return ok(row_to_json(row), "Medição salva.")


# --- Investimentos ---


@router.get("/revisoes/{revisao_id}/investimentos")
def list_investimentos(revisao_id: str):
    rows = InvestimentoRepository().list_by_revisao(revisao_id)
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.post("/investimentos")
def create_investimento(body: InvestimentoBody, request: Request):
    try:
        assert_in(body.tipo_investimento, TIPO_INVESTIMENTO, "tipo_investimento")
        assert_in(body.recorrencia, RECORRENCIAS, "recorrencia")
        if body.categoria_investimento:
            assert_in(body.categoria_investimento, CATEGORIAS, "categoria_investimento")
        row = InvestimentoRepository().create(body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)

    iid = str(row["investimento_id"])
    _audit(request, "investimento", iid, "create", body.model_dump())
    return ok(row_to_json(row), "Investimento criado.", 201)


@router.delete("/investimentos/{investimento_id}")
def delete_investimento(investimento_id: str, request: Request):
    if not InvestimentoRepository().soft_delete(investimento_id):
        return fail("Investimento não encontrado.", 404)
    _audit(request, "investimento", investimento_id, "delete", {})
    return ok(message="Investimento excluído.")


# --- Recursos ---


@router.get("/recursos-compartilhados")
def list_recursos():
    rows = RecursoRepository().list()
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.post("/recursos-compartilhados")
def create_recurso(body: RecursoBody, request: Request):
    try:
        assert_in(body.tipo_custo, TIPO_CUSTO_RECURSO, "tipo_custo")
        assert_in(body.criterio_rateio, CRITERIO_RATEIO, "criterio_rateio")
        assert_in(body.status_recurso, STATUS_RECURSO, "status_recurso")
        assert_in(body.recorrencia, RECORRENCIAS, "recorrencia")
        row = RecursoRepository().create(body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)

    rid = str(row["recurso_compartilhado_id"])
    _audit(request, "recurso", rid, "create", body.model_dump())
    return ok(row_to_json(row), "Recurso criado.", 201)


@router.put("/recursos-compartilhados/{recurso_id}")
def update_recurso(recurso_id: str, body: RecursoBody, request: Request):
    try:
        assert_in(body.tipo_custo, TIPO_CUSTO_RECURSO, "tipo_custo")
        assert_in(body.criterio_rateio, CRITERIO_RATEIO, "criterio_rateio")
        assert_in(body.status_recurso, STATUS_RECURSO, "status_recurso")
        assert_in(body.recorrencia, RECORRENCIAS, "recorrencia")
        row = RecursoRepository().update(recurso_id, body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)

    if not row:
        return fail("Recurso não encontrado.", 404)

    _audit(request, "recurso", recurso_id, "update", body.model_dump())
    return ok(row_to_json(row), "Recurso atualizado.")


@router.delete("/recursos-compartilhados/{recurso_id}")
def delete_recurso(recurso_id: str, request: Request):
    if not RecursoRepository().soft_delete(recurso_id):
        return fail("Recurso não encontrado.", 404)
    _audit(request, "recurso", recurso_id, "delete", {})
    return ok(message="Recurso excluído.")


# --- Vínculos ---


@router.get("/revisoes/{revisao_id}/recursos-compartilhados")
def list_vinculos(revisao_id: str):
    rows = VinculoRepository().list_by_revisao(revisao_id)
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.post("/revisao-recursos-compartilhados")
def create_vinculo(body: VinculoBody, request: Request):
    row = VinculoRepository().create(body.model_dump())
    vid = str(row["vinculo_id"])
    _audit(request, "vinculo", vid, "create", body.model_dump())
    return ok(row_to_json(row), "Vínculo criado.", 201)


@router.put("/revisao-recursos-compartilhados/{vinculo_id}")
def update_vinculo(vinculo_id: str, body: VinculoUpdateBody, request: Request):
    row = VinculoRepository().update(vinculo_id, body.model_dump())
    if not row:
        return fail("Vínculo não encontrado.", 404)
    _audit(request, "vinculo", vinculo_id, "update", body.model_dump())
    return ok(row_to_json(row), "Vínculo atualizado.")


@router.delete("/revisao-recursos-compartilhados/{vinculo_id}")
def delete_vinculo(vinculo_id: str, request: Request):
    if not VinculoRepository().soft_delete(vinculo_id):
        return fail("Vínculo não encontrado.", 404)
    _audit(request, "vinculo", vinculo_id, "delete", {})
    return ok(message="Vínculo excluído.")


@router.get("/options")
def get_options():
    return ok(options_payload())
