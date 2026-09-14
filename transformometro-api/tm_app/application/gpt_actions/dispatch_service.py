"""Dispatch Custom GPT Actions to existing Transformômetro repositories/services."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request

from tm_app.application.gpt_actions.entities import (
    GptAnalysisView,
    GptEntity,
    GptMeetingMinuteWorkflow,
    entity_supports,
    parse_entity,
)
from tm_app.application.gpt_actions.registration_guide import build_registration_guide
from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
from tm_app.application.services.dashboard_snapshot_read_service import (
    DashboardSnapshotReadService,
)
from tm_app.application.services.instance_duplicate_service import (
    InstanciaDuplicateService,
    InstanciaNotFoundError,
)
from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.application.services.process_duplicate_service import (
    ProcessoDuplicateService,
    ProcessoNotFoundError,
)
from tm_app.application.services.revision_duplicate_service import (
    RevisaoDuplicateService,
    RevisaoNotFoundError,
)
from tm_app.application.services.revision_impact_effort_matrix_service import (
    RevisaoImpactEffortMatrixService,
)
from tm_app.application.services.transformometro_realtime_notify import (
    notify_catalog_updated,
    notify_from_audit,
)
from tm_app.core.auth_actor import actor_from_request, client_id_from_request
from tm_app.core.catalogs import (
    BASE_COMPETENCIA_RECURSO,
    BENEFICIO_CALCULO_CATEGORIA,
    CATEGORIAS,
    CENARIO_TIPO,
    CRITERIO_RATEIO,
    ESCOPO_RECURSO,
    FILIAIS,
    RECORRENCIAS,
    STATUS_FILIAL,
    STATUS_PROCESSO,
    STATUS_RECURSO,
    STATUS_SETOR,
    TIPO_CUSTO_RECURSO,
    TIPO_INVESTIMENTO,
    assert_in,
    options_payload,
)
from tm_app.core.errors import format_api_error
from tm_app.core.serialize import row_to_json, rows_to_json
from tm_app.domain.services.branch_catalog_service import assert_filial_ativa
from tm_app.domain.services.process_instance_service import ProcessoInstanciaDomainError
from tm_app.domain.services.process_scope_service import ProcessoEscopoDomainError
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository
from tm_app.infrastructure.persistence.repositories.branch_repository import FilialRepository
from tm_app.infrastructure.persistence.repositories.department_repository import (
    SetorRepository,
)
from tm_app.infrastructure.persistence.repositories.instance_scope_decomposition_repository import (
    InstanciaDecomposicaoEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.instance_scope_diagram_repository import (
    InstanciaDiagramEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.investment_repository import (
    InvestimentoRepository,
)
from tm_app.infrastructure.persistence.repositories.measurement_repository import (
    MedicaoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_decomposition_repository import (
    ProcessoDecomposicaoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_diagram_repository import (
    ProcessoDiagramRepository,
)
from tm_app.infrastructure.persistence.repositories.process_instance_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_scope_repository import (
    ProcessoEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.resource_cost_repository import (
    RecursoCustoRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_decomposition_overlay_repository import (
    RevisaoDecomposicaoOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_diagram_overlay_repository import (
    RevisaoDiagramOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import (
    RevisaoRepository,
)
from tm_app.infrastructure.persistence.repositories.shared_resource_repository import (
    RecursoRepository,
    VinculoRepository,
)
from tm_app.application.services.branch_access_scope_service import FilialAccessScopeService
from tm_app.application.services.dashboard_recalc_hook_service import DashboardRecalcHookService
from tm_app.application.services.process_setup_stats_service import ProcessoSetupStatsService
from tm_app.application.services.process_write_service import (
    ProcessWriteError,
    ProcessWriteService,
    RevisionActivationService,
)
from tm_app.interface.http.branch_access_http import (
    check_dashboard_filial_access,
    check_instancia_view_access,
    check_manage_filial_access,
    check_processo_view_access,
    check_view_filial_access,
    filter_rows_for_access,
    require_transformometro_view_access,
    require_unrestricted_catalog_admin,
    resolve_access_scope,
)
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
    RevisaoBody,
    RevisaoDuplicateBody,
    RevisaoMatrizImpactoBody,
    SetorBody,
    SetorUpdateBody,
    VinculoBody,
    VinculoUpdateBody,
)

logger = logging.getLogger(__name__)

_PERSONAL_DATA_FIELDS = frozenset(
    {
        "gestor_responsavel",
        "aprovado_por_email",
        "email",
        "user_email",
        "fornecedor",
    }
)


class GptActionsError(Exception):
    def __init__(self, message: str, status_code: int = 400, data: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data


class GptActionsDispatchService:
    """Application facade used by `/transformometro/gpt-actions/v1/*`."""

    def __init__(self) -> None:
        self._snapshot = DashboardSnapshotReadService()
        self._recalc_hook = DashboardRecalcHookService()
        self._minutes = MeetingMinutesService()

    # --- helpers ---------------------------------------------------------

    def _mask_personal_data(self, payload: dict) -> dict:
        if not payload:
            return payload
        masked = {}
        for key, value in payload.items():
            if key in _PERSONAL_DATA_FIELDS and isinstance(value, str) and value:
                masked[key] = value[:2] + "***"
            else:
                masked[key] = value
        return masked

    def _audit(
        self,
        request: Request,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: dict,
    ) -> None:
        user_id, user_email, user_name = actor_from_request(request)
        try:
            AuditRepository().log(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                user_id=user_id,
                user_email=user_email,
                user_name=user_name,
                payload=self._mask_personal_data(payload),
            )
        except Exception as exc:
            logger.warning(
                "gpt_audit_log_failed entity=%s id=%s action=%s err=%s",
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

    def _active_filial_codigos(self) -> set[str]:
        try:
            active = FilialRepository().list_active_codigos()
        except PluginsRepositoryError:
            active = set()
        return active or set(FILIAIS.keys())

    def _raise_http_err(self, response) -> None:
        """Convert branch_access JSONResponse into GptActionsError."""
        if response is None:
            return
        body = getattr(response, "body", None)
        message = "Acesso negado."
        status = getattr(response, "status_code", 403) or 403
        if body:
            try:
                import json

                parsed = json.loads(body.decode("utf-8") if isinstance(body, bytes) else body)
                message = str(parsed.get("message") or message)
            except Exception:
                pass
        raise GptActionsError(message, status)

    def _require_capability(self, entity: GptEntity, capability: str) -> None:
        if not entity_supports(entity, capability):
            raise GptActionsError(
                f"Entity '{entity.value}' does not support '{capability}'.",
                400,
            )

    def _data(self, payload: dict | None) -> dict:
        if not payload:
            return {}
        if "data" in payload and isinstance(payload["data"], dict):
            return dict(payload["data"])
        return dict(payload)

    # --- catalog / analysis ----------------------------------------------

    def get_catalog(self, request: Request) -> dict[str, Any]:
        self._raise_http_err(require_transformometro_view_access(request))
        scope = resolve_access_scope(request)
        try:
            filiais = FilialRepository().list_for_options() or []
        except Exception:
            filiais = [{"id": k, "label": v} for k, v in FILIAIS.items()]
        filiais = FilialAccessScopeService().filter_filiais_options(filiais, scope)
        try:
            setores = SetorRepository().list_for_options()
        except Exception:
            setores = []
        if not scope.is_unrestricted:
            allowed = scope.allowed_codigos
            setores = [
                item
                for item in setores
                if not item.get("filiais")
                or any(str(code) in allowed for code in item.get("filiais") or [])
            ]
        payload = options_payload(setores, filiais)
        payload["access_scope"] = scope.meta()
        payload["entities"] = [e.value for e in GptEntity]
        payload["registration_guide"] = build_registration_guide()
        try:
            repo = ProcessoRepository()
            payload["familias_processo"] = repo.list_distinct_tag_values("familia_processo")
            payload["agrupadores_ferramenta"] = repo.list_distinct_tag_values(
                "agrupador_ferramenta"
            )
        except Exception:
            payload.setdefault("familias_processo", [])
            payload.setdefault("agrupadores_ferramenta", [])
        return payload

    def analyze(
        self,
        request: Request,
        *,
        view: str,
        filial_id: str | None = None,
        setor_id: str | None = None,
        processo_id: str | None = None,
        revisao_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        self._raise_http_err(require_transformometro_view_access(request))
        try:
            analysis_view = GptAnalysisView(str(view or "").strip())
        except ValueError as exc:
            raise GptActionsError(
                f"Invalid view '{view}'. Allowed: {[v.value for v in GptAnalysisView]}",
                400,
            ) from exc

        if analysis_view != GptAnalysisView.META:
            self._raise_http_err(
                check_dashboard_filial_access(
                    request,
                    view=None,
                    filial_id=filial_id,
                    setor_id=setor_id,
                )
            )

        if analysis_view == GptAnalysisView.META:
            return self._snapshot.meta()
        if analysis_view == GptAnalysisView.SUMMARY:
            return self._snapshot.resumo(
                filial_id=filial_id,
                setor_id=setor_id,
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
            )
        if analysis_view == GptAnalysisView.PROCESSES:
            return self._snapshot.processos(
                filial_id=filial_id,
                setor_id=setor_id,
                familia_processo=familia_processo,
                processo_id=processo_id,
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
                limit=limit or 200,
            )
        if analysis_view == GptAnalysisView.INSTANCES:
            return self._snapshot.instancias(
                filial_id=filial_id,
                setor_id=setor_id,
                limit=limit or 500,
            )
        return self._snapshot.linhas(
            processo_id=processo_id,
            revisao_id=revisao_id,
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            limit=limit or 500,
        )

    # --- records CRUD ----------------------------------------------------

    def search_records(
        self,
        request: Request,
        entity_value: str,
        *,
        parent_id: str | None = None,
        instance_id: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        status: str | None = None,
        familia_processo: str | None = None,
        q: str | None = None,
        unit_code: str | None = None,
    ) -> dict[str, Any]:
        entity = parse_entity(entity_value)
        self._require_capability(entity, "search")

        if entity == GptEntity.BRANCH:
            rows = FilialRepository().list(include_inactive=True)
            return {"total": len(rows), "items": rows_to_json(rows)}

        if entity == GptEntity.DEPARTMENT:
            rows = SetorRepository().list(filial_id=filial_id)
            return {"total": len(rows), "items": rows_to_json(rows)}

        if entity == GptEntity.PROCESS:
            if filial_id:
                self._raise_http_err(check_view_filial_access(request, filial_id))
            rows = ProcessoRepository().list(
                filial_id=filial_id,
                setor_id=setor_id,
                status_processo=status,
                familia_processo=familia_processo,
                q=q,
            )
            rows = filter_rows_for_access(request, rows)
            rows = ProcessoSetupStatsService().enrich_processos(rows)
            return {"total": len(rows), "items": rows_to_json(rows)}

        if entity == GptEntity.INSTANCE:
            if not parent_id:
                raise GptActionsError(
                    "parent_id (processo_id) is required to list instances.", 400
                )
            self._raise_http_err(check_processo_view_access(request, parent_id))
            rows = ProcessoInstanciaRepository().list_by_processo(parent_id)
            rows = filter_rows_for_access(request, rows, codigo_key="codigo_filial")
            return {"total": len(rows), "items": rows_to_json(rows)}

        if entity == GptEntity.REVISION:
            instancia_id = (instance_id or "").strip() or None
            if instancia_id:
                self._raise_http_err(check_instancia_view_access(request, instancia_id))
                rows = RevisaoRepository().list_by_instancia(instancia_id)
                return {"total": len(rows), "items": rows_to_json(rows)}
            if not parent_id:
                raise GptActionsError(
                    "parent_id (processo_id) or instance_id is required to list revisions.",
                    400,
                )
            self._raise_http_err(check_processo_view_access(request, parent_id))
            rows = RevisaoRepository().list_by_processo(parent_id)
            return {"total": len(rows), "items": rows_to_json(rows)}

        if entity == GptEntity.MEASUREMENT:
            if not parent_id:
                raise GptActionsError(
                    "parent_id (revisao_id) is required to list measurements.", 400
                )
            row = MedicaoRepository().get_by_revisao(parent_id)
            items = [row_to_json(row)] if row else []
            return {"total": len(items), "items": items}

        if entity == GptEntity.INVESTMENT:
            if not parent_id:
                raise GptActionsError(
                    "parent_id (revisao_id) is required to list investments.", 400
                )
            rows = InvestimentoRepository().list_by_revisao(parent_id)
            return {"total": len(rows), "items": rows_to_json(rows)}

        if entity == GptEntity.SHARED_RESOURCE:
            rows = RecursoRepository().list()
            return {"total": len(rows), "items": rows_to_json(rows)}

        if entity == GptEntity.RESOURCE_COST:
            if not parent_id:
                raise GptActionsError(
                    "parent_id (recurso_id) is required to list resource costs.", 400
                )
            rows = RecursoCustoRepository().list_by_recurso(parent_id)
            return {"total": len(rows), "items": rows_to_json(rows)}

        if entity == GptEntity.RESOURCE_LINK:
            if not parent_id:
                raise GptActionsError(
                    "parent_id (revisao_id or recurso_id) is required.", 400
                )
            # Prefer revisao links; fall back to recurso.
            rows = VinculoRepository().list_by_revisao(parent_id)
            if not rows:
                rows = VinculoRepository().list_by_recurso(parent_id)
            return {"total": len(rows), "items": rows_to_json(rows)}

        if entity == GptEntity.MEETING_MINUTE:
            try:
                return self._minutes.list_minutes(
                    request.state.user,
                    {
                        "unit_code": unit_code,
                        "status": status,
                        "q": q,
                        "limit": 50,
                        "offset": 0,
                    },
                )
            except PermissionError as exc:
                raise GptActionsError(str(exc), 403) from exc

        raise GptActionsError(f"Search not implemented for {entity.value}.", 400)

    def get_record(self, request: Request, entity_value: str, record_id: str) -> dict[str, Any]:
        entity = parse_entity(entity_value)
        self._require_capability(entity, "get")
        rid = str(record_id)

        if entity == GptEntity.BRANCH:
            row = FilialRepository().get(rid)
            if not row:
                raise GptActionsError("Unidade não encontrada.", 404)
            return row_to_json(row)

        if entity == GptEntity.DEPARTMENT:
            row = SetorRepository().get(rid)
            if not row:
                raise GptActionsError("Setor não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.PROCESS:
            self._raise_http_err(check_processo_view_access(request, rid))
            row = ProcessoRepository().get(rid)
            if not row:
                raise GptActionsError("Processo não encontrado.", 404)
            enriched = ProcessoSetupStatsService().enrich_processos([row])
            return row_to_json(enriched[0])

        if entity == GptEntity.INSTANCE:
            self._raise_http_err(check_instancia_view_access(request, rid))
            row = ProcessoInstanciaRepository().get(rid)
            if not row:
                raise GptActionsError("Instância não encontrada.", 404)
            return row_to_json(row)

        if entity == GptEntity.REVISION:
            row = RevisaoRepository().get(rid)
            if not row:
                raise GptActionsError("Revisão não encontrada.", 404)
            processo_id = str(row.get("processo_id") or "")
            if processo_id:
                self._raise_http_err(check_processo_view_access(request, processo_id))
            return row_to_json(row)

        if entity == GptEntity.MEASUREMENT:
            row = MedicaoRepository().get_by_revisao(rid)
            if not row:
                raise GptActionsError("Medição não encontrada.", 404)
            return row_to_json(row)

        if entity == GptEntity.INVESTMENT:
            row = InvestimentoRepository().get(rid)
            if not row:
                raise GptActionsError("Investimento não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.SHARED_RESOURCE:
            row = RecursoRepository().get(rid)
            if not row:
                raise GptActionsError("Recurso não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.RESOURCE_COST:
            row = RecursoCustoRepository().get(rid)
            if not row:
                raise GptActionsError("Custo de recurso não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.RESOURCE_LINK:
            row = VinculoRepository().get(rid)
            if not row:
                raise GptActionsError("Vínculo não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.MEETING_MINUTE:
            try:
                return self._minutes.get_detail(request.state.user, rid)
            except PermissionError as exc:
                raise GptActionsError(str(exc), 403) from exc
            except LookupError as exc:
                raise GptActionsError(str(exc), 404) from exc

        if entity == GptEntity.DECOMPOSITION_TREE:
            self._raise_http_err(check_processo_view_access(request, rid))
            row = ProcessoDecomposicaoRepository().get(rid)
            if not row:
                raise GptActionsError("Decomposição não encontrada.", 404)
            return row_to_json(row)

        if entity == GptEntity.INSTANCE_DECOMPOSITION_SCOPE:
            self._raise_http_err(check_instancia_view_access(request, rid))
            row = InstanciaDecomposicaoEscopoRepository().get(rid)
            if not row:
                raise GptActionsError("Escopo de decomposição não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.REVISION_DECOMPOSITION_OVERLAY:
            row = RevisaoDecomposicaoOverlayRepository().get(rid)
            if not row:
                raise GptActionsError("Overlay de decomposição não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.PROCESS_DIAGRAM:
            self._raise_http_err(check_processo_view_access(request, rid))
            row = ProcessoDiagramRepository().get(rid)
            if not row:
                raise GptActionsError("Diagrama não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.INSTANCE_DIAGRAM_SCOPE:
            self._raise_http_err(check_instancia_view_access(request, rid))
            row = InstanciaDiagramEscopoRepository().get(rid)
            if not row:
                raise GptActionsError("Escopo de diagrama não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.REVISION_DIAGRAM_OVERLAY:
            row = RevisaoDiagramOverlayRepository().get(rid)
            if not row:
                raise GptActionsError("Overlay de diagrama não encontrado.", 404)
            return row_to_json(row)

        if entity == GptEntity.IMPACT_EFFORT_MATRIX:
            data = RevisaoImpactEffortMatrixService().build_for_revisao(rid)
            if not data:
                raise GptActionsError("Revisão não encontrada.", 404)
            return data

        raise GptActionsError(f"Get not implemented for {entity.value}.", 400)

    def create_record(
        self, request: Request, entity_value: str, payload: dict | None
    ) -> tuple[dict[str, Any], str, int]:
        entity = parse_entity(entity_value)
        self._require_capability(entity, "create")
        data = self._data(payload)

        if entity == GptEntity.BRANCH:
            self._raise_http_err(require_unrestricted_catalog_admin(request))
            body = FilialBody.model_validate(data)
            assert_in(body.status_filial, STATUS_FILIAL, "status_filial")
            row = FilialRepository().create(body.model_dump())
            fid = str(row["filial_id"])
            self._audit(request, "filial", fid, "create", body.model_dump())
            return row_to_json(row), "Unidade criada.", 201

        if entity == GptEntity.DEPARTMENT:
            body = SetorBody.model_validate(data)
            assert_in(body.status_setor, STATUS_SETOR, "status_setor")
            for filial_id in body.filiais:
                assert_filial_ativa(filial_id, self._active_filial_codigos())
            row = SetorRepository().create(body.model_dump())
            sid = str(row["setor_id"])
            self._audit(request, "setor", sid, "create", body.model_dump())
            return row_to_json(row), "Setor criado.", 201

        if entity == GptEntity.PROCESS:
            return self._create_processo(request, data)

        if entity == GptEntity.INSTANCE:
            processo_id = str(data.get("processo_id") or "").strip()
            if not processo_id:
                raise GptActionsError("data.processo_id is required.", 400)
            body = InstanciaBody.model_validate(
                {k: v for k, v in data.items() if k != "processo_id"}
            )
            return self._create_instancia(request, processo_id, body)

        if entity == GptEntity.REVISION:
            body = RevisaoBody.model_validate(data)
            assert_in(body.cenario_tipo, CENARIO_TIPO, "cenario_tipo")
            assert_in(
                body.beneficio_calculo_categoria,
                BENEFICIO_CALCULO_CATEGORIA,
                "beneficio_calculo_categoria",
            )
            row = RevisaoRepository().create(body.model_dump())
            rid = str(row["revisao_id"])
            self._audit(request, "revisao", rid, "create", body.model_dump())
            self._recalc_hook.after_revisao(rid, processo_id=str(body.processo_id))
            return row_to_json(row), "Revisão criada.", 201

        if entity == GptEntity.MEASUREMENT:
            body = MedicaoBody.model_validate(data)
            row = MedicaoRepository().upsert(body.model_dump())
            mid = str(row["medicao_id"])
            self._audit(request, "medicao", mid, "upsert", body.model_dump())
            self._recalc_hook.after_revisao(str(body.revisao_id))
            return row_to_json(row), "Medição salva.", 200

        if entity == GptEntity.INVESTMENT:
            body = InvestimentoBody.model_validate(data)
            assert_in(body.tipo_investimento, TIPO_INVESTIMENTO, "tipo_investimento")
            assert_in(body.recorrencia, RECORRENCIAS, "recorrencia")
            if body.categoria_investimento:
                assert_in(body.categoria_investimento, CATEGORIAS, "categoria_investimento")
            row = InvestimentoRepository().create(body.model_dump())
            iid = str(row["investimento_id"])
            self._audit(request, "investimento", iid, "create", body.model_dump())
            self._recalc_hook.after_revisao(str(body.revisao_id))
            return row_to_json(row), "Investimento criado.", 201

        if entity == GptEntity.SHARED_RESOURCE:
            body = RecursoBody.model_validate(data)
            self._validate_recurso(body)
            row = RecursoRepository().create(body.model_dump())
            rid = str(row["recurso_compartilhado_id"])
            self._audit(request, "recurso", rid, "create", body.model_dump())
            self._recalc_hook.after_global_resource_change()
            return row_to_json(row), "Recurso criado.", 201

        if entity == GptEntity.RESOURCE_COST:
            recurso_id = str(data.get("recurso_compartilhado_id") or data.get("recurso_id") or "").strip()
            if not recurso_id:
                raise GptActionsError("data.recurso_compartilhado_id is required.", 400)
            if not RecursoRepository().get(recurso_id):
                raise GptActionsError("Recurso não encontrado.", 404)
            body = RecursoCustoBody.model_validate(
                {
                    k: v
                    for k, v in data.items()
                    if k not in {"recurso_compartilhado_id", "recurso_id"}
                }
            )
            row = RecursoCustoRepository().create(
                {"recurso_compartilhado_id": recurso_id, **body.model_dump()}
            )
            cid = str(row["recurso_custo_id"])
            self._audit(
                request,
                "recurso_custo",
                cid,
                "create",
                {**body.model_dump(), "recurso_compartilhado_id": recurso_id},
            )
            self._recalc_hook.after_global_resource_change()
            return row_to_json(row), "Vigência de custo registrada.", 201

        if entity == GptEntity.RESOURCE_LINK:
            body = VinculoBody.model_validate(data)
            row = VinculoRepository().create(body.model_dump())
            vid = str(row["vinculo_id"])
            self._audit(request, "vinculo", vid, "create", body.model_dump())
            self._recalc_hook.after_revisao(str(body.revisao_id))
            return row_to_json(row), "Vínculo criado.", 201

        if entity == GptEntity.MEETING_MINUTE:
            try:
                row = self._minutes.create(request.state.user, data)
            except PermissionError as exc:
                raise GptActionsError(str(exc), 403) from exc
            except ValueError as exc:
                raise GptActionsError(str(exc), 400) from exc
            return row, "Ata criada.", 201

        if entity in {
            GptEntity.DECOMPOSITION_TREE,
            GptEntity.INSTANCE_DECOMPOSITION_SCOPE,
            GptEntity.REVISION_DECOMPOSITION_OVERLAY,
            GptEntity.PROCESS_DIAGRAM,
            GptEntity.INSTANCE_DIAGRAM_SCOPE,
            GptEntity.REVISION_DIAGRAM_OVERLAY,
        }:
            # create == upsert for document entities
            parent_id = self._document_parent_id(entity, data)
            return self._upsert_document(request, entity, parent_id, data)

        raise GptActionsError(f"Create not implemented for {entity.value}.", 400)

    def update_record(
        self,
        request: Request,
        entity_value: str,
        record_id: str,
        payload: dict | None,
    ) -> tuple[dict[str, Any], str]:
        entity = parse_entity(entity_value)
        self._require_capability(entity, "update")
        data = self._data(payload)
        rid = str(record_id)

        if entity == GptEntity.BRANCH:
            self._raise_http_err(require_unrestricted_catalog_admin(request))
            body = FilialUpdateBody.model_validate(data)
            assert_in(body.status_filial, STATUS_FILIAL, "status_filial")
            row = FilialRepository().update(rid, body.model_dump())
            if not row:
                raise GptActionsError("Unidade não encontrada.", 404)
            self._audit(request, "filial", str(row["filial_id"]), "update", body.model_dump())
            return row_to_json(row), "Unidade atualizada."

        if entity == GptEntity.DEPARTMENT:
            body = SetorUpdateBody.model_validate(data)
            assert_in(body.status_setor, STATUS_SETOR, "status_setor")
            for filial_id in body.filiais:
                assert_filial_ativa(filial_id, self._active_filial_codigos())
            row = SetorRepository().update(rid, body.model_dump())
            if not row:
                raise GptActionsError("Setor não encontrado.", 404)
            self._audit(request, "setor", rid, "update", body.model_dump())
            return row_to_json(row), "Setor atualizado."

        if entity == GptEntity.PROCESS:
            return self._update_processo(request, rid, data)

        if entity == GptEntity.INSTANCE:
            return self._update_instancia(request, rid, data)

        if entity == GptEntity.REVISION:
            existing = RevisaoRepository().get(rid)
            if not existing:
                raise GptActionsError("Revisão não encontrada.", 404)
            body = RevisaoBody.model_validate(data)
            payload_dump = body.model_dump()
            confirm_vigencia = bool(payload_dump.pop("confirm_vigencia_change", False))
            has_medicao = MedicaoRepository().get_by_revisao(rid) is not None
            if has_medicao:
                old_inicio = str(existing.get("data_inicio_vigencia") or "")[:10]
                old_fim = str(existing.get("data_fim_vigencia") or "")[:10]
                new_inicio = str(body.data_inicio_vigencia or "")[:10]
                new_fim = str(body.data_fim_vigencia or "")[:10]
                if (old_inicio != new_inicio or old_fim != new_fim) and not confirm_vigencia:
                    raise GptActionsError(
                        "Alteração de vigência com medição existente exige "
                        "confirm_vigencia_change=true.",
                        400,
                    )
            assert_in(body.cenario_tipo, CENARIO_TIPO, "cenario_tipo")
            row = RevisaoRepository().update(rid, payload_dump)
            if not row:
                raise GptActionsError("Revisão não encontrada.", 404)
            self._audit(request, "revisao", rid, "update", payload_dump)
            self._recalc_hook.after_revisao(rid, processo_id=str(row.get("processo_id") or ""))
            return row_to_json(row), "Revisão atualizada."

        if entity == GptEntity.MEASUREMENT:
            body = MedicaoBody.model_validate({**data, "revisao_id": data.get("revisao_id") or rid})
            row = MedicaoRepository().upsert(body.model_dump())
            mid = str(row["medicao_id"])
            self._audit(request, "medicao", mid, "upsert", body.model_dump())
            self._recalc_hook.after_revisao(str(body.revisao_id))
            return row_to_json(row), "Medição salva."

        if entity == GptEntity.INVESTMENT:
            body = InvestimentoUpdateBody.model_validate(data)
            assert_in(body.tipo_investimento, TIPO_INVESTIMENTO, "tipo_investimento")
            assert_in(body.recorrencia, RECORRENCIAS, "recorrencia")
            row = InvestimentoRepository().update(rid, body.model_dump())
            if not row:
                raise GptActionsError("Investimento não encontrado.", 404)
            self._audit(request, "investimento", rid, "update", body.model_dump())
            if row.get("revisao_id"):
                self._recalc_hook.after_revisao(str(row["revisao_id"]))
            return row_to_json(row), "Investimento atualizado."

        if entity == GptEntity.SHARED_RESOURCE:
            body = RecursoBody.model_validate(data)
            self._validate_recurso(body)
            row = RecursoRepository().update(rid, body.model_dump())
            if not row:
                raise GptActionsError("Recurso não encontrado.", 404)
            self._audit(request, "recurso", rid, "update", body.model_dump())
            self._recalc_hook.after_global_resource_change()
            return row_to_json(row), "Recurso atualizado."

        if entity == GptEntity.RESOURCE_COST:
            body = RecursoCustoBody.model_validate(data)
            row = RecursoCustoRepository().update(rid, body.model_dump())
            if not row:
                raise GptActionsError("Custo de recurso não encontrado.", 404)
            self._audit(request, "recurso_custo", rid, "update", body.model_dump())
            self._recalc_hook.after_global_resource_change()
            return row_to_json(row), "Custo atualizado."

        if entity == GptEntity.RESOURCE_LINK:
            body = VinculoUpdateBody.model_validate(data)
            row = VinculoRepository().update(rid, body.model_dump())
            if not row:
                raise GptActionsError("Vínculo não encontrado.", 404)
            self._audit(request, "vinculo", rid, "update", body.model_dump())
            if row.get("revisao_id"):
                self._recalc_hook.after_revisao(str(row["revisao_id"]))
            return row_to_json(row), "Vínculo atualizado."

        if entity == GptEntity.MEETING_MINUTE:
            try:
                row = self._minutes.update(request.state.user, rid, data)
            except PermissionError as exc:
                raise GptActionsError(str(exc), 403) from exc
            except LookupError as exc:
                raise GptActionsError(str(exc), 404) from exc
            except ValueError as exc:
                raise GptActionsError(str(exc), 400) from exc
            return row, "Ata atualizada."

        if entity == GptEntity.IMPACT_EFFORT_MATRIX:
            body = RevisaoMatrizImpactoBody.model_validate(data)
            user_id, user_email, user_name = actor_from_request(request)
            atualizado_por = user_name or user_email or user_id or "sistema"
            try:
                result = RevisaoImpactEffortMatrixService().save_for_revisao(
                    rid,
                    body.model_dump(),
                    atualizado_por=atualizado_por,
                )
            except ValueError as exc:
                raise GptActionsError(str(exc), 400) from exc
            if not result:
                raise GptActionsError("Revisão não encontrada.", 404)
            self._audit(request, "revisao", rid, "matrix.updated", body.model_dump())
            return result, "Matriz impacto×esforço atualizada."

        if entity in {
            GptEntity.DECOMPOSITION_TREE,
            GptEntity.INSTANCE_DECOMPOSITION_SCOPE,
            GptEntity.REVISION_DECOMPOSITION_OVERLAY,
            GptEntity.PROCESS_DIAGRAM,
            GptEntity.INSTANCE_DIAGRAM_SCOPE,
            GptEntity.REVISION_DIAGRAM_OVERLAY,
        }:
            data_out, message, _status = self._upsert_document(
                request, entity, rid, data
            )
            return data_out, message

        raise GptActionsError(f"Update not implemented for {entity.value}.", 400)

    def delete_record(
        self, request: Request, entity_value: str, record_id: str
    ) -> tuple[dict[str, Any], str]:
        entity = parse_entity(entity_value)
        self._require_capability(entity, "delete")
        rid = str(record_id)

        if entity == GptEntity.BRANCH:
            self._raise_http_err(require_unrestricted_catalog_admin(request))
            if not FilialRepository().soft_delete(rid):
                raise GptActionsError("Unidade não encontrada.", 404)
            self._audit(request, "filial", rid, "delete", {})
            return {"id": rid}, "Unidade removida."

        if entity == GptEntity.DEPARTMENT:
            if not SetorRepository().soft_delete(rid):
                raise GptActionsError("Setor não encontrado.", 404)
            self._audit(request, "setor", rid, "delete", {})
            return {"id": rid}, "Setor removido."

        if entity == GptEntity.PROCESS:
            self._raise_http_err(check_processo_view_access(request, rid))
            if not ProcessoRepository().soft_delete(rid):
                raise GptActionsError("Processo não encontrado.", 404)
            self._audit(request, "processo", rid, "delete", {})
            self._recalc_hook.after_processo(rid)
            return {"id": rid}, "Processo removido."

        if entity == GptEntity.INSTANCE:
            self._raise_http_err(check_instancia_view_access(request, rid))
            row = ProcessoInstanciaRepository().get(rid)
            if not row:
                raise GptActionsError("Instância não encontrada.", 404)
            codigo = str(row.get("codigo_filial") or row.get("filial_id") or "")
            if codigo and not row.get("todas_filiais_ativas"):
                self._raise_http_err(check_manage_filial_access(request, codigo))
            if not ProcessoInstanciaRepository().soft_delete(rid):
                raise GptActionsError("Instância não encontrada.", 404)
            self._audit(request, "processo_instancia", rid, "delete", {})
            return {"id": rid}, "Melhoria removida."

        if entity == GptEntity.REVISION:
            row = RevisaoRepository().get(rid)
            if not row:
                raise GptActionsError("Revisão não encontrada.", 404)
            if not RevisaoRepository().soft_delete(rid):
                raise GptActionsError("Revisão não encontrada.", 404)
            self._audit(request, "revisao", rid, "delete", {})
            self._recalc_hook.after_revisao(rid, processo_id=str(row.get("processo_id") or ""))
            return {"id": rid}, "Revisão removida."

        if entity == GptEntity.INVESTMENT:
            row = InvestimentoRepository().get(rid)
            if not row:
                raise GptActionsError("Investimento não encontrado.", 404)
            if not InvestimentoRepository().soft_delete(rid):
                raise GptActionsError("Investimento não encontrado.", 404)
            self._audit(request, "investimento", rid, "delete", {})
            if row.get("revisao_id"):
                self._recalc_hook.after_revisao(str(row["revisao_id"]))
            return {"id": rid}, "Investimento removido."

        if entity == GptEntity.SHARED_RESOURCE:
            if not RecursoRepository().soft_delete(rid):
                raise GptActionsError("Recurso não encontrado.", 404)
            self._audit(request, "recurso", rid, "delete", {})
            self._recalc_hook.after_global_resource_change()
            return {"id": rid}, "Recurso removido."

        if entity == GptEntity.RESOURCE_COST:
            if not RecursoCustoRepository().soft_delete(rid):
                raise GptActionsError("Custo de recurso não encontrado.", 404)
            self._audit(request, "recurso_custo", rid, "delete", {})
            self._recalc_hook.after_global_resource_change()
            return {"id": rid}, "Custo removido."

        if entity == GptEntity.RESOURCE_LINK:
            row = VinculoRepository().get(rid)
            if not row:
                raise GptActionsError("Vínculo não encontrado.", 404)
            if not VinculoRepository().soft_delete(rid):
                raise GptActionsError("Vínculo não encontrado.", 404)
            self._audit(request, "vinculo", rid, "delete", {})
            if row.get("revisao_id"):
                self._recalc_hook.after_revisao(str(row["revisao_id"]))
            return {"id": rid}, "Vínculo removido."

        if entity == GptEntity.MEETING_MINUTE:
            try:
                row = self._minutes.soft_delete(request.state.user, rid)
            except PermissionError as exc:
                raise GptActionsError(str(exc), 403) from exc
            except LookupError as exc:
                raise GptActionsError(str(exc), 404) from exc
            return row, "Ata removida."

        raise GptActionsError(f"Delete not implemented for {entity.value}.", 400)

    def duplicate_record(
        self,
        request: Request,
        entity_value: str,
        record_id: str,
        payload: dict | None = None,
    ) -> tuple[dict[str, Any], str, int]:
        entity = parse_entity(entity_value)
        self._require_capability(entity, "duplicate")
        data = self._data(payload)
        rid = str(record_id)

        if entity == GptEntity.PROCESS:
            body = ProcessoDuplicateBody.model_validate(data or {})
            try:
                result = ProcessoDuplicateService().duplicate(
                    rid, nome_processo=body.nome_processo
                )
            except ProcessoNotFoundError as exc:
                raise GptActionsError(str(exc), 404) from exc
            new_id = str(result["processo"]["processo_id"])
            self._audit(request, "processo", new_id, "duplicate", {"source_id": rid})
            self._recalc_hook.after_processo(new_id)
            return row_to_json(result["processo"]), "Processo duplicado.", 201

        if entity == GptEntity.INSTANCE:
            body = InstanciaDuplicateBody.model_validate(data)
            self._raise_http_err(check_manage_filial_access(request, body.filial_id))
            try:
                result = InstanciaDuplicateService().duplicate(
                    rid,
                    filial_id=body.filial_id,
                    setor_id=body.setor_id,
                    rotulo_instancia=body.rotulo_instancia,
                )
            except InstanciaNotFoundError as exc:
                raise GptActionsError(str(exc), 404) from exc
            new_id = str(result["instancia"]["instancia_id"])
            self._audit(request, "processo_instancia", new_id, "duplicate", {"source_id": rid})
            return (
                {
                    "instancia": row_to_json(result["instancia"]),
                    "processo_id": result.get("processo_id"),
                    "copiados": result.get("copiados"),
                },
                "Melhoria duplicada.",
                201,
            )

        if entity == GptEntity.REVISION:
            body = RevisaoDuplicateBody.model_validate(data or {})
            try:
                result = RevisaoDuplicateService().duplicate(
                    rid, versao_revisao=body.versao_revisao
                )
            except RevisaoNotFoundError as exc:
                raise GptActionsError(str(exc), 404) from exc
            new_id = str(result["revisao"]["revisao_id"])
            self._audit(request, "revisao", new_id, "duplicate", {"source_id": rid})
            self._recalc_hook.after_revisao(
                new_id, processo_id=str(result.get("processo_id") or "")
            )
            return row_to_json(result["revisao"]), "Revisão duplicada.", 201

        raise GptActionsError(f"Duplicate not implemented for {entity.value}.", 400)

    def activate_revision(self, request: Request, revisao_id: str) -> dict[str, Any]:
        row = RevisionActivationService().activate(str(revisao_id))
        if not row:
            raise GptActionsError("Revisão não encontrada.", 404)
        self._audit(
            request,
            "revisao",
            str(revisao_id),
            "activate",
            {
                "processo_id": str(row["processo_id"]),
                "instancia_id": str(row.get("instancia_id") or ""),
                "revisao_id": str(revisao_id),
            },
        )
        self._recalc_hook.after_revisao(
            str(revisao_id), processo_id=str(row["processo_id"])
        )
        return row_to_json(row)

    def recalculate_dashboard(
        self,
        request: Request,
        *,
        revisao_id: str | None = None,
        processo_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict[str, Any]:
        result = DashboardRecalcService().recalculate(
            revisao_id=revisao_id,
            processo_id=processo_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        user_id, _email, _name = actor_from_request(request)
        notify_catalog_updated(
            catalog_id="dashboard",
            action="recalcular",
            actor_user_id=user_id,
            actor_client_id=client_id_from_request(request),
            payload={
                "revisao_id": revisao_id,
                "processo_id": processo_id,
                "mode": result.get("mode"),
            },
        )
        result["observacao"] = (
            "Cache materializado atualizado. Os endpoints GET do dashboard não dependem deste passo."
        )
        return result

    def meeting_minute_workflow(
        self,
        request: Request,
        minute_id: str,
        *,
        action: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        try:
            workflow = GptMeetingMinuteWorkflow(str(action or "").strip())
        except ValueError as exc:
            raise GptActionsError(
                f"Invalid action '{action}'. Allowed: {[a.value for a in GptMeetingMinuteWorkflow]}",
                400,
            ) from exc
        user = request.state.user
        try:
            if workflow == GptMeetingMinuteWorkflow.SEND:
                return self._minutes.send_for_signature(user, minute_id)
            if workflow == GptMeetingMinuteWorkflow.FINALIZE:
                return self._minutes.finalize(user, minute_id)
            return self._minutes.cancel(user, minute_id, reason=reason)
        except PermissionError as exc:
            raise GptActionsError(str(exc), 403) from exc
        except LookupError as exc:
            raise GptActionsError(str(exc), 404) from exc
        except ValueError as exc:
            raise GptActionsError(str(exc), 400) from exc

    # --- private entity helpers ------------------------------------------

    def _validate_recurso(self, body: RecursoBody) -> None:
        assert_in(body.tipo_custo, TIPO_CUSTO_RECURSO, "tipo_custo")
        assert_in(body.recorrencia, RECORRENCIAS, "recorrencia")
        assert_in(body.criterio_rateio, CRITERIO_RATEIO, "criterio_rateio")
        assert_in(body.base_competencia, BASE_COMPETENCIA_RECURSO, "base_competencia")
        assert_in(body.status_recurso, STATUS_RECURSO, "status_recurso")
        assert_in(body.escopo_recurso, ESCOPO_RECURSO, "escopo_recurso")
        if body.categoria_recurso:
            assert_in(body.categoria_recurso, CATEGORIAS, "categoria_recurso")

    def _create_processo(
        self, request: Request, data: dict
    ) -> tuple[dict[str, Any], str, int]:
        body = ProcessoCreateBody.model_validate(data)
        filial_id = (body.filial_id or "").strip() or None
        setor_id = (body.setor_id or "").strip() or None
        create_instancia = bool(filial_id and setor_id)
        if create_instancia:
            self._raise_http_err(check_manage_filial_access(request, filial_id))
        self._raise_http_err(self._validate_processo_escopo_access(request, body))
        try:
            row = ProcessWriteService().create(
                body,
                active_filial_codigos=self._active_filial_codigos(),
                save_escopo=self._save_processo_escopo,
            )
        except ProcessWriteError as exc:
            raise GptActionsError(str(exc), 400) from exc
        pid = str(row["processo_id"])
        self._audit(request, "processo", pid, "create", body.model_dump())
        self._recalc_hook.after_processo(pid)
        return row_to_json(row), "Processo criado.", 201

    def _update_processo(
        self, request: Request, processo_id: str, data: dict
    ) -> tuple[dict[str, Any], str]:
        body = ProcessoUpdateBody.model_validate(data)
        self._raise_http_err(check_processo_view_access(request, processo_id))
        self._raise_http_err(self._validate_processo_escopo_access(request, body))
        try:
            row = ProcessWriteService().update(
                processo_id,
                body,
                save_escopo=self._save_processo_escopo,
            )
        except ProcessWriteError as exc:
            raise GptActionsError(str(exc), 400) from exc
        if not row:
            raise GptActionsError("Processo não encontrado.", 404)
        self._audit(request, "processo", processo_id, "update", body.model_dump())
        self._recalc_hook.after_processo(processo_id)
        return row_to_json(row), "Processo atualizado."

    def _create_instancia(
        self, request: Request, processo_id: str, body: InstanciaBody
    ) -> tuple[dict[str, Any], str, int]:
        if not body.todas_filiais_ativas:
            self._raise_http_err(check_manage_filial_access(request, body.filial_id or ""))
        if not ProcessoRepository().get(processo_id):
            raise GptActionsError("Processo não encontrado.", 404)
        try:
            if not body.todas_filiais_ativas:
                assert_filial_ativa(body.filial_id or "", self._active_filial_codigos())
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
        except (ProcessoInstanciaDomainError, ValueError) as exc:
            raise GptActionsError(str(exc), 400) from exc
        iid = str(row["instancia_id"])
        self._audit(
            request,
            "processo_instancia",
            iid,
            "create",
            {**body.model_dump(), "processo_id": processo_id, "instancia_id": iid},
        )
        return row_to_json(row), "Melhoria criada.", 201

    def _update_instancia(
        self, request: Request, instancia_id: str, data: dict
    ) -> tuple[dict[str, Any], str]:
        self._raise_http_err(check_instancia_view_access(request, instancia_id))
        existing = ProcessoInstanciaRepository().get(instancia_id)
        if not existing:
            raise GptActionsError("Instância não encontrada.", 404)
        body = InstanciaUpdateBody.model_validate(data)
        filial_atual = str(existing.get("codigo_filial") or existing.get("filial_id") or "")
        if filial_atual and not existing.get("todas_filiais_ativas"):
            self._raise_http_err(check_manage_filial_access(request, filial_atual))
        if body.todas_filiais_ativas is False and body.filial_id:
            self._raise_http_err(check_manage_filial_access(request, body.filial_id))
        try:
            row = ProcessoInstanciaRepository().update(
                instancia_id,
                {
                    "rotulo_instancia": body.rotulo_instancia,
                    "status_instancia": body.status_instancia,
                    "setor_ids": body.setor_ids,
                    "resumo_melhoria": body.resumo_melhoria,
                    "responsavel_local": body.responsavel_local,
                    "fase_melhoria": body.fase_melhoria,
                    "data_alvo_go_live": body.data_alvo_go_live,
                    "prioridade": body.prioridade,
                    "filial_id": body.filial_id,
                    "todas_filiais_ativas": body.todas_filiais_ativas,
                },
            )
        except (ProcessoInstanciaDomainError, ValueError) as exc:
            raise GptActionsError(str(exc), 400) from exc
        self._audit(request, "processo_instancia", instancia_id, "update", body.model_dump())
        return row_to_json(row), "Melhoria atualizada."

    def _has_processo_escopo(self, body: ProcessoCreateBody | ProcessoUpdateBody) -> bool:
        if isinstance(body, ProcessoUpdateBody):
            return (
                body.todas_filiais_ativas is not None
                or body.filial_ids is not None
                or body.setor_ids is not None
            )
        return bool(body.todas_filiais_ativas or body.filial_ids or body.setor_ids)

    def _escopo_values(
        self, body: ProcessoCreateBody | ProcessoUpdateBody
    ) -> tuple[bool, list[str], list[str]]:
        if isinstance(body, ProcessoUpdateBody):
            return (
                bool(body.todas_filiais_ativas),
                list(body.filial_ids or []),
                list(body.setor_ids or []),
            )
        return (
            bool(body.todas_filiais_ativas),
            list(body.filial_ids or []),
            list(body.setor_ids or []),
        )

    def _validate_processo_escopo_access(
        self, request: Request, body: ProcessoCreateBody | ProcessoUpdateBody
    ):
        if not self._has_processo_escopo(body):
            return None
        todas, filial_ids, _ = self._escopo_values(body)
        if todas:
            return None
        for filial_id in filial_ids:
            if err := check_manage_filial_access(request, filial_id):
                return err
        return None

    def _save_processo_escopo(
        self, processo_id: str, body: ProcessoCreateBody | ProcessoUpdateBody
    ) -> None:
        if not self._has_processo_escopo(body):
            return
        todas, filial_ids, setor_ids = self._escopo_values(body)
        ProcessoEscopoRepository().save_escopo(
            processo_id,
            todas_filiais_ativas=todas,
            filial_ids=filial_ids,
            setor_ids=setor_ids,
        )

    def _document_parent_id(self, entity: GptEntity, data: dict) -> str:
        key_map = {
            GptEntity.DECOMPOSITION_TREE: "processo_id",
            GptEntity.PROCESS_DIAGRAM: "processo_id",
            GptEntity.INSTANCE_DECOMPOSITION_SCOPE: "instancia_id",
            GptEntity.INSTANCE_DIAGRAM_SCOPE: "instancia_id",
            GptEntity.REVISION_DECOMPOSITION_OVERLAY: "revisao_id",
            GptEntity.REVISION_DIAGRAM_OVERLAY: "revisao_id",
        }
        key = key_map[entity]
        parent_id = str(data.get(key) or "").strip()
        if not parent_id:
            raise GptActionsError(f"data.{key} is required.", 400)
        return parent_id

    def _upsert_document(
        self,
        request: Request,
        entity: GptEntity,
        parent_id: str,
        data: dict,
    ) -> tuple[dict[str, Any], str, int] | tuple[dict[str, Any], str]:
        if entity == GptEntity.DECOMPOSITION_TREE:
            self._raise_http_err(check_processo_view_access(request, parent_id))
            conteudo = data.get("conteudo") if isinstance(data.get("conteudo"), dict) else data
            row = ProcessoDecomposicaoRepository().upsert(parent_id, conteudo=conteudo)
            self._audit(request, "processo", parent_id, "decomposition.updated", {})
            return row_to_json(row), "Decomposição salva.", 200

        if entity == GptEntity.INSTANCE_DECOMPOSITION_SCOPE:
            self._raise_http_err(check_instancia_view_access(request, parent_id))
            row = InstanciaDecomposicaoEscopoRepository().upsert(
                parent_id,
                node_ids=list(data.get("node_ids") or []),
                inherit_all=bool(data.get("inherit_all", False)),
                include_descendants=bool(data.get("include_descendants", True)),
            )
            self._audit(
                request,
                "processo_instancia",
                parent_id,
                "decomposition.scope.updated",
                {},
            )
            return row_to_json(row), "Escopo de decomposição salvo.", 200

        if entity == GptEntity.REVISION_DECOMPOSITION_OVERLAY:
            conteudo = data.get("conteudo") if isinstance(data.get("conteudo"), dict) else data
            row = RevisaoDecomposicaoOverlayRepository().upsert(
                parent_id, conteudo=conteudo
            )
            self._audit(request, "revisao", parent_id, "decomposition.overlay.updated", {})
            return row_to_json(row), "Overlay de decomposição salvo.", 200

        if entity == GptEntity.PROCESS_DIAGRAM:
            self._raise_http_err(check_processo_view_access(request, parent_id))
            conteudo = data.get("conteudo") if isinstance(data.get("conteudo"), dict) else data
            mermaid = data.get("mermaid_cached")
            row = ProcessoDiagramRepository().upsert(
                parent_id,
                conteudo=conteudo,
                mermaid_cached=mermaid if isinstance(mermaid, str) else None,
            )
            self._audit(request, "processo", parent_id, "diagram.macro.updated", {})
            return row_to_json(row), "Diagrama salvo.", 200

        if entity == GptEntity.INSTANCE_DIAGRAM_SCOPE:
            self._raise_http_err(check_instancia_view_access(request, parent_id))
            row = InstanciaDiagramEscopoRepository().upsert(
                parent_id,
                node_ids=list(data.get("node_ids") or []),
                inherit_all=bool(data.get("inherit_all", False)),
                include_boundary_edges=bool(data.get("include_boundary_edges", True)),
            )
            self._audit(
                request, "processo_instancia", parent_id, "diagram.escopo.updated", {}
            )
            return row_to_json(row), "Escopo de diagrama salvo.", 200

        if entity == GptEntity.REVISION_DIAGRAM_OVERLAY:
            conteudo = data.get("conteudo") if isinstance(data.get("conteudo"), dict) else data
            mermaid = data.get("mermaid_cached")
            row = RevisaoDiagramOverlayRepository().upsert(
                parent_id,
                conteudo=conteudo,
                mermaid_cached=mermaid if isinstance(mermaid, str) else None,
            )
            self._audit(request, "revisao", parent_id, "diagram.overlay.updated", {})
            return row_to_json(row), "Overlay de diagrama salvo.", 200

        raise GptActionsError(f"Document upsert not implemented for {entity.value}.", 400)
