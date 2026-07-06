from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request

from tm_app.application.services.audit_timeline_service import enrich_timeline_actor_names
from tm_app.application.services.transformometro_realtime_notify import notify_from_audit
from tm_app.core.auth_actor import actor_from_request
from tm_app.core.errors import format_api_error

from tm_app.core.catalogs import (
    BASE_COMPETENCIA_RECURSO,
    CENARIO_TIPO,
    CATEGORIAS,
    CRITERIO_RATEIO,
    FILIAIS,
    RECORRENCIAS,
    ESCOPO_RECURSO,
    STATUS_FILIAL,
    STATUS_PROCESSO,
    STATUS_RECURSO,
    STATUS_SETOR,
    TIPO_CUSTO_RECURSO,
    TIPO_INVESTIMENTO,
    assert_in,
)
from tm_app.core.responses import fail, ok
from tm_app.core.serialize import row_to_json, rows_to_json
from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository
from tm_app.infrastructure.persistence.repositories.investimento_repository import (
    InvestimentoRepository,
)
from tm_app.infrastructure.persistence.repositories.medicao_repository import MedicaoRepository
from tm_app.domain.services.processo_instancia_service import ProcessoInstanciaDomainError
from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_repository import ProcessoRepository
from tm_app.infrastructure.persistence.repositories.recurso_custo_repository import (
    RecursoCustoRepository,
)
from tm_app.infrastructure.persistence.repositories.recurso_repository import (
    RecursoRepository,
    VinculoRepository,
)
from tm_app.application.services.dashboard_live_service import DashboardLiveService
from tm_app.application.services.dashboard_recalc_hook_service import DashboardRecalcHookService
from tm_app.application.services.process_revision_compare_service import (
    ProcessRevisionCompareService,
)
from tm_app.application.services.processo_duplicate_service import (
    ProcessoDuplicateService,
    ProcessoNotFoundError,
)
from tm_app.application.services.instancia_duplicate_service import (
    InstanciaDuplicateService,
    InstanciaNotFoundError,
)
from tm_app.application.services.revisao_rateio_diagnostic_service import (
    RevisaoRateioDiagnosticService,
)
from tm_app.domain.services.filial_catalog_service import assert_filial_ativa
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from tm_app.infrastructure.persistence.repositories.filial_repository import FilialRepository
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository
from tm_app.infrastructure.persistence.repositories.setor_repository import SetorRepository
from tm_app.interface.http.schemas.crud_schemas import (
    FilialBody,
    FilialUpdateBody,
    InstanciaBody,
    InstanciaDuplicateBody,
    InstanciaUpdateBody,
    InvestimentoBody,
    InvestimentoUpdateBody,
    MedicaoBody,
    ProcessoCreateBody,
    ProcessoDuplicateBody,
    ProcessoUpdateBody,
    RecursoBody,
    RecursoCustoBody,
    RecursoCustoReajusteBody,
    RevisaoBody,
    SetorBody,
    SetorUpdateBody,
    VinculoBody,
    VinculoUpdateBody,
)
from tm_app.interface.http.filial_access_http import (
    check_instancia_view_access,
    check_manage_filial_access,
    check_processo_view_access,
    check_view_filial_access,
    filter_rows_for_access,
    require_unrestricted_catalog_admin,
)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro CRUD"])
logger = logging.getLogger(__name__)
_recalc_hook = DashboardRecalcHookService()


_PERSONAL_DATA_FIELDS = frozenset({
    "gestor_responsavel", "aprovado_por_email", "email",
    "user_email", "fornecedor",
})


def _mask_personal_data(payload: dict) -> dict:
    if not payload:
        return payload
    masked = {}
    for key, value in payload.items():
        if key in _PERSONAL_DATA_FIELDS and isinstance(value, str) and value:
            masked[key] = value[:2] + "***"
        else:
            masked[key] = value
    return masked


def _audit(request: Request, entity_type: str, entity_id: str, action: str, payload: dict):
    user_id, user_email, user_name = actor_from_request(request)
    try:
        AuditRepository().log(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            payload=_mask_personal_data(payload),
        )
    except Exception as exc:
        logger.warning(
            "audit_log_failed entity=%s id=%s action=%s err=%s",
            entity_type,
            entity_id,
            action,
            format_api_error(exc),
        )
    notify_from_audit(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_user_id=user_id,
        payload=payload,
    )


def _recalc_after_processo(processo_id: str) -> None:
    _recalc_hook.after_processo(processo_id)


def _recalc_after_revisao(revisao_id: str, *, processo_id: str | None = None) -> None:
    _recalc_hook.after_revisao(revisao_id, processo_id=processo_id)


def _recalc_after_global_resource_change() -> None:
    _recalc_hook.after_global_resource_change()


def _active_filial_codigos() -> set[str]:
    try:
        active = FilialRepository().list_active_codigos()
    except PluginsRepositoryError:
        active = set()
    if active:
        return active
    return set(FILIAIS.keys())


def _validate_processo_body(body: ProcessoCreateBody):
    assert_in(body.status_processo, STATUS_PROCESSO, "status_processo")
    has_filial = bool((body.filial_id or "").strip())
    has_setor = bool((body.setor_id or "").strip())
    if has_filial != has_setor:
        raise ValueError(
            "filial_id e setor_id devem ser informados juntos para criar instância operacional."
        )
    if not has_filial:
        return
    assert_filial_ativa(body.filial_id, _active_filial_codigos())
    if not SetorRepository().is_active_for_filial(body.setor_id, body.filial_id):
        raise ValueError(
            f"setor_id '{body.setor_id}' não está vinculado à unidade {body.filial_id}"
        )


def _validate_filial_body(body: FilialBody | FilialUpdateBody, *, is_create: bool):
    assert_in(body.status_filial, STATUS_FILIAL, "status_filial")
    if is_create and isinstance(body, FilialBody):
        from tm_app.domain.services.filial_catalog_service import normalize_codigo_filial

        normalize_codigo_filial(body.codigo_filial)


def _validate_setor_body(body: SetorBody | SetorUpdateBody, *, is_create: bool):
    assert_in(body.status_setor, STATUS_SETOR, "status_setor")
    for filial_id in body.filiais:
        assert_filial_ativa(filial_id, _active_filial_codigos())
    if is_create and isinstance(body, SetorBody):
        from tm_app.infrastructure.persistence.repositories.setor_repository import (
            normalize_setor_id,
        )

        normalize_setor_id(body.setor_id or body.nome_setor)


def _validate_recurso_body(body: RecursoBody):
    assert_in(body.tipo_custo, TIPO_CUSTO_RECURSO, "tipo_custo")
    assert_in(body.recorrencia, RECORRENCIAS, "recorrencia")
    assert_in(body.criterio_rateio, CRITERIO_RATEIO, "criterio_rateio")
    assert_in(body.base_competencia, BASE_COMPETENCIA_RECURSO, "base_competencia")
    assert_in(body.status_recurso, STATUS_RECURSO, "status_recurso")
    assert_in(body.escopo_recurso, ESCOPO_RECURSO, "escopo_recurso")
    if body.categoria_recurso:
        assert_in(body.categoria_recurso, CATEGORIAS, "categoria_recurso")


# --- Processos ---


@router.get("/processos")
def list_processos(
    request: Request,
    filial_id: str | None = None,
    setor_id: str | None = None,
    status: str | None = None,
    familia_processo: str | None = None,
    q: str | None = None,
):
    if filial_id:
        if err := check_view_filial_access(request, filial_id):
            return err
    rows = ProcessoRepository().list(
        filial_id=filial_id,
        setor_id=setor_id,
        status_processo=status,
        familia_processo=familia_processo,
        q=q,
    )
    rows = filter_rows_for_access(request, rows)
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.get("/processos/calculados")
def list_processos_calculados(
    request: Request,
    filial_id: str | None = None,
    setor_id: str | None = None,
    familia_processo: str | None = None,
):
    if filial_id:
        if err := check_view_filial_access(request, filial_id):
            return err
    items = DashboardLiveService().list_processos_calculados(
        filial_id=filial_id,
        setor_id=setor_id,
        familia_processo=familia_processo,
    )
    items = filter_rows_for_access(request, items)
    return ok(
        {"total": len(items), "items": rows_to_json(items)},
        "Processos com indicadores calculados em tempo real.",
    )


@router.get("/processos/{processo_id}")
def get_processo(processo_id: str, request: Request):
    if err := check_processo_view_access(request, processo_id):
        return err
    row = ProcessoRepository().get(processo_id)
    if not row:
        return fail("Processo não encontrado.", 404)
    return ok(row_to_json(row))


@router.get("/processos/{processo_id}/timeline")
def processo_timeline(
    processo_id: str,
    request: Request,
    page: int = 1,
    page_size: int = 100,
):
    if err := check_processo_view_access(request, processo_id):
        return err
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    data = AuditRepository().list_for_processo(processo_id, page=page, page_size=page_size)
    items = enrich_timeline_actor_names(
        rows_to_json(data["items"]),
        authorization=request.headers.get("Authorization"),
    )
    return ok(
        {
            "total": data["total"],
            "page": data["page"],
            "page_size": data["page_size"],
            "items": items,
        },
        "Linha do tempo de alterações do processo.",
    )


def _processo_master_payload(body: ProcessoCreateBody) -> dict:
    return {
        "nome_processo": body.nome_processo,
        "descricao_processo": body.descricao_processo,
        "gestor_responsavel": body.gestor_responsavel,
        "objetivo_processo": body.objetivo_processo,
        "status_processo": body.status_processo,
        "codigo_processo": body.codigo_processo,
        "familia_processo": body.familia_processo,
        "agrupador_ferramenta": body.agrupador_ferramenta,
    }


@router.post("/processos")
def create_processo(body: ProcessoCreateBody, request: Request):
    filial_id = (body.filial_id or "").strip() or None
    setor_id = (body.setor_id or "").strip() or None
    create_instancia = bool(filial_id and setor_id)
    if create_instancia:
        if err := check_manage_filial_access(request, filial_id):
            return err
    try:
        _validate_processo_body(body)
        repo = ProcessoRepository()
        row = repo.create(_processo_master_payload(body))
        pid = str(row["processo_id"])
        if create_instancia:
            instancia = ProcessoInstanciaRepository().create(
                {
                    "processo_id": pid,
                    "filial_id": filial_id,
                    "setor_ids": [setor_id],
                }
            )
            row = repo.get(pid) or {**row, **instancia}
    except ProcessoInstanciaDomainError as exc:
        return fail(str(exc), 400)
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("create_processo_failed")
        return fail(format_api_error(exc), 500)

    pid = str(row["processo_id"])
    _audit(request, "processo", pid, "create", body.model_dump())
    _recalc_after_processo(pid)
    return ok(row_to_json(row), "Processo criado.", 201)


@router.get("/processos/{processo_id}/instancias")
def list_processo_instancias(processo_id: str, request: Request):
    if err := check_processo_view_access(request, processo_id):
        return err
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    rows = ProcessoInstanciaRepository().list_by_processo(processo_id)
    rows = filter_rows_for_access(request, rows, codigo_key="codigo_filial")
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.post("/processos/{processo_id}/instancias")
def create_processo_instancia(processo_id: str, body: InstanciaBody, request: Request):
    if not body.todas_filiais_ativas:
        if err := check_manage_filial_access(request, body.filial_id or ""):
            return err
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    try:
        if not body.todas_filiais_ativas:
            assert_filial_ativa(body.filial_id or "", _active_filial_codigos())
        row = ProcessoInstanciaRepository().create(
            {
                "processo_id": processo_id,
                "filial_id": body.filial_id,
                "todas_filiais_ativas": body.todas_filiais_ativas,
                "setor_ids": body.setor_ids,
                "rotulo_instancia": body.rotulo_instancia,
                "status_instancia": body.status_instancia,
                "resumo_melhoria": body.resumo_melhoria,
                "responsavel_local": body.responsavel_local,
                "fase_melhoria": body.fase_melhoria,
                "data_alvo_go_live": body.data_alvo_go_live,
                "prioridade": body.prioridade,
            }
        )
    except ProcessoInstanciaDomainError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("create_processo_instancia_failed")
        return fail(format_api_error(exc), 500)

    iid = str(row["instancia_id"])
    _audit(request, "processo_instancia", iid, "create", body.model_dump())
    return ok(row_to_json(row), "Melhoria criada.", 201)


@router.get("/instancias/{instancia_id}")
def get_instancia(instancia_id: str, request: Request):
    if err := check_instancia_view_access(request, instancia_id):
        return err
    row = ProcessoInstanciaRepository().get(instancia_id)
    if not row:
        return fail("Instância não encontrada.", 404)
    return ok(row_to_json(row))


@router.put("/instancias/{instancia_id}")
def update_instancia(instancia_id: str, body: InstanciaUpdateBody, request: Request):
    if err := check_instancia_view_access(request, instancia_id):
        return err
    repo = ProcessoInstanciaRepository()
    existing = repo.get(instancia_id)
    if not existing:
        return fail("Instância não encontrada.", 404)
    filial_atual = str(existing.get("codigo_filial") or existing.get("filial_id") or "").strip()
    existing_todas = bool(existing.get("todas_filiais_ativas"))
    if not existing_todas:
        if err := check_manage_filial_access(request, filial_atual):
            return err

    # Escopo alvo: consolidada (todas as filiais) ou uma filial específica.
    target_todas = body.todas_filiais_ativas if body.todas_filiais_ativas is not None else existing_todas
    nova_filial = (body.filial_id or "").strip() or None
    if target_todas:
        target_filial = None
    else:
        target_filial = nova_filial or (filial_atual or None)
        if not target_filial:
            return fail("Informe a unidade da instância (ou marque todas as unidades ativas).", 400)

    scope_changed = (target_todas != existing_todas) or (
        not target_todas and (target_filial or "").lower() != filial_atual.lower()
    )
    if scope_changed and not target_todas:
        if err := check_manage_filial_access(request, target_filial):
            return err
        try:
            assert_filial_ativa(target_filial, _active_filial_codigos())
        except ValueError as exc:
            return fail(str(exc), 400)
    try:
        row = repo.update(
            instancia_id,
            {
                "setor_ids": body.setor_ids,
                "rotulo_instancia": body.rotulo_instancia,
                "status_instancia": body.status_instancia,
                "todas_filiais_ativas": target_todas,
                "filial_id": target_filial,
                "scope_changed": scope_changed,
                "resumo_melhoria": body.resumo_melhoria,
                "responsavel_local": body.responsavel_local,
                "fase_melhoria": body.fase_melhoria,
                "data_alvo_go_live": body.data_alvo_go_live,
                "prioridade": body.prioridade,
            },
        )
    except ProcessoInstanciaDomainError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("update_instancia_failed")
        return fail(format_api_error(exc), 500)

    _audit(request, "processo_instancia", instancia_id, "update", body.model_dump())
    if scope_changed:
        # Cache do dashboard é denormalizado por filial: recalcula ao mudar o escopo.
        _recalc_after_processo(str(existing["processo_id"]))
    return ok(row_to_json(row), "Melhoria atualizada.")


@router.delete("/instancias/{instancia_id}")
def delete_instancia(instancia_id: str, request: Request):
    if err := check_instancia_view_access(request, instancia_id):
        return err
    existing = ProcessoInstanciaRepository().get(instancia_id)
    if not existing:
        return fail("Instância não encontrada.", 404)
    if not existing.get("todas_filiais_ativas"):
        filial_codigo = str(existing.get("codigo_filial") or existing.get("filial_id") or "")
        if err := check_manage_filial_access(request, filial_codigo):
            return err
    try:
        if not ProcessoInstanciaRepository().soft_delete(instancia_id):
            return fail("Instância não encontrada.", 404)
    except ProcessoInstanciaDomainError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("delete_instancia_failed")
        return fail(format_api_error(exc), 500)

    _audit(request, "processo_instancia", instancia_id, "delete", {})
    return ok(message="Instância operacional excluída.")


@router.post("/instancias/{instancia_id}/duplicar")
def duplicate_instancia(instancia_id: str, body: InstanciaDuplicateBody, request: Request):
    if err := check_instancia_view_access(request, instancia_id):
        return err
    if err := check_manage_filial_access(request, body.filial_id):
        return err
    try:
        result = InstanciaDuplicateService().duplicate(
            instancia_id,
            filial_id=body.filial_id,
            setor_id=body.setor_id,
            rotulo_instancia=body.rotulo_instancia,
        )
    except InstanciaNotFoundError as exc:
        return fail(str(exc), 404)
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("duplicate_instancia_failed")
        return fail(format_api_error(exc), 500)

    target_id = str(result["instancia"]["instancia_id"])
    processo_id = str(result["processo_id"])
    _audit(
        request,
        "processo_instancia",
        target_id,
        "duplicate",
        {
            "origem_instancia_id": instancia_id,
            "filial_id": body.filial_id,
            "setor_id": body.setor_id,
            "copiados": result["copiados"],
        },
    )
    _recalc_after_processo(processo_id)
    return ok(
        {
            "instancia": row_to_json(result["instancia"]),
            "processo_id": processo_id,
            "origem_instancia_id": instancia_id,
            "copiados": result["copiados"],
        },
        "Instância replicada com timeline de revisões.",
        201,
    )


@router.put("/processos/{processo_id}")
def update_processo(processo_id: str, body: ProcessoUpdateBody, request: Request):
    try:
        assert_in(body.status_processo, STATUS_PROCESSO, "status_processo")
        row = ProcessoRepository().update(processo_id, _processo_master_payload(body))
    except ValueError as exc:
        return fail(str(exc), 400)

    if not row:
        return fail("Processo não encontrado.", 404)

    _audit(request, "processo", processo_id, "update", body.model_dump())
    _recalc_after_processo(processo_id)
    return ok(row_to_json(row), "Processo atualizado.")


@router.delete("/processos/{processo_id}")
def delete_processo(processo_id: str, request: Request):
    if not ProcessoRepository().soft_delete(processo_id):
        return fail("Processo não encontrado.", 404)
    _audit(request, "processo", processo_id, "delete", {})
    _recalc_after_processo(processo_id)
    return ok(message="Processo excluído.")


@router.post("/processos/{processo_id}/duplicar")
def duplicate_processo(
    processo_id: str,
    request: Request,
    body: ProcessoDuplicateBody | None = None,
):
    try:
        result = ProcessoDuplicateService().duplicate(
            processo_id,
            nome_processo=body.nome_processo if body else None,
        )
    except ProcessoNotFoundError as exc:
        return fail(str(exc), 404)
    except ValueError as exc:
        return fail(str(exc), 400)

    new_id = str(result["processo"]["processo_id"])
    _audit(
        request,
        "processo",
        new_id,
        "duplicate",
        {
            "origem_processo_id": processo_id,
            "copiados": result["copiados"],
        },
    )
    _recalc_after_processo(new_id)
    payload = {
        "processo": row_to_json(result["processo"]),
        "origem_processo_id": processo_id,
        "copiados": result["copiados"],
    }
    return ok(payload, "Processo duplicado com melhorias, diagrama, mapeamento e revisões.", 201)


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
    _recalc_after_revisao(rid, processo_id=str(body.processo_id))
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
    _recalc_after_revisao(revisao_id, processo_id=str(row["processo_id"]))
    return ok(row_to_json(row), "Revisão atualizada.")


@router.post("/revisoes/{revisao_id}/ativar")
def activate_revisao(revisao_id: str, request: Request):
    repo = RevisaoRepository()
    row = repo.activate(revisao_id)
    if not row:
        return fail("Revisão não encontrada.", 404)
    _audit(request, "revisao", revisao_id, "activate", {})
    _recalc_after_revisao(revisao_id, processo_id=str(row["processo_id"]))
    return ok(row_to_json(row), "Revisão ativada.")


@router.delete("/revisoes/{revisao_id}")
def delete_revisao(revisao_id: str, request: Request):
    if not RevisaoRepository().soft_delete(revisao_id):
        return fail("Revisão não encontrada.", 404)
    _audit(request, "revisao", revisao_id, "delete", {})
    _recalc_after_revisao(revisao_id)
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
    _recalc_after_revisao(str(body.revisao_id))
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
    _recalc_after_revisao(str(body.revisao_id))
    return ok(row_to_json(row), "Investimento criado.", 201)


@router.put("/investimentos/{investimento_id}")
def update_investimento(investimento_id: str, body: InvestimentoUpdateBody, request: Request):
    try:
        assert_in(body.tipo_investimento, TIPO_INVESTIMENTO, "tipo_investimento")
        assert_in(body.recorrencia, RECORRENCIAS, "recorrencia")
        if body.categoria_investimento:
            assert_in(body.categoria_investimento, CATEGORIAS, "categoria_investimento")
        row = InvestimentoRepository().update(investimento_id, body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)

    if not row:
        return fail("Investimento não encontrado.", 404)

    _audit(request, "investimento", investimento_id, "update", body.model_dump())
    _recalc_after_revisao(str(row["revisao_id"]))
    return ok(row_to_json(row), "Investimento atualizado.")


@router.delete("/investimentos/{investimento_id}")
def delete_investimento(investimento_id: str, request: Request):
    existing = InvestimentoRepository().get(investimento_id)
    if not existing:
        return fail("Investimento não encontrado.", 404)
    if not InvestimentoRepository().soft_delete(investimento_id):
        return fail("Investimento não encontrado.", 404)
    _audit(request, "investimento", investimento_id, "delete", {})
    _recalc_after_revisao(str(existing["revisao_id"]))
    return ok(message="Investimento excluído.")


# --- Filiais ---


@router.get("/filiais")
def list_filiais(request: Request, include_inactive: bool = False):
    rows = FilialRepository().list(include_inactive=include_inactive)
    rows = filter_rows_for_access(
        request,
        rows,
        codigo_key="codigo_filial",
        alt_codigo_key=None,
    )
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.get("/filiais/{filial_id}")
def get_filial(filial_id: str, request: Request):
    if err := check_view_filial_access(request, filial_id):
        return err
    row = FilialRepository().get(filial_id)
    if not row:
        return fail("Unidade não encontrada.", 404)
    return ok(row_to_json(row))


@router.post("/filiais")
def create_filial(body: FilialBody, request: Request):
    if err := require_unrestricted_catalog_admin(request):
        return err
    try:
        _validate_filial_body(body, is_create=True)
        row = FilialRepository().create(body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("create_filial_failed")
        return fail(format_api_error(exc), 500)

    fid = str(row["filial_id"])
    _audit(request, "filial", fid, "create", body.model_dump())
    return ok(row_to_json(row), "Unidade criada.", 201)


@router.put("/filiais/{filial_id}")
def update_filial(filial_id: str, body: FilialUpdateBody, request: Request):
    if err := require_unrestricted_catalog_admin(request):
        return err
    try:
        _validate_filial_body(body, is_create=False)
        row = FilialRepository().update(filial_id, body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("update_filial_failed")
        return fail(format_api_error(exc), 500)

    if not row:
        return fail("Unidade não encontrada.", 404)

    _audit(request, "filial", str(row["filial_id"]), "update", body.model_dump())
    return ok(row_to_json(row), "Unidade atualizada.")


@router.delete("/filiais/{filial_id}")
def delete_filial(filial_id: str, request: Request):
    if err := require_unrestricted_catalog_admin(request):
        return err
    existing = FilialRepository().get(filial_id)
    if not existing:
        return fail("Unidade não encontrada.", 404)
    try:
        if not FilialRepository().soft_delete(filial_id):
            return fail("Unidade não encontrada.", 404)
    except ValueError as exc:
        return fail(str(exc), 400)

    _audit(request, "filial", str(existing["filial_id"]), "delete", {})
    return ok(message="Unidade excluída.")


# --- Setores ---


@router.get("/setores")
def list_setores(request: Request, filial_id: str | None = None):
    if filial_id:
        if err := check_view_filial_access(request, filial_id):
            return err
    rows = SetorRepository().list(filial_id=filial_id)
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.get("/setores/{setor_id}")
def get_setor(setor_id: str):
    row = SetorRepository().get(setor_id)
    if not row:
        return fail("Setor não encontrado.", 404)
    return ok(row_to_json(row))


@router.post("/setores")
def create_setor(body: SetorBody, request: Request):
    try:
        _validate_setor_body(body, is_create=True)
        row = SetorRepository().create(body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("create_setor_failed")
        return fail(format_api_error(exc), 500)

    sid = str(row["setor_id"])
    _audit(request, "setor", sid, "create", body.model_dump())
    return ok(row_to_json(row), "Setor criado.", 201)


@router.put("/setores/{setor_id}")
def update_setor(setor_id: str, body: SetorUpdateBody, request: Request):
    try:
        _validate_setor_body(body, is_create=False)
        row = SetorRepository().update(setor_id, body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        logger.exception("update_setor_failed")
        return fail(format_api_error(exc), 500)

    if not row:
        return fail("Setor não encontrado.", 404)

    _audit(request, "setor", setor_id, "update", body.model_dump())
    return ok(row_to_json(row), "Setor atualizado.")


@router.delete("/setores/{setor_id}")
def delete_setor(setor_id: str, request: Request):
    try:
        if not SetorRepository().soft_delete(setor_id):
            return fail("Setor não encontrado.", 404)
    except ValueError as exc:
        return fail(str(exc), 400)

    _audit(request, "setor", setor_id, "delete", {})
    return ok(message="Setor excluído.")


# --- Recursos ---


@router.get("/recursos-compartilhados")
def list_recursos():
    rows = RecursoRepository().list()
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.get("/recursos-compartilhados/{recurso_id}")
def get_recurso(recurso_id: str):
    row = RecursoRepository().get(recurso_id)
    if not row:
        return fail("Recurso não encontrado.", 404)
    return ok(row_to_json(row))


@router.post("/recursos-compartilhados")
def create_recurso(body: RecursoBody, request: Request):
    try:
        _validate_recurso_body(body)
        row = RecursoRepository().create(body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)

    rid = str(row["recurso_compartilhado_id"])
    _audit(request, "recurso", rid, "create", body.model_dump())
    _recalc_after_global_resource_change()
    return ok(row_to_json(row), "Recurso criado.", 201)


@router.put("/recursos-compartilhados/{recurso_id}")
def update_recurso(recurso_id: str, body: RecursoBody, request: Request):
    try:
        _validate_recurso_body(body)
        row = RecursoRepository().update(recurso_id, body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)

    if not row:
        return fail("Recurso não encontrado.", 404)

    _audit(request, "recurso", recurso_id, "update", body.model_dump())
    _recalc_after_global_resource_change()
    return ok(row_to_json(row), "Recurso atualizado.")


@router.delete("/recursos-compartilhados/{recurso_id}")
def delete_recurso(recurso_id: str, request: Request):
    if not RecursoRepository().soft_delete(recurso_id):
        return fail("Recurso não encontrado.", 404)
    _audit(request, "recurso", recurso_id, "delete", {})
    _recalc_after_global_resource_change()
    return ok(message="Recurso excluído.")


@router.get("/recursos-compartilhados/{recurso_id}/vinculos")
def list_recurso_vinculos(recurso_id: str):
    if not RecursoRepository().get(recurso_id):
        return fail("Recurso não encontrado.", 404)
    rows = VinculoRepository().list_by_recurso(recurso_id)
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.get("/recursos-compartilhados/{recurso_id}/custos")
def list_recurso_custos(recurso_id: str):
    if not RecursoRepository().get(recurso_id):
        return fail("Recurso não encontrado.", 404)
    rows = RecursoCustoRepository().list_by_recurso(recurso_id)
    return ok({"total": len(rows), "items": rows_to_json(rows)})


@router.post("/recursos-compartilhados/{recurso_id}/custos")
def create_recurso_custo(recurso_id: str, body: RecursoCustoBody, request: Request):
    if not RecursoRepository().get(recurso_id):
        return fail("Recurso não encontrado.", 404)
    try:
        row = RecursoCustoRepository().create(
            {
                "recurso_compartilhado_id": recurso_id,
                **body.model_dump(),
            }
        )
    except ValueError as exc:
        return fail(str(exc), 400)

    cid = str(row["recurso_custo_id"])
    _audit(request, "recurso_custo", cid, "create", body.model_dump())
    _recalc_after_global_resource_change()
    recurso = RecursoRepository().get(recurso_id)
    return ok(
        {"custo": row_to_json(row), "recurso": row_to_json(recurso) if recurso else None},
        "Vigência de custo registrada.",
        201,
    )


@router.post("/recursos-compartilhados/{recurso_id}/custos/reajuste")
def reajuste_recurso_custo(recurso_id: str, body: RecursoCustoReajusteBody, request: Request):
    if not RecursoRepository().get(recurso_id):
        return fail("Recurso não encontrado.", 404)
    try:
        row = RecursoCustoRepository().registrar_reajuste(
            recurso_id,
            float(body.valor_mensal),
            body.vigente_desde,
            body.observacoes,
        )
    except ValueError as exc:
        return fail(str(exc), 400)

    cid = str(row["recurso_custo_id"])
    _audit(request, "recurso_custo", cid, "reajuste", body.model_dump())
    _recalc_after_global_resource_change()
    recurso = RecursoRepository().get(recurso_id)
    return ok(
        {"custo": row_to_json(row), "recurso": row_to_json(recurso) if recurso else None},
        "Reajuste de custo registrado.",
        201,
    )


@router.put("/recurso-custos/{recurso_custo_id}")
def update_recurso_custo(recurso_custo_id: str, body: RecursoCustoBody, request: Request):
    existing = RecursoCustoRepository().get(recurso_custo_id)
    if not existing:
        return fail("Vigência de custo não encontrada.", 404)
    try:
        row = RecursoCustoRepository().update(recurso_custo_id, body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 400)

    if not row:
        return fail("Vigência de custo não encontrada.", 404)

    _audit(request, "recurso_custo", recurso_custo_id, "update", body.model_dump())
    _recalc_after_global_resource_change()
    recurso = RecursoRepository().get(str(existing["recurso_compartilhado_id"]))
    return ok(
        {"custo": row_to_json(row), "recurso": row_to_json(recurso) if recurso else None},
        "Vigência de custo atualizada.",
    )


@router.delete("/recurso-custos/{recurso_custo_id}")
def delete_recurso_custo(recurso_custo_id: str, request: Request):
    existing = RecursoCustoRepository().get(recurso_custo_id)
    if not existing:
        return fail("Vigência de custo não encontrada.", 404)
    if not RecursoCustoRepository().soft_delete(recurso_custo_id):
        return fail("Vigência de custo não encontrada.", 404)
    _audit(request, "recurso_custo", recurso_custo_id, "delete", {})
    _recalc_after_global_resource_change()
    recurso = RecursoRepository().get(str(existing["recurso_compartilhado_id"]))
    return ok(
        {"recurso": row_to_json(recurso) if recurso else None},
        message="Vigência de custo excluída.",
    )


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
    _recalc_after_global_resource_change()
    return ok(row_to_json(row), "Vínculo criado.", 201)


@router.put("/revisao-recursos-compartilhados/{vinculo_id}")
def update_vinculo(vinculo_id: str, body: VinculoUpdateBody, request: Request):
    row = VinculoRepository().update(vinculo_id, body.model_dump())
    if not row:
        return fail("Vínculo não encontrado.", 404)
    _audit(request, "vinculo", vinculo_id, "update", body.model_dump())
    _recalc_after_global_resource_change()
    return ok(row_to_json(row), "Vínculo atualizado.")


@router.delete("/revisao-recursos-compartilhados/{vinculo_id}")
def delete_vinculo(vinculo_id: str, request: Request):
    if not VinculoRepository().get(vinculo_id):
        return fail("Vínculo não encontrado.", 404)
    if not VinculoRepository().soft_delete(vinculo_id):
        return fail("Vínculo não encontrado.", 404)
    _audit(request, "vinculo", vinculo_id, "delete", {})
    _recalc_after_global_resource_change()
    return ok(message="Vínculo excluído.")
