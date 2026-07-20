from __future__ import annotations

import logging
from typing import Any

from datetime import date

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from tm_app.application.services.diagram_mermaid_export_service import DiagramMermaidExportService
from tm_app.application.services.diagrama_composition_service import DiagramaCompositionService
from tm_app.application.services.flowchart_bpmn_xml_service import FlowchartBpmnXmlService
from tm_app.application.services.revisao_diagram_merge_service import RevisaoDiagramMergeService
from tm_app.application.services.transformometro_realtime_notify import notify_from_audit
from tm_app.core.auth_actor import actor_from_request
from tm_app.core.errors import format_api_error
from tm_app.core.responses import fail, ok
from tm_app.domain.diagram.bpmn_mermaid_mapping import build_bpmn_catalog_for_api
from tm_app.domain.diagram.flowchart_validation_service import FlowchartValidationService
from tm_app.domain.diagram.flowchart_v1 import (
    FlowchartValidationError,
    empty_escopo,
    empty_flowchart,
    empty_overlay,
    macro_node_ids,
    validate_escopo,
    validate_flowchart_v1,
    validate_overlay_v1,
)
from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository
from tm_app.infrastructure.persistence.repositories.instancia_diagram_escopo_repository import (
    InstanciaDiagramEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_diagram_repository import (
    ProcessoDiagramRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_repository import ProcessoRepository
from tm_app.infrastructure.persistence.repositories.revisao_diagram_overlay_repository import (
    RevisaoDiagramOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transformometro", tags=["Transformômetro — diagramas"])

_mermaid = DiagramMermaidExportService()
_merge = RevisaoDiagramMergeService(_mermaid)
_composition = DiagramaCompositionService()
_validator = FlowchartValidationService()
_bpmn_xml = FlowchartBpmnXmlService()


class FlowchartBody(BaseModel):
    conteudo: dict[str, Any] = Field(default_factory=dict)


class EscopoBody(BaseModel):
    node_ids: list[str] = Field(default_factory=list)
    inherit_all: bool = True
    include_boundary_edges: bool = False


class OverlayBody(BaseModel):
    conteudo: dict[str, Any] = Field(default_factory=dict)


class BpmnImportBody(BaseModel):
    xml: str = Field(min_length=1)


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
        payload=payload,
    )


def _macro_response(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        empty = empty_flowchart()
        return {
            "processo_id": None,
            "conteudo": empty,
            "mermaid": _mermaid.flowchart_to_mermaid(empty),
            "empty": True,
        }
    conteudo = row.get("conteudo") or empty_flowchart()
    mermaid = row.get("mermaid_cached") or _mermaid.flowchart_to_mermaid(conteudo)
    return {
        "processo_id": str(row.get("processo_id")),
        "conteudo": conteudo,
        "mermaid": mermaid,
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
        "include_boundary_edges": bool(row.get("include_boundary_edges", False)),
        "empty": False,
        "updated_at": row.get("updated_at"),
    }


def _overlay_response(row: dict[str, Any] | None, revisao_id: str) -> dict[str, Any]:
    if not row:
        empty = empty_overlay()
        return {
            "revisao_id": revisao_id,
            "conteudo": empty,
            "mermaid": None,
            "empty": True,
        }
    conteudo = row.get("conteudo") or empty_overlay()
    return {
        "revisao_id": revisao_id,
        "conteudo": conteudo,
        "mermaid": row.get("mermaid_cached"),
        "empty": RevisaoDiagramMergeService.overlay_is_empty(conteudo),
        "updated_at": row.get("updated_at"),
    }


@router.get("/diagrama/catalogo")
def get_diagrama_catalogo():
    return ok(build_bpmn_catalog_for_api(), "Catálogo BPMN + convenções Mermaid do Transformômetro.")


@router.get("/processos/{processo_id}/diagrama")
def get_processo_diagrama(processo_id: str):
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    row = ProcessoDiagramRepository().get(processo_id)
    return ok(_macro_response(row), "Diagrama macro do processo.")


@router.get("/processos/{processo_id}/diagrama/composed")
def get_processo_diagrama_composed(
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
    return ok(composed, "Diagrama composto na data informada.")


@router.put("/processos/{processo_id}/diagrama")
def put_processo_diagrama(processo_id: str, body: FlowchartBody, request: Request):
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    try:
        conteudo = validate_flowchart_v1(body.conteudo)
    except FlowchartValidationError as exc:
        return fail(str(exc), 400)

    mermaid = _mermaid.flowchart_to_mermaid(conteudo)
    row = ProcessoDiagramRepository().upsert(
        processo_id,
        conteudo=conteudo,
        mermaid_cached=mermaid,
    )
    _audit(request, "processo", processo_id, "diagram.macro.updated", {"nodes": len(conteudo.get("nodes", []))})
    payload = _macro_response(row)
    payload["processo_id"] = processo_id
    return ok(payload, "Diagrama macro salvo.")


@router.post("/processos/{processo_id}/diagrama/validacao")
def post_processo_diagrama_validacao(processo_id: str, body: FlowchartBody):
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    try:
        conteudo = validate_flowchart_v1(body.conteudo)
    except FlowchartValidationError as exc:
        return fail(str(exc), 400)
    report = _validator.validate(conteudo)
    return ok(report, "Validação estrutural e simulação do diagrama.")


@router.get("/processos/{processo_id}/diagrama/bpmn.xml")
def get_processo_diagrama_bpmn_xml(processo_id: str):
    processo = ProcessoRepository().get(processo_id)
    if not processo:
        return fail("Processo não encontrado.", 404)
    row = ProcessoDiagramRepository().get(processo_id)
    conteudo = (row or {}).get("conteudo") or empty_flowchart()
    try:
        xml_text = _bpmn_xml.export_xml(
            conteudo,
            process_name=str(processo.get("nome_processo") or "Processo"),
        )
    except FlowchartValidationError as exc:
        return fail(str(exc), 400)
    return ok({"xml": xml_text}, "Export BPMN 2.0 XML.")


@router.put("/processos/{processo_id}/diagrama/bpmn.xml")
def put_processo_diagrama_bpmn_xml(processo_id: str, body: BpmnImportBody, request: Request):
    if not ProcessoRepository().get(processo_id):
        return fail("Processo não encontrado.", 404)
    try:
        conteudo = _bpmn_xml.import_xml(body.xml)
    except FlowchartValidationError as exc:
        return fail(str(exc), 400)

    mermaid = _mermaid.flowchart_to_mermaid(conteudo)
    row = ProcessoDiagramRepository().upsert(
        processo_id,
        conteudo=conteudo,
        mermaid_cached=mermaid,
    )
    _audit(
        request,
        "processo",
        processo_id,
        "diagram.macro.imported_bpmn",
        {"nodes": len(conteudo.get("nodes", []))},
    )
    payload = _macro_response(row)
    payload["processo_id"] = processo_id
    return ok(payload, "Diagrama importado de BPMN 2.0 XML.")


@router.get("/instancias/{instancia_id}/diagrama-escopo")
def get_instancia_diagrama_escopo(instancia_id: str):
    instancia = ProcessoInstanciaRepository().get(instancia_id)
    if not instancia:
        return fail("Instância não encontrada.", 404)
    row = InstanciaDiagramEscopoRepository().get(instancia_id)
    return ok(_escopo_response(row, instancia_id), "Escopo de diagrama da instância.")


@router.put("/instancias/{instancia_id}/diagrama-escopo")
def put_instancia_diagrama_escopo(instancia_id: str, body: EscopoBody, request: Request):
    instancia = ProcessoInstanciaRepository().get(instancia_id)
    if not instancia:
        return fail("Instância não encontrada.", 404)

    macro_row = ProcessoDiagramRepository().get(str(instancia["processo_id"]))
    macro = (macro_row or {}).get("conteudo") or empty_flowchart()
    try:
        escopo = validate_escopo(
            body.model_dump(),
            macro_node_ids=macro_node_ids(macro),
        )
    except FlowchartValidationError as exc:
        return fail(str(exc), 400)

    row = InstanciaDiagramEscopoRepository().upsert(
        instancia_id,
        node_ids=escopo["node_ids"],
        inherit_all=escopo["inherit_all"],
        include_boundary_edges=escopo["include_boundary_edges"],
    )
    _audit(
        request,
        "processo_instancia",
        instancia_id,
        "diagram.escopo.updated",
        {"inherit_all": escopo["inherit_all"], "nodes": len(escopo["node_ids"])},
    )
    return ok(_escopo_response(row, instancia_id), "Escopo de diagrama salvo.")


def _load_merge_context(
    revisao_id: str,
) -> tuple[
    dict[str, Any] | None,
    dict[str, Any] | None,
    dict[str, Any] | None,
    dict[str, Any] | None,
]:
    revisao = RevisaoRepository().get(revisao_id)
    if not revisao:
        return None, None, None, None

    processo_id = str(revisao["processo_id"])
    instancia_id = str(revisao.get("instancia_id") or "")

    macro_row = ProcessoDiagramRepository().get(processo_id)
    macro = (macro_row or {}).get("conteudo") if macro_row else None

    escopo_row = InstanciaDiagramEscopoRepository().get(instancia_id) if instancia_id else None
    if escopo_row:
        escopo = {
            "node_ids": escopo_row.get("node_ids") or [],
            "inherit_all": bool(escopo_row.get("inherit_all", True)),
            "include_boundary_edges": bool(escopo_row.get("include_boundary_edges", False)),
        }
    else:
        escopo = empty_escopo()

    overlay_row = RevisaoDiagramOverlayRepository().get(revisao_id)
    overlay = (overlay_row or {}).get("conteudo") if overlay_row else None
    return revisao, macro, escopo, overlay


@router.get("/revisoes/{revisao_id}/diagrama")
def get_revisao_diagrama_merged(revisao_id: str):
    revisao, macro, escopo, overlay = _load_merge_context(revisao_id)
    if not revisao:
        return fail("Revisão não encontrada.", 404)

    reference_overlay = None
    reference_meta = None
    baseline_revisao = RevisaoRepository().find_reference_for_revisao(
        revisao_id,
        revisao_row=revisao,
    )
    if baseline_revisao:
        _, _, _, reference_overlay = _load_merge_context(str(baseline_revisao["revisao_id"]))
        reference_meta = {
            "revisao_id": str(baseline_revisao["revisao_id"]),
            "versao_revisao": baseline_revisao.get("versao_revisao"),
            "cenario_tipo": baseline_revisao.get("cenario_tipo"),
        }

    view = _merge.build_revisao_view(
        macro=macro,
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
        "Diagrama mesclado da revisão.",
    )


@router.get("/revisoes/{revisao_id}/diagrama/overlay")
def get_revisao_diagrama_overlay(revisao_id: str):
    if not RevisaoRepository().get(revisao_id):
        return fail("Revisão não encontrada.", 404)
    row = RevisaoDiagramOverlayRepository().get(revisao_id)
    return ok(_overlay_response(row, revisao_id), "Overlay da revisão.")


@router.put("/revisoes/{revisao_id}/diagrama/overlay")
def put_revisao_diagrama_overlay(revisao_id: str, body: OverlayBody, request: Request):
    revisao = RevisaoRepository().get(revisao_id)
    if not revisao:
        return fail("Revisão não encontrada.", 404)

    try:
        overlay = validate_overlay_v1(body.conteudo)
    except FlowchartValidationError as exc:
        return fail(str(exc), 400)

    _, macro, escopo, _ = _load_merge_context(revisao_id)
    merged = _merge.merge(macro=macro, escopo=escopo, overlay=overlay)
    mermaid = merged["mermaid"]

    row = RevisaoDiagramOverlayRepository().upsert(
        revisao_id,
        conteudo=overlay,
        mermaid_cached=mermaid,
    )
    _audit(
        request,
        "revisao",
        revisao_id,
        "diagram.overlay.updated",
        {"overrides": len(overlay.get("node_overrides") or {})},
    )
    payload = _overlay_response(row, revisao_id)
    payload["mermaid"] = mermaid
    payload["merged_preview"] = merged["flowchart"]
    return ok(payload, "Overlay da revisão salvo.")


@router.get("/revisoes/{revisao_id}/diagrama/mermaid")
def get_revisao_diagrama_mermaid(revisao_id: str):
    revisao, macro, escopo, overlay = _load_merge_context(revisao_id)
    if not revisao:
        return fail("Revisão não encontrada.", 404)
    merged = _merge.merge(macro=macro, escopo=escopo, overlay=overlay)
    return ok({"mermaid": merged["mermaid"]}, "Mermaid derivado.")
