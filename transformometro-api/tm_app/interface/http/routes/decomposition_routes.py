from __future__ import annotations

import logging
from typing import Any

from datetime import date

from fastapi import APIRouter, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from tm_app.application.services.decomposition_flat_export_service import (
    DecompositionFlatExportService,
)
from tm_app.application.services.decomposition_flowchart_link_validator import (
    DecompositionFlowchartLinkValidator,
)
from tm_app.application.services.decomposicao_composition_service import (
    DecomposicaoCompositionService,
)
from tm_app.application.services.revisao_decomposicao_merge_service import (
    RevisaoDecomposicaoMergeService,
)
from tm_app.application.services.transformometro_realtime_notify import notify_from_audit
from tm_app.core.auth_actor import actor_from_request, client_id_from_request
from tm_app.core.errors import format_api_error
from tm_app.core.responses import fail, ok
from tm_app.domain.decomposition.decomposition_tree_v1 import (
    DecompositionValidationError,
    empty_contexto,
    empty_escopo,
    empty_overlay,
    empty_tree,
    tree_node_ids,
    validate_decomposition_escopo,
    validate_decomposition_tree_v1,
    validate_instancia_contexto_v1,
)
from tm_app.domain.diagram.flowchart_v1 import empty_flowchart
from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository
from tm_app.infrastructure.persistence.repositories.instancia_decomposicao_escopo_repository import (
    InstanciaDecomposicaoEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_decomposicao_repository import (
    ProcessoDecomposicaoRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_diagram_repository import (
    ProcessoDiagramRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_repository import ProcessoRepository
from tm_app.infrastructure.persistence.repositories.revisao_decomposicao_overlay_repository import (
    RevisaoDecomposicaoOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro — decomposição"])

_merge = RevisaoDecomposicaoMergeService()
_composition = DecomposicaoCompositionService()
_export = DecompositionFlatExportService()
_link_validator = DecompositionFlowchartLinkValidator()


class TreeBody(BaseModel):
    conteudo: dict[str, Any] = Field(default_factory=dict)


class DecompositionEscopoBody(BaseModel):
    node_ids: list[str] = Field(default_factory=list)
    inherit_all: bool = True
    include_descendants: bool = True


class OverlayBody(BaseModel):
    conteudo: dict[str, Any] = Field(default_factory=dict)


class ContextoBody(BaseModel):
    conteudo: dict[str, Any] = Field(default_factory=dict)


def _audit(request: Request, entity_type: str, entity_id: str, action: str, payload: dict):
    user_id, user_email, user_name = actor_from_request(request)
    try:
        AuditRepository().log(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name or user_email,
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
    notify_from_audit(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_user_id=user_id,
        actor_client_id=client_id_from_request(request),
        payload=payload,
    )


def _tree_response(row: dict[str, Any] | None, processo_id: str | None = None) -> dict[str, Any]:
    if not row:
        empty = empty_tree()
        return {
            "processo_id": processo_id,
            "conteudo": empty,
            "empty": True,
        }
    conteudo = row.get("conteudo") or empty_tree()
    return {
        "processo_id": str(row.get("processo_id") or processo_id),
        "conteudo": conteudo,
        "empty": not (conteudo.get("nodes") or []),
        "updated_at": row.get("updated_at"),
    }


def _escopo_response(row: dict[str, Any] | None, instancia_id: str) -> dict[str, Any]:
    if not row:
        default = empty_escopo()
        return {"instancia_id": instancia_id, **default, "empty": True}
    return {
        "instancia_id": instancia_id,
        "node_ids": row.get("node_ids") or [],
        "inherit_all": bool(row.get("inherit_all", True)),
        "include_descendants": bool(row.get("include_descendants", True)),
        "empty": False,
        "updated_at": row.get("updated_at"),
    }


def _overlay_response(row: dict[str, Any] | None, revisao_id: str) -> dict[str, Any]:
    if not row:
        empty = empty_overlay()
        return {"revisao_id": revisao_id, "conteudo": empty, "empty": True}
    conteudo = row.get("conteudo") or empty_overlay()
    return {
        "revisao_id": revisao_id,
        "conteudo": conteudo,
        "empty": not conteudo.get("node_overrides") and not conteudo.get("disabled_node_ids"),
        "updated_at": row.get("updated_at"),
    }


def _departamento_label(instancia: dict[str, Any]) -> str:
    setores = instancia.get("setores") or []
    if isinstance(setores, list) and setores:
        names = [
            str(s.get("nome_setor") or s.get("codigo_setor") or "")
            for s in setores
            if isinstance(s, dict)
        ]
        return ", ".join(n for n in names if n)
    return str(instancia.get("nome_setor") or instancia.get("codigo_setor") or "")


def _load_decomposition_merge_context(revisao_id: str):
    revisao = RevisaoRepository().get(revisao_id)
    if not revisao:
        return None, None, None, None

    processo_id = str(revisao["processo_id"])
    instancia_id = str(revisao.get("instancia_id") or "")

    tree_row = ProcessoDecomposicaoRepository().get(processo_id)
    tree = (tree_row or {}).get("conteudo") if tree_row else None

    escopo_row = (
        InstanciaDecomposicaoEscopoRepository().get(instancia_id) if instancia_id else None
    )
    if escopo_row:
        escopo = {
            "node_ids": escopo_row.get("node_ids") or [],
            "inherit_all": bool(escopo_row.get("inherit_all", True)),
            "include_descendants": bool(escopo_row.get("include_descendants", True)),
        }
    else:
        escopo = empty_escopo()

    overlay_row = RevisaoDecomposicaoOverlayRepository().get(revisao_id)
    overlay = (overlay_row or {}).get("conteudo") if overlay_row else None
    return revisao, tree, escopo, overlay


@router.get("/processos/{processo_id}/decomposicao")
def get_processo_decomposicao(processo_id: str):
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    row = ProcessoDecomposicaoRepository().get(processo_id)
    return ok(_tree_response(row, processo_id), "Árvore de decomposição do processo.")


@router.get("/processos/{processo_id}/decomposicao/composed")
def get_processo_decomposicao_composed(
    processo_id: str,
    at: date | None = Query(default=None, description="Data de composição (YYYY-MM-DD)"),
    instancia_id: str | None = Query(default=None),
):
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    composed = _composition.compose_for_processo(
        processo_id,
        at=at,
        instancia_id=instancia_id,
    )
    return ok(composed, "Macro composto na data informada.")


@router.put("/processos/{processo_id}/decomposicao")
def put_processo_decomposicao(processo_id: str, body: TreeBody, request: Request):
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    try:
        conteudo = validate_decomposition_tree_v1(body.conteudo)
    except DecompositionValidationError as exc:
        return fail(str(exc), 400)

    row = ProcessoDecomposicaoRepository().upsert(processo_id, conteudo=conteudo)
    _audit(
        request,
        "processo",
        processo_id,
        "decomposition.updated",
        {"nodes": len(conteudo.get("nodes", []))},
    )
    payload = _tree_response(row, processo_id)
    return ok(payload, "Árvore de decomposição salva.")


@router.get("/processos/{processo_id}/decomposicao/export.csv")
def get_processo_decomposicao_export_csv(
    processo_id: str,
    instancia_id: str | None = None,
    revisao_id: str | None = None,
):
    processo = ProcessoRepository().get(processo_id)
    if not processo:
        return fail("Processo não encontrado.", 404)

    tree_row = ProcessoDecomposicaoRepository().get(processo_id)
    tree = (tree_row or {}).get("conteudo") or empty_tree()
    overlay = None
    departamento = ""

    if revisao_id:
        revisao, _, escopo, merged_overlay = _load_decomposition_merge_context(revisao_id)
        if not revisao or str(revisao.get("processo_id")) != processo_id:
            return fail("Revisão não encontrada para este processo.", 404)
        merged = _merge.merge(tree=tree, escopo=escopo, overlay=merged_overlay)
        tree = merged["tree"]
        overlay = merged_overlay
        inst = ProcessoInstanciaRepository().get(str(revisao.get("instancia_id") or ""))
        if inst:
            departamento = _departamento_label(inst)
    elif instancia_id:
        inst = ProcessoInstanciaRepository().get(instancia_id)
        if not inst or str(inst.get("processo_id")) != processo_id:
            return fail("Instância não encontrada para este processo.", 404)
        escopo_row = InstanciaDecomposicaoEscopoRepository().get(instancia_id)
        escopo = (
            {
                "node_ids": escopo_row.get("node_ids") or [],
                "inherit_all": bool(escopo_row.get("inherit_all", True)),
                "include_descendants": bool(escopo_row.get("include_descendants", True)),
            }
            if escopo_row
            else empty_escopo()
        )
        merged = _merge.merge(tree=tree, escopo=escopo, overlay=None)
        tree = merged["tree"]
        departamento = _departamento_label(inst)

    macroprocesso = str(processo.get("nome_processo") or "")
    rows = _export.build_rows(
        tree=tree,
        macroprocesso=macroprocesso,
        departamento=departamento,
        overlay=overlay,
    )
    csv_text = _export.to_csv(rows)
    filename = f"mapeamento-{processo.get('codigo_processo', processo_id)}.csv"
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/processos/{processo_id}/decomposicao/validar-vinculos-fluxo")
def post_validar_vinculos_fluxo(processo_id: str):
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    tree_row = ProcessoDecomposicaoRepository().get(processo_id)
    tree = (tree_row or {}).get("conteudo") or empty_tree()
    diagram_row = ProcessoDiagramRepository().get(processo_id)
    flowchart = (diagram_row or {}).get("conteudo") or empty_flowchart()
    report = _link_validator.validate(tree=tree, flowchart=flowchart)
    return ok(report, "Validação de vínculos árvore ↔ fluxo.")


@router.post("/processos/{processo_id}/decomposicao/sugerir-rascunho")
def post_sugerir_rascunho_decomposicao(processo_id: str):
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    diagram_row = ProcessoDiagramRepository().get(processo_id)
    flowchart = (diagram_row or {}).get("conteudo") or empty_flowchart()

    draft_nodes: list[dict[str, Any]] = []
    ordem_pk = 1
    for node in flowchart.get("nodes", []):
        if not isinstance(node, dict):
            continue
        if node.get("type") != "subprocess":
            continue
        pk_id = f"pk_{node.get('id', ordem_pk)}"
        draft_nodes.append(
            {
                "id": pk_id,
                "level": "processo_chave",
                "ordem": ordem_pk,
                "label": str(node.get("label") or f"Processo-chave {ordem_pk}"),
                "parent_id": None,
                "descricao": None,
                "meta": {"source_flow_node_id": str(node.get("id") or "")},
            }
        )
        ordem_pk += 1

    ordem_st = 1
    for node in flowchart.get("nodes", []):
        if not isinstance(node, dict) or node.get("type") != "process":
            continue
        parent_pk = draft_nodes[0]["id"] if draft_nodes else None
        if not parent_pk:
            continue
        draft_nodes.append(
            {
                "id": f"st_{node.get('id', ordem_st)}",
                "level": "sub_tarefa",
                "ordem": ordem_st,
                "label": str(node.get("label") or f"Sub-tarefa {ordem_st}"),
                "parent_id": parent_pk,
                "descricao": None,
                "meta": {"source_flow_node_id": str(node.get("id") or "")},
            }
        )
        ordem_st += 1

    draft = {
        "format": "decomposition_tree_v1",
        "format_version": 1,
        "nodes": draft_nodes,
    }
    return ok(
        {"conteudo": draft, "persisted": False},
        "Rascunho sugerido a partir do diagrama macro — revise antes de salvar.",
    )


@router.get("/instancias/{instancia_id}/decomposicao-escopo")
def get_instancia_decomposicao_escopo(instancia_id: str):
    instancia = ProcessoInstanciaRepository().get(instancia_id)
    if not instancia:
        return fail("Instância não encontrada.", 404)
    row = InstanciaDecomposicaoEscopoRepository().get(instancia_id)
    return ok(_escopo_response(row, instancia_id), "Escopo WBS da instância.")


@router.put("/instancias/{instancia_id}/decomposicao-escopo")
def put_instancia_decomposicao_escopo(
    instancia_id: str,
    body: DecompositionEscopoBody,
    request: Request,
):
    instancia = ProcessoInstanciaRepository().get(instancia_id)
    if not instancia:
        return fail("Instância não encontrada.", 404)

    tree_row = ProcessoDecomposicaoRepository().get(str(instancia["processo_id"]))
    tree = (tree_row or {}).get("conteudo") or empty_tree()
    try:
        escopo = validate_decomposition_escopo(
            body.model_dump(),
            tree_node_ids_set=tree_node_ids(tree),
        )
    except DecompositionValidationError as exc:
        return fail(str(exc), 400)

    row = InstanciaDecomposicaoEscopoRepository().upsert(
        instancia_id,
        node_ids=escopo["node_ids"],
        inherit_all=escopo["inherit_all"],
        include_descendants=escopo["include_descendants"],
    )
    _audit(
        request,
        "processo_instancia",
        instancia_id,
        "decomposition.scope.updated",
        {"inherit_all": escopo["inherit_all"], "nodes": len(escopo["node_ids"])},
    )
    return ok(_escopo_response(row, instancia_id), "Escopo WBS salvo.")


@router.get("/instancias/{instancia_id}/contexto")
def get_instancia_contexto(instancia_id: str):
    instancia = ProcessoInstanciaRepository().get(instancia_id)
    if not instancia:
        return fail("Instância não encontrada.", 404)
    contexto = instancia.get("contexto") or empty_contexto()
    return ok(
        {"instancia_id": instancia_id, "conteudo": contexto, "empty": not contexto.get("node_notes")},
        "Contexto operacional da instância.",
    )


@router.put("/instancias/{instancia_id}/contexto")
def put_instancia_contexto(instancia_id: str, body: ContextoBody, request: Request):
    instancia = ProcessoInstanciaRepository().get(instancia_id)
    if not instancia:
        return fail("Instância não encontrada.", 404)
    try:
        contexto = validate_instancia_contexto_v1(body.conteudo)
    except DecompositionValidationError as exc:
        return fail(str(exc), 400)

    ProcessoInstanciaRepository().update_contexto(instancia_id, contexto)
    _audit(
        request,
        "processo_instancia",
        instancia_id,
        "decomposition.context.updated",
        {"node_notes": len(contexto.get("node_notes") or {})},
    )
    return ok(
        {"instancia_id": instancia_id, "conteudo": contexto},
        "Contexto operacional salvo.",
    )


@router.get("/revisoes/{revisao_id}/decomposicao")
def get_revisao_decomposicao_merged(revisao_id: str):
    revisao, tree, escopo, overlay = _load_decomposition_merge_context(revisao_id)
    if not revisao:
        return fail("Revisão não encontrada.", 404)

    reference_overlay = None
    reference_meta = None
    baseline_revisao = RevisaoRepository().find_reference_for_revisao(
        revisao_id,
        revisao_row=revisao,
    )
    if baseline_revisao:
        _, _, _, reference_overlay = _load_decomposition_merge_context(
            str(baseline_revisao["revisao_id"])
        )
        reference_meta = {
            "revisao_id": str(baseline_revisao["revisao_id"]),
            "versao_revisao": baseline_revisao.get("versao_revisao"),
            "cenario_tipo": baseline_revisao.get("cenario_tipo"),
        }

    view = _merge.build_revisao_view(
        tree=tree,
        escopo=escopo,
        overlay=overlay,
        reference_overlay=reference_overlay,
        reference_meta=reference_meta,
    )

    return ok(
        {
            "revisao_id": revisao_id,
            "cenario_tipo": revisao.get("cenario_tipo"),
            **view,
        },
        "Árvore de decomposição mesclada da revisão.",
    )


@router.get("/revisoes/{revisao_id}/decomposicao/overlay")
def get_revisao_decomposicao_overlay(revisao_id: str):
    if not RevisaoRepository().get(revisao_id):
        return fail("Revisão não encontrada.", 404)
    row = RevisaoDecomposicaoOverlayRepository().get(revisao_id)
    return ok(_overlay_response(row, revisao_id), "Overlay de decomposição da revisão.")


@router.put("/revisoes/{revisao_id}/decomposicao/overlay")
def put_revisao_decomposicao_overlay(revisao_id: str, body: OverlayBody, request: Request):
    revisao = RevisaoRepository().get(revisao_id)
    if not revisao:
        return fail("Revisão não encontrada.", 404)
    _, tree, escopo, _ = _load_decomposition_merge_context(revisao_id)
    try:
        conteudo = _merge.assert_overlay_within_escopo(
            tree=tree,
            escopo=escopo,
            overlay=body.conteudo,
        )
    except DecompositionValidationError as exc:
        return fail(str(exc), 400)

    row = RevisaoDecomposicaoOverlayRepository().upsert(revisao_id, conteudo=conteudo)
    _audit(
        request,
        "revisao",
        revisao_id,
        "decomposition.overlay.updated",
        {"overrides": len(conteudo.get("node_overrides") or {})},
    )
    return ok(_overlay_response(row, revisao_id), "Overlay de decomposição salvo.")
