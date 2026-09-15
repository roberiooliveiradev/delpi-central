"""TM-GPI-006 — governed user-parity capabilities for the Custom GPT facade.

Link/metadata evidence, process timeline, shared-resource cost adjustment,
and meeting-minute extras. Binary upload/download stays out of this surface.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import Request

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.services.audit_timeline_service import enrich_timeline_actor_names
from tm_app.application.services.html_sanitizer import TmAtaHtmlSanitizer
from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.application.services.process_activity_touch import (
    touch_processo_for_revisao,
    touch_processo_updated_at,
)
from tm_app.application.services.transformometro_realtime_notify import (
    notify_entity_updated,
)
from tm_app.core.auth_actor import actor_from_request, client_id_from_request
from tm_app.core.serialize import row_to_json, rows_to_json
from tm_app.infrastructure.llm.kimi_llm_gateway import KimiLlmGateway
from tm_app.infrastructure.persistence.repositories.audit_repository import (
    AuditRepository,
)
from tm_app.infrastructure.persistence.repositories.process_file_repository import (
    ProcessoArquivoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.resource_cost_repository import (
    RecursoCustoRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_evidence_repository import (
    RevisaoEvidenceRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import (
    RevisaoRepository,
)
from tm_app.infrastructure.persistence.repositories.shared_resource_repository import (
    RecursoRepository,
)
from tm_app.interface.http.branch_access_http import (
    check_instancia_manage_access,
    check_instancia_view_access,
    check_processo_manage_access,
    check_processo_view_access,
)


class GptEvidenceScope(str, Enum):
    PROCESS = "process"
    REVISION = "revision"


class GptEvidenceOperation(str, Enum):
    CREATE_LINK = "create_link"
    UPDATE_DESCRIPTION = "update_description"
    DELETE = "delete"


class GptMeetingMinuteManageAction(str, Enum):
    PENDING_SIGNATURES = "pending_signatures"
    AUDIT = "audit"
    VERSIONS = "versions"
    RESEND = "resend"
    CREATE_VERSION = "create_version"
    SET_PARTICIPANTS = "set_participants"
    SET_SIGNERS = "set_signers"
    GENERATE_FROM_TRANSCRIPT = "generate_from_transcript"


class ParityCapabilitiesService:
    """Canonical orchestration for TÉO user-parity Actions."""

    def __init__(
        self,
        *,
        minutes: MeetingMinutesService | None = None,
        kimi: KimiLlmGateway | None = None,
        raise_http_err,
        audit,
    ) -> None:
        self._minutes = minutes or MeetingMinutesService()
        self._kimi = kimi or KimiLlmGateway()
        self._raise_http_err = raise_http_err
        self._audit = audit

    # --- evidence --------------------------------------------------------

    def list_evidence(
        self,
        request: Request,
        *,
        scope: str,
        parent_id: str,
    ) -> dict[str, Any]:
        evidence_scope = self._parse_scope(scope)
        parent_id = str(parent_id or "").strip()
        if not parent_id:
            raise GptActionsError("parent_id is required.", 400)

        if evidence_scope == GptEvidenceScope.PROCESS:
            self._require_process_exists(parent_id)
            self._raise_http_err(check_processo_view_access(request, parent_id))
            rows = ProcessoArquivoRepository().list_by_processo(parent_id)
            items = [self._public_evidence_item(row, scope="process") for row in rows]
            return {
                "scope": "process",
                "processo_id": parent_id,
                "total": len(items),
                "items": items,
                "binary_upload": False,
                "binary_download": False,
                "link_metadata_supported": True,
            }

        revisao = self._require_revisao(parent_id)
        self._require_revisao_view(request, revisao)
        rows = RevisaoEvidenceRepository().list_by_revisao(parent_id)
        items = [self._public_evidence_item(row, scope="revision") for row in rows]
        return {
            "scope": "revision",
            "revisao_id": parent_id,
            "processo_id": str(revisao.get("processo_id") or ""),
            "total": len(items),
            "items": items,
            "binary_upload": False,
            "binary_download": False,
            "link_metadata_supported": True,
        }

    def manage_evidence(
        self,
        request: Request,
        *,
        scope: str,
        operation: str,
        parent_id: str,
        evidence_id: str | None = None,
        url_externa: str | None = None,
        descricao: str | None = None,
        confirm_delete: bool = False,
    ) -> dict[str, Any]:
        evidence_scope = self._parse_scope(scope)
        op = self._parse_evidence_op(operation)
        parent_id = str(parent_id or "").strip()
        if not parent_id:
            raise GptActionsError("parent_id is required.", 400)

        if evidence_scope == GptEvidenceScope.PROCESS:
            return self._manage_process_evidence(
                request,
                operation=op,
                processo_id=parent_id,
                evidence_id=evidence_id,
                url_externa=url_externa,
                descricao=descricao,
                confirm_delete=confirm_delete,
            )
        return self._manage_revision_evidence(
            request,
            operation=op,
            revisao_id=parent_id,
            evidence_id=evidence_id,
            url_externa=url_externa,
            descricao=descricao,
            confirm_delete=confirm_delete,
        )

    def _manage_process_evidence(
        self,
        request: Request,
        *,
        operation: GptEvidenceOperation,
        processo_id: str,
        evidence_id: str | None,
        url_externa: str | None,
        descricao: str | None,
        confirm_delete: bool,
    ) -> dict[str, Any]:
        self._require_process_exists(processo_id)
        self._raise_http_err(check_processo_manage_access(request, processo_id))
        repo = ProcessoArquivoRepository()
        user_id, email, _name = actor_from_request(request)

        if operation == GptEvidenceOperation.CREATE_LINK:
            url = str(url_externa or "").strip()
            if not url:
                raise GptActionsError("url_externa is required for create_link.", 400)
            row = repo.create(
                processo_id,
                {
                    "tipo": "link",
                    "url_externa": url,
                    "descricao": descricao,
                    "enviado_por_id": user_id or "unknown",
                    "enviado_por_nome": email or user_id,
                },
            )
            touch_processo_updated_at(processo_id)
            arquivo_id = str(row.get("arquivo_id") or "")
            self._audit(
                request, "processo_arquivo", arquivo_id, "create_link", {"processo_id": processo_id}
            )
            self._notify_process_file(request, processo_id, "processo.arquivo.created", arquivo_id)
            read_back = repo.get(processo_id, arquivo_id)
            return {
                "scope": "process",
                "operation": operation.value,
                "item": self._public_evidence_item(read_back or row, scope="process"),
                "verified": read_back is not None,
                "persisted": True,
            }

        eid = str(evidence_id or "").strip()
        if not eid:
            raise GptActionsError("evidence_id is required.", 400)

        if operation == GptEvidenceOperation.UPDATE_DESCRIPTION:
            row = repo.update(processo_id, eid, {"descricao": descricao})
            if not row:
                raise GptActionsError("Arquivo não encontrado.", 404)
            touch_processo_updated_at(processo_id)
            self._audit(
                request,
                "processo_arquivo",
                eid,
                "update_description",
                {"processo_id": processo_id},
            )
            self._notify_process_file(request, processo_id, "processo.arquivo.updated", eid)
            read_back = repo.get(processo_id, eid)
            return {
                "scope": "process",
                "operation": operation.value,
                "item": self._public_evidence_item(read_back or row, scope="process"),
                "verified": read_back is not None,
                "persisted": True,
            }

        if not confirm_delete:
            raise GptActionsError(
                "confirm_delete=true is required for evidence delete.",
                400,
            )
        removed = repo.soft_delete(processo_id, eid)
        if not removed:
            raise GptActionsError("Arquivo não encontrado.", 404)
        stored_name = removed.get("nome_armazenado")
        if stored_name:
            from tm_app.application.services.process_file_storage import (
                ProcessoArquivoStorage,
            )

            ProcessoArquivoStorage().delete_file(
                processo_id=processo_id,
                stored_name=str(stored_name),
            )
        touch_processo_updated_at(processo_id)
        self._audit(
            request, "processo_arquivo", eid, "delete", {"processo_id": processo_id}
        )
        self._notify_process_file(request, processo_id, "processo.arquivo.deleted", eid)
        still = repo.get(processo_id, eid)
        return {
            "scope": "process",
            "operation": operation.value,
            "arquivo_id": eid,
            "deleted": True,
            "verified": still is None,
            "persisted": True,
        }

    def _manage_revision_evidence(
        self,
        request: Request,
        *,
        operation: GptEvidenceOperation,
        revisao_id: str,
        evidence_id: str | None,
        url_externa: str | None,
        descricao: str | None,
        confirm_delete: bool,
    ) -> dict[str, Any]:
        revisao = self._require_revisao(revisao_id)
        self._require_revisao_manage(request, revisao)
        repo = RevisaoEvidenceRepository()
        user_id, email, _name = actor_from_request(request)
        processo_id = str(revisao.get("processo_id") or "") or None

        if operation == GptEvidenceOperation.CREATE_LINK:
            url = str(url_externa or "").strip()
            if not url:
                raise GptActionsError("url_externa is required for create_link.", 400)
            row = repo.create(
                revisao_id,
                {
                    "tipo": "link",
                    "url_externa": url,
                    "descricao": descricao,
                    "enviado_por_id": user_id or "unknown",
                    "enviado_por_nome": email or user_id,
                },
            )
            evidencia_id = str(
                row.get("evidencia_id") or row.get("revisao_evidencia_id") or ""
            )
            touch_processo_for_revisao(revisao_id, processo_id=processo_id)
            self._audit(
                request,
                "revisao_evidencia",
                evidencia_id,
                "create_link",
                {"revisao_id": revisao_id},
            )
            read_back = repo.get(revisao_id, evidencia_id)
            return {
                "scope": "revision",
                "operation": operation.value,
                "item": self._public_evidence_item(read_back or row, scope="revision"),
                "verified": read_back is not None,
                "persisted": True,
            }

        eid = str(evidence_id or "").strip()
        if not eid:
            raise GptActionsError("evidence_id is required.", 400)

        if operation == GptEvidenceOperation.UPDATE_DESCRIPTION:
            row = repo.update(revisao_id, eid, {"descricao": descricao})
            if not row:
                raise GptActionsError("Evidência não encontrada.", 404)
            touch_processo_for_revisao(revisao_id, processo_id=processo_id)
            self._audit(
                request,
                "revisao_evidencia",
                eid,
                "update_description",
                {"revisao_id": revisao_id},
            )
            read_back = repo.get(revisao_id, eid)
            return {
                "scope": "revision",
                "operation": operation.value,
                "item": self._public_evidence_item(read_back or row, scope="revision"),
                "verified": read_back is not None,
                "persisted": True,
            }

        if not confirm_delete:
            raise GptActionsError(
                "confirm_delete=true is required for evidence delete.",
                400,
            )
        removed = repo.soft_delete(revisao_id, eid)
        if not removed:
            raise GptActionsError("Evidência não encontrada.", 404)
        stored_name = removed.get("nome_armazenado")
        if stored_name:
            from tm_app.application.services.revision_evidence_storage import (
                RevisaoEvidenceStorage,
            )

            RevisaoEvidenceStorage().delete_file(
                revisao_id=revisao_id,
                stored_name=str(stored_name),
            )
        touch_processo_for_revisao(revisao_id, processo_id=processo_id)
        self._audit(
            request, "revisao_evidencia", eid, "delete", {"revisao_id": revisao_id}
        )
        still = repo.get(revisao_id, eid)
        return {
            "scope": "revision",
            "operation": operation.value,
            "evidencia_id": eid,
            "deleted": True,
            "verified": still is None,
            "persisted": True,
        }

    # --- timeline --------------------------------------------------------

    def get_process_timeline(
        self,
        request: Request,
        *,
        processo_id: str,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        processo_id = str(processo_id or "").strip()
        if not processo_id:
            raise GptActionsError("processo_id is required.", 400)
        self._require_process_exists(processo_id)
        self._raise_http_err(check_processo_view_access(request, processo_id))
        page = max(1, int(page or 1))
        page_size = min(200, max(1, int(page_size or 100)))
        data = AuditRepository().list_for_processo(
            processo_id, page=page, page_size=page_size
        )
        items = enrich_timeline_actor_names(
            rows_to_json(data["items"]),
            authorization=request.headers.get("Authorization"),
        )
        return {
            "processo_id": processo_id,
            "total": data["total"],
            "page": data["page"],
            "page_size": data["page_size"],
            "items": items,
        }

    # --- shared resource cost adjustment ---------------------------------

    def adjust_shared_resource_cost(
        self,
        request: Request,
        *,
        recurso_compartilhado_id: str,
        valor_mensal: float,
        vigente_desde: str,
        observacoes: str | None = None,
    ) -> dict[str, Any]:
        recurso_id = str(recurso_compartilhado_id or "").strip()
        if not recurso_id:
            raise GptActionsError("recurso_compartilhado_id is required.", 400)
        if not RecursoRepository().get(recurso_id):
            raise GptActionsError("Recurso não encontrado.", 404)
        try:
            row = RecursoCustoRepository().registrar_reajuste(
                recurso_id,
                float(valor_mensal),
                str(vigente_desde or "").strip(),
                observacoes,
            )
        except ValueError as exc:
            raise GptActionsError(str(exc), 400) from exc
        cid = str(row["recurso_custo_id"])
        self._audit(
            request,
            "recurso_custo",
            cid,
            "reajuste",
            {
                "recurso_compartilhado_id": recurso_id,
                "valor_mensal": valor_mensal,
                "vigente_desde": vigente_desde,
                "observacoes": observacoes,
            },
        )
        from tm_app.application.services.dashboard_recalc_hook_service import (
            DashboardRecalcHookService,
        )

        DashboardRecalcHookService().after_global_resource_change()
        read_back = RecursoCustoRepository().get(cid)
        recurso = RecursoRepository().get(recurso_id)
        return {
            "custo": row_to_json(read_back or row),
            "recurso": row_to_json(recurso) if recurso else None,
            "verified": read_back is not None,
            "persisted": True,
            "semantic_operation": "registrar_reajuste",
        }

    # --- meeting minute manage -------------------------------------------

    def manage_meeting_minute(
        self,
        request: Request,
        *,
        action: str,
        minute_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            manage = GptMeetingMinuteManageAction(str(action or "").strip())
        except ValueError as exc:
            raise GptActionsError(
                f"Invalid action '{action}'. Allowed: "
                f"{[a.value for a in GptMeetingMinuteManageAction]}",
                400,
            ) from exc
        user = request.state.user
        body = payload or {}
        try:
            if manage == GptMeetingMinuteManageAction.PENDING_SIGNATURES:
                data = self._minutes.pending_signatures(user)
                return {"action": manage.value, "data": data, "persisted": False}

            mid = str(minute_id or "").strip()
            if manage != GptMeetingMinuteManageAction.GENERATE_FROM_TRANSCRIPT and not mid:
                raise GptActionsError("minute_id is required for this action.", 400)

            if manage == GptMeetingMinuteManageAction.AUDIT:
                data = self._minutes.audit(user, mid)
                return {"action": manage.value, "minute_id": mid, "data": data}

            if manage == GptMeetingMinuteManageAction.VERSIONS:
                detail = self._minutes.get_detail(user, mid)
                return {
                    "action": manage.value,
                    "minute_id": mid,
                    "data": {
                        "versions": detail.get("versions") or [],
                        "current_version": detail.get("version"),
                    },
                }

            if manage == GptMeetingMinuteManageAction.RESEND:
                if not bool(body.get("confirm_resend")):
                    raise GptActionsError(
                        "confirm_resend=true is required for resend.",
                        400,
                    )
                data = self._minutes.resend_sign_invites(user, mid)
                return {
                    "action": manage.value,
                    "minute_id": mid,
                    "data": data,
                    "persisted": True,
                    "verified": True,
                }

            if manage == GptMeetingMinuteManageAction.CREATE_VERSION:
                data = self._minutes.create_version(user, mid, body)
                return {
                    "action": manage.value,
                    "minute_id": mid,
                    "data": data,
                    "persisted": True,
                    "verified": True,
                }

            if manage == GptMeetingMinuteManageAction.SET_PARTICIPANTS:
                participants = body.get("participants")
                if not isinstance(participants, list):
                    raise GptActionsError("participants[] is required.", 400)
                data = self._minutes.set_participants(user, mid, participants)
                return {
                    "action": manage.value,
                    "minute_id": mid,
                    "data": data,
                    "persisted": True,
                    "verified": True,
                }

            if manage == GptMeetingMinuteManageAction.SET_SIGNERS:
                signers = body.get("signers")
                if not isinstance(signers, list):
                    raise GptActionsError("signers[] is required.", 400)
                data = self._minutes.set_signers(user, mid, signers)
                return {
                    "action": manage.value,
                    "minute_id": mid,
                    "data": data,
                    "persisted": True,
                    "verified": True,
                }

            # generate_from_transcript — no persist
            unit_code = str(body.get("unit_code") or "").strip()
            transcript_html = str(body.get("transcript_html") or "").strip()
            if not unit_code or not transcript_html:
                raise GptActionsError(
                    "unit_code and transcript_html are required for generate_from_transcript.",
                    400,
                )
            self._minutes._assert(user, "manage", unit_code)
            sections = self._kimi.generate_from_transcript(transcript_html)
            sanitized = {
                key: TmAtaHtmlSanitizer.sanitize(value)
                for key, value in sections.items()
            }
            return {
                "action": manage.value,
                "persisted": False,
                "derived": True,
                "provenance": "transcript_derived_draft",
                "data": {
                    "unit_code": unit_code,
                    "meeting_date": body.get("meeting_date"),
                    "title": body.get("title"),
                    "source": body.get("source"),
                    **sanitized,
                },
            }
        except PermissionError as exc:
            raise GptActionsError(str(exc), 403) from exc
        except LookupError as exc:
            raise GptActionsError(str(exc), 404) from exc
        except ValueError as exc:
            raise GptActionsError(str(exc), 400) from exc

    # --- helpers ---------------------------------------------------------

    @staticmethod
    def _parse_scope(value: str) -> GptEvidenceScope:
        try:
            return GptEvidenceScope(str(value or "").strip())
        except ValueError as exc:
            raise GptActionsError(
                f"Invalid scope '{value}'. Allowed: process|revision",
                400,
            ) from exc

    @staticmethod
    def _parse_evidence_op(value: str) -> GptEvidenceOperation:
        try:
            return GptEvidenceOperation(str(value or "").strip())
        except ValueError as exc:
            raise GptActionsError(
                f"Invalid operation '{value}'. Allowed: "
                f"{[o.value for o in GptEvidenceOperation]}",
                400,
            ) from exc

    @staticmethod
    def _require_process_exists(processo_id: str) -> dict[str, Any]:
        row = ProcessoRepository().get(processo_id)
        if not row:
            raise GptActionsError("Processo não encontrado.", 404)
        return row

    @staticmethod
    def _require_revisao(revisao_id: str) -> dict[str, Any]:
        row = RevisaoRepository().get(revisao_id)
        if not row:
            raise GptActionsError("Revisão não encontrada.", 404)
        return row

    def _require_revisao_view(self, request: Request, revisao: dict[str, Any]) -> None:
        instancia_id = str(revisao.get("instancia_id") or "").strip()
        if instancia_id:
            self._raise_http_err(check_instancia_view_access(request, instancia_id))
            return
        processo_id = str(revisao.get("processo_id") or "").strip()
        if processo_id:
            self._raise_http_err(check_processo_view_access(request, processo_id))

    def _require_revisao_manage(self, request: Request, revisao: dict[str, Any]) -> None:
        instancia_id = str(revisao.get("instancia_id") or "").strip()
        if instancia_id:
            self._raise_http_err(check_instancia_manage_access(request, instancia_id))
            return
        processo_id = str(revisao.get("processo_id") or "").strip()
        if processo_id:
            self._raise_http_err(check_processo_manage_access(request, processo_id))

    @staticmethod
    def _public_evidence_item(row: dict[str, Any] | None, *, scope: str) -> dict[str, Any]:
        data = row_to_json(row or {})
        # Never expose storage internals to the GPT surface.
        data.pop("nome_armazenado", None)
        data["scope"] = scope
        data["has_binary"] = bool(
            (row or {}).get("nome_armazenado") or (row or {}).get("tamanho_bytes")
        )
        data["is_external_link"] = str((row or {}).get("tipo") or "") == "link" or bool(
            (row or {}).get("url_externa")
        )
        return data

    def _notify_process_file(
        self, request: Request, processo_id: str, action: str, arquivo_id: str
    ) -> None:
        user_id, _, _ = actor_from_request(request)
        notify_entity_updated(
            entity_type="processo",
            entity_id=processo_id,
            action=action,
            actor_user_id=user_id,
            actor_client_id=client_id_from_request(request),
            payload={"arquivo_id": arquivo_id},
        )
