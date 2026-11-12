"""Use cases do Product Registration — intake, fila, workflow, verify.

Regras do contrato §5–§8: solicitação ≠ cadastro; draft ≠ revisão;
revisão imutável só nasce de verificação ``matched``; alteração seletiva
nunca exige ficha inteira; rejeição não toca a ficha vigente; falha de
verificação nunca publica revisão.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from engineering_app.application.ports.product_registration import (
    AttachmentStoragePort,
    OfficialProductReaderPort,
    ProductRegistrationRepository,
)
from engineering_app.application.ports.realtime import (
    NullRealtimePublisher,
    RealtimeEvent,
    RealtimePublisher,
)
from engineering_app.domain.product_registration import (
    attachments as attachments_mod,
)
from engineering_app.domain.product_registration import baseline as sa5_baseline
from engineering_app.domain.product_registration import catalog
from engineering_app.domain.product_registration import flags as attendance_flags
from engineering_app.domain.product_registration import (
    correction_returns as corr_returns,
)
from engineering_app.domain.product_registration import (
    information_rounds as info_rounds,
)
from engineering_app.domain.product_registration.errors import (
    PrcConcurrencyError,
    PrcDuplicateError,
    PrcForbiddenError,
    PrcNotFoundError,
    PrcOfficialError,
    PrcStateConflictError,
    PrcUnverifiableFieldError,
    PrcValidationError,
)
from engineering_app.domain.product_registration.models import (
    DIVERGENCE_ROUTE_DECISIONS,
    DIVERGENCE_ROUTE_FROM,
    DIVERGENCE_TARGET_TYPES,
    REQUEST_TYPES,
    PrcActor,
    transition_for,
)

_ALLOWED_SOURCES_DEFAULT = (
    "portal-engineering",
    "my-requests",
    "eva",
    "engineering-test",
)

_EVENT_TYPE_BY_ACTION = {
    "start": "started",
    "request_information": "information_requested",
    "resume": "resumed",
    "submit_review": "submitted_for_review",
    "return_to_attendance": "returned_to_attendance",
    "return_for_correction": "correction_returned",
    "resubmit_correction": "correction_resubmitted",
    "complete": "completed",
    "reject": "rejected",
}

_REQUESTER_SCOPED_ACTIONS = frozenset(
    {
        # FIX-08 — ações de escrita exclusivas do criador do caso:
        # correção da devolução + edição livre pré-atendimento.
        "save_returned_fields",
        "resubmit_correction",
        "edit_draft",
    }
)
_ANALYST_ONLY_ACTIONS = frozenset(
    {
        "start",
        "return_for_correction",
        "complete",
        "verify_and_complete",
        "reject",
        "request_information",
        "resume",
        "submit_review",
        "return_to_attendance",
        "route_divergence",
    }
)

# Status a partir dos quais a conclusão verificada é permitida (REF-020).
_COMPLETE_FROM = frozenset({"in_progress", "under_review"})


logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


def _fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()


def _require_actor_read(actor: PrcActor) -> None:
    if not actor.can_read:
        raise PrcForbiddenError("Sem permissão de leitura do módulo.")


def _require_actor_create(actor: PrcActor) -> None:
    if not actor.can_create:
        raise PrcForbiddenError("Sem permissão de criação de solicitação.")


def _require_actor_process(actor: PrcActor) -> None:
    if not actor.can_process:
        raise PrcForbiddenError("Sem permissão de processamento técnico.")


def _require_actor_verify(actor: PrcActor) -> None:
    if not actor.can_verify:
        raise PrcForbiddenError(
            "Concluir exige permissões process + verify."
        )


def _scope_check(actor: PrcActor, request: dict) -> None:
    """Escopo do recurso: analista vê tudo; solicitante, somente o próprio
    caso (ou o caso a ele atribuído)."""
    if actor.is_analyst:
        return
    if (
        request["requester_subject"] != actor.user_id
        and request.get("assigned_to_subject") != actor.user_id
    ):
        raise PrcForbiddenError("Solicitação fora do escopo do ator.")


def _request_detail(request: dict, actor: PrcActor) -> dict[str, Any]:
    draft = request.get("draft") or {}
    verifs = request.get("verifications") or []
    last = verifs[-1] if verifs else None
    return {
        "id": request["id"],
        "requestType": request["request_type"],
        "productType": request["product_type"],
        "status": request["status"],
        "source": request["source"],
        "externalRequestId": request.get("external_request_id"),
        "requester": {
            "subject": request["requester_subject"],
            "displayName": request.get("requester_display_name"),
        },
        "assignedTo": request.get("assigned_to_subject"),
        "assignedToDisplayName": request.get("assigned_to_display_name"),
        "officialCode": request.get("official_product_code"),
        "baseRevision": request.get("base_revision_number"),
        "requestedChanges": request["requested_payload"],
        "technicalDraft": draft.get("technical_data"),
        "changedPaths": draft.get("changed_paths", []),
        "draftVersion": draft.get("row_version"),
        "caseVersion": request["row_version"],
        "officialBaseline": sa5_baseline.public_baseline_view(
            request.get("official_baseline")
        ),
        "removeCompletionPolicy": (
            sa5_baseline.SA5_REMOVE_COMPLETION_POLICY
        ),
        "allowedActions": actor.allowed_actions(request["status"]),
        "verificationSummary": (
            {
                "result": last["result"],
                "checkedAt": last["checked_at"],
                "officialSource": last["official_source"],
            }
            if last
            else None
        ),
        "createdAt": request["created_at"],
        "updatedAt": request["updated_at"],
        "completedRecordId": request.get("completed_record_id"),
    }


def _active_info_round(
    rounds: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for rnd in rounds:
        if rnd.get("status") in ("awaiting_requester", "awaiting_review"):
            return rnd
    return None


class ProductRegistrationService:
    """Casos de uso do módulo — mesma implementação REST/EVA."""

    def __init__(
        self,
        repository: ProductRegistrationRepository,
        *,
        official_reader: OfficialProductReaderPort | None = None,
        allowed_sources: tuple[str, ...] | None = None,
        attachment_storage: "AttachmentStoragePort | None" = None,
        realtime_publisher: RealtimePublisher | None = None,
    ) -> None:
        self._repo = repository
        self._reader = official_reader
        self._sources = allowed_sources or _ALLOWED_SOURCES_DEFAULT
        self._storage = attachment_storage
        self._realtime = realtime_publisher or NullRealtimePublisher()

    def _filter_actions_for_actor(
        self,
        actions: list[str],
        *,
        actor: PrcActor,
        request: dict[str, Any],
    ) -> list[str]:
        """Object AuthZ: solicitante ≠ analista; dual-role sem toggle."""
        requester = str(request.get("requester_subject") or "")
        is_requester = bool(requester) and actor.user_id == requester
        out: list[str] = []
        for action in actions:
            if action in _REQUESTER_SCOPED_ACTIONS:
                if is_requester and actor.has_action_permission(action):
                    out.append(action)
                continue
            if action in _ANALYST_ONLY_ACTIONS:
                if actor.is_analyst and actor.has_action_permission(action):
                    out.append(action)
                continue
            if actor.has_action_permission(action):
                out.append(action)
        return out

    def _attach_information_exchange(
        self,
        detail: dict[str, Any],
        request_id: str,
        *,
        actor: PrcActor,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """PRC-REF-019-FIX-01 — capabilities explícitas + filtro de resume.

        ``allowedActions`` não oferece ``resume`` enquanto houver rodada
        aberta (o domínio rejeitaria com 409). ``canRespond``/``canReview``
        são capacidades de apresentação; a AuthZ efetiva permanece nos
        use cases de draft/submit/accept/follow-up/resume.
        """
        rounds = self._repo.list_information_rounds(request_id=request_id)
        blocker = info_rounds.has_open_information_blocker(rounds)
        active = _active_info_round(rounds)
        actions = [
            action
            for action in (detail.get("allowedActions") or [])
            if not (
                blocker
                and action in ("resume", "complete", "verify_and_complete")
            )
        ]
        detail["allowedActions"] = actions
        requester = str(request.get("requester_subject") or "")
        active_status = active.get("status") if active else None
        detail["informationExchange"] = {
            "hasOpenBlocker": blocker,
            "canRespond": bool(
                requester
                and actor.user_id == requester
                and active_status == "awaiting_requester"
            ),
            "canReview": bool(
                actor.is_analyst
                and request.get("status") == "needs_information"
            ),
            "activeRoundStatus": active_status,
            "activeRoundId": active.get("id") if active else None,
        }
        return detail

    def _attach_correction_exchange(
        self,
        detail: dict[str, Any],
        request_id: str,
        *,
        actor: PrcActor,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """PRC-REF-022 — ciclo aberto de devolução + AuthZ por objeto."""
        open_ret = self._repo.get_open_correction_return(
            request_id=request_id
        )
        last_closed = None
        if open_ret is None:
            history = self._repo.list_correction_returns(
                request_id=request_id
            )
            for row in reversed(history):
                if row.get("status") == "resubmitted":
                    last_closed = row
                    break
        actions = self._filter_actions_for_actor(
            list(detail.get("allowedActions") or []),
            actor=actor,
            request=request,
        )
        # Em needs_correction o analista não edita a ficha operacionalmente.
        if request.get("status") == "needs_correction":
            actions = [
                a
                for a in actions
                if a not in ("edit_draft", "return_for_correction", "complete")
            ]
        detail["allowedActions"] = actions
        requester = str(request.get("requester_subject") or "")
        is_requester = bool(requester) and actor.user_id == requester
        view = (
            corr_returns.public_return_view(open_ret)
            if open_ret
            else (
                corr_returns.public_return_view(last_closed)
                if last_closed
                else None
            )
        )
        detail["correctionExchange"] = {
            "hasOpenReturn": open_ret is not None,
            "canCorrect": bool(
                is_requester
                and open_ret is not None
                and request.get("status") == "needs_correction"
            ),
            "canReturn": bool(
                actor.is_analyst and request.get("status") == "in_progress"
            ),
            "openReturn": view if open_ret else None,
            "lastResubmitted": (
                corr_returns.public_return_view(last_closed)
                if last_closed and open_ret is None
                else None
            ),
            "requesterAuthz": {
                "status": (
                    "PENDING_OWNER"
                    if not actor.has_action_permission(
                        "save_returned_fields"
                    )
                    else "object_scoped"
                ),
                "code": (
                    "ARCHITECTURE_DECISION_REQUIRED"
                    if not actor.has_action_permission(
                        "save_returned_fields"
                    )
                    else None
                ),
                "note": (
                    "Solicitante sem engineering.access e sem "
                    "my-requests.raw-material-creation.create não corrige."
                    if not actor.has_action_permission(
                        "save_returned_fields"
                    )
                    else "Object AuthZ: apenas requester_subject do caso."
                ),
            },
        }
        return detail

    def _detail(
        self,
        request: dict[str, Any],
        actor: PrcActor,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        detail = _request_detail(request, actor)
        rid = request_id or str(request.get("id") or "")
        if not rid:
            return detail
        detail = self._attach_information_exchange(
            detail, rid, actor=actor, request=request
        )
        return self._attach_correction_exchange(
            detail, rid, actor=actor, request=request
        )

    # --- helpers de idempotência -------------------------------------------------

    def _idempotent_replay(
        self,
        *,
        actor: PrcActor,
        operation: str,
        key: str | None,
        fingerprint: str,
    ) -> dict[str, Any] | None:
        if not key:
            return None
        stored = self._repo.find_idempotent(
            actor_or_source=actor.user_id,
            operation=operation,
            idempotency_key=key,
        )
        if stored is None:
            return None
        if stored["request_fingerprint"] != fingerprint:
            raise PrcDuplicateError(
                "Idempotency-Key reutilizada com payload divergente."
            )
        return {
            "replayed": True,
            "response": stored["response_payload"],
        }

    def _idempotent_store(
        self,
        *,
        actor: PrcActor,
        operation: str,
        key: str | None,
        fingerprint: str,
        request_id: str | None,
        status: int,
        payload: dict[str, Any],
    ) -> None:
        if key:
            self._repo.save_idempotent(
                actor_or_source=actor.user_id,
                operation=operation,
                idempotency_key=key,
                request_fingerprint=fingerprint,
                request_id=request_id,
                response_status=status,
                response_payload=payload,
            )
        # ENG-REALTIME-01 — a mutação do caso (e o registro idempotente)
        # já commitaram neste ponto: emitir aqui é pós-commit real.
        # Replays retornam antes da mutação → nunca chegam aqui.
        if request_id:
            self._emit_change(request_id, reason=operation, actor=actor)

    # --- realtime (ENG-REALTIME-01) ------------------------------------------

    def _emit_change(
        self,
        request_id: str,
        *,
        reason: str,
        actor: PrcActor,
    ) -> None:
        """Evento leve pós-commit — best-effort, nunca falha a mutação."""
        try:
            request = self._repo.get_request(request_id) or {}
            recipients = tuple(
                uid
                for uid in (
                    str(request.get("requester_subject") or "").strip(),
                    str(request.get("assigned_to_subject") or "").strip(),
                )
                if uid
            )
            self._realtime.publish(
                RealtimeEvent(
                    domain="product-registration",
                    resource_type="request",
                    resource_id=str(request_id),
                    reason=reason,
                    occurred_at=_now(),
                    event_id=_uuid(),
                    version=request.get("version"),
                    status=request.get("status"),
                    actor_user_id=actor.user_id,
                    actor_client_id=getattr(actor, "client_id", None),
                    recipient_user_ids=recipients,
                )
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "prc_realtime_emit_failed request_id=%s reason=%s",
                request_id,
                reason,
            )

    def can_observe(self, request_id: str, actor: PrcActor) -> bool:
        """Autorização de assinatura WS: leitura do módulo + escopo por
        objeto (solicitante/atribuído ou analista). Fail-closed."""
        try:
            _require_actor_read(actor)
            self._get_scoped(request_id, actor)
        except Exception:  # noqa: BLE001
            return False
        return True

    # --- INTAKE ------------------------------------------------------------------

    async def submit_request(
        self,
        *,
        actor: PrcActor,
        source: str,
        external_request_id: str | None,
        external_item_id: str | None,
        request_type: str,
        product_type: str,
        schema_version: int,
        payload: dict[str, Any],
        idempotency_key: str | None,
        access_token: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        _require_actor_create(actor)
        if request_type not in REQUEST_TYPES:
            raise PrcValidationError(
                "requestType inválido.", fields={"requestType": "enum"}
            )
        if product_type not in catalog.PRODUCT_TYPES:
            raise PrcValidationError(
                "productType não suportado no MVP.",
                fields={"productType": ",".join(catalog.PRODUCT_TYPES)},
            )
        if schema_version != catalog.PAYLOAD_SCHEMA_VERSION:
            raise PrcValidationError(
                "schemaVersion não suportada.",
                fields={"schemaVersion": str(catalog.PAYLOAD_SCHEMA_VERSION)},
            )
        if source not in self._sources:
            raise PrcForbiddenError("Origem da solicitação não autorizada.")

        fp = _fingerprint(
            {
                "source": source,
                "external_request_id": external_request_id,
                "external_item_id": external_item_id,
                "request_type": request_type,
                "product_type": product_type,
                "schema_version": schema_version,
                "payload": payload,
            }
        )
        replay = self._idempotent_replay(
            actor=actor,
            operation="intake",
            key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay

        draft_data: dict[str, Any]
        changed_paths: list[dict[str, Any]]
        official_code: str | None
        base_revision: int | None
        official_baseline: dict[str, Any] | None = None

        if request_type == "create":
            draft_data = catalog.validate_create_payload(
                payload.get("requestedData")
            )
            changed_paths = []
            official_code = draft_data.pop("officialProductCode", None)
            base_revision = None
            stored_payload = dict(draft_data)
            # D14-FIX — justificativas opcionais individuais do create:
            # canal `reasons` próprio, validado contra os vínculos
            # declarados; auditado no payload, nunca no snapshot técnico.
            supplier_keys = {
                (
                    str(s.get("supplierCode") or "").strip(),
                    str(s.get("store") or "").strip(),
                )
                for s in draft_data.get("suppliers") or []
            }
            reasons, reasons_err = catalog.validate_create_reasons(
                payload.get("reasons"), supplier_keys
            )
            if reasons_err:
                raise PrcValidationError(
                    reasons_err, fields={"reasons": "invalid"}
                )
            if reasons:
                stored_payload["reasons"] = reasons
        else:
            official_code = (payload.get("officialProductCode") or "").strip()
            if not official_code:
                raise PrcValidationError(
                    "officialProductCode é obrigatório em update.",
                    fields={"officialProductCode": "required"},
                )
            try:
                official_code = catalog.normalize_code(
                    official_code, max_length=60
                )
            except PrcValidationError:
                raise PrcValidationError(
                    "officialProductCode inválido.",
                    fields={"officialProductCode": "invalid"},
                )
            base_revision_raw = payload.get("baseRevision")
            base_revision = None
            if base_revision_raw is not None:
                try:
                    base_revision = int(base_revision_raw)
                except (TypeError, ValueError):
                    raise PrcValidationError(
                        "baseRevision inválido.",
                        fields={"baseRevision": "invalid"},
                    )
                if base_revision < 1:
                    raise PrcValidationError(
                        "baseRevision deve ser >= 1.",
                        fields={"baseRevision": "invalid"},
                    )
            link_ops, link_err = catalog.validate_supplier_link_changes(
                payload.get("supplierLinkChanges")
            )
            if link_err:
                raise PrcValidationError(
                    link_err, fields={"supplierLinkChanges": "invalid"}
                )
            # D13: UPDATE só-SA5 é legítimo — changes pode ser vazio
            # quando há ops de vínculo; o requisito "1+ alteração" é
            # garantido pelo check conjunto logo abaixo.
            raw_changes = payload.get("changes")
            if raw_changes or not link_ops:
                changes = catalog.validate_update_changes(raw_changes)
            else:
                changes = []
            if not changes and not link_ops:
                raise PrcValidationError(
                    "UPDATE exige ao menos uma alteração efetiva.",
                    fields={"changes": "required"},
                )
            record = self._repo.get_record_by_official_code(
                official_source=catalog.OFFICIAL_SOURCE,
                official_code=official_code,
            )
            if record is not None:
                current = int(record["current_revision_number"])
                # REF-001: a revisão-base é resolvida pelo backend — o
                # solicitante nunca digita a revisão. Se um consumidor
                # legado informar revisão divergente da corrente, o CAS
                # ainda falha fechado com stale_revision.
                if base_revision is not None and base_revision != current:
                    raise PrcConcurrencyError("stale_revision")
                base_revision = current
                base = self._repo.get_revision(
                    record["id"], current
                )
                snapshot = (base or {}).get("technical_snapshot") or {}
            else:
                snapshot = {"officialProductCode": official_code}
            # D15 — baseline oficial server-side (não confiar no browser).
            official_baseline = await self._capture_update_baseline(
                actor=actor,
                official_code=official_code,
                access_token=access_token,
                correlation_id=correlation_id or _uuid(),
                client_fingerprint=payload.get("baselineFingerprint"),
                require_links_complete=bool(link_ops),
            )
            baseline_err = sa5_baseline.validate_link_ops_against_baseline(
                link_ops, official_baseline
            )
            if baseline_err:
                raise PrcValidationError(
                    baseline_err,
                    fields={"supplierLinkChanges": "baseline_precondition"},
                )
            draft_data = dict(snapshot)
            draft_data["officialProductCode"] = official_code
            for change in changes:
                draft_data[change["path"]] = change["proposedValue"]
            changed_paths = [
                {"path": c["path"], "reason": c["reason"]} for c in changes
            ]
            draft_data["supplierLinkChanges"] = link_ops
            stored_payload = {
                "officialProductCode": official_code,
                "baseRevision": base_revision,
                "changes": changes,
                "supplierLinkChanges": link_ops,
                "baselineFingerprint": official_baseline.get("fingerprint"),
            }

        request_id = _uuid()
        now = _now()
        request = {
            "id": request_id,
            "request_type": request_type,
            "product_type": product_type,
            "source": source,
            "external_request_id": external_request_id,
            "external_item_id": external_item_id,
            "requester_subject": actor.user_id,
            "requester_display_name": actor.label,
            "official_product_code": official_code,
            "base_revision_number": base_revision,
            "requested_payload": stored_payload,
            "payload_schema_version": schema_version,
            "status": "submitted",
            "assigned_to_subject": None,
            "row_version": 1,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "rejected_at": None,
            "completed_record_id": None,
            "official_baseline": official_baseline,
        }
        draft = {
            "request_id": request_id,
            "schema_version": catalog.PAYLOAD_SCHEMA_VERSION,
            "technical_data": draft_data,
            "changed_paths": changed_paths,
            "row_version": 1,
            "updated_by_subject": actor.user_id,
            "updated_at": now,
        }
        event = {
            "event_type": "submitted",
            "actor_subject": actor.user_id,
            "actor_display_name": actor.label,
            "actor_email": actor.email,
            "reason": None,
            "metadata": {
                "source": source,
                "request_type": request_type,
                "external_request_id": external_request_id,
                "channel": actor.channel,
                **(
                    {
                        "baselineFingerprint": (
                            official_baseline or {}
                        ).get("fingerprint"),
                        "baselineVersion": (
                            official_baseline or {}
                        ).get("baselineVersion"),
                        "linksComplete": (
                            official_baseline or {}
                        ).get("linksComplete"),
                    }
                    if official_baseline
                    else {}
                ),
            },
            "previous_status": None,
            "next_status": "submitted",
        }
        try:
            created = self._repo.create_request(
                request=request, draft=draft, event=event
            )
        except PrcDuplicateError:
            existing = self._repo.get_request_by_external_ref(
                source=source,
                external_request_id=external_request_id or "",
                external_item_id=external_item_id,
            )
            if existing is not None:
                raise PrcDuplicateError("duplicate_external_reference")
            raise
        response = {
            "requestId": request_id,
            "caseStatus": "submitted",
            "createdAt": now,
            "source": source,
            "requestType": request_type,
            "caseVersion": 1,
        }
        self._idempotent_store(
            actor=actor,
            operation="intake",
            key=idempotency_key,
            fingerprint=fp,
            request_id=request_id,
            status=201,
            payload=response,
        )
        return response

    # --- READS --------------------------------------------------------------------

    def list_requests(
        self, *, actor: PrcActor, filters: dict[str, Any]
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        return self._repo.list_requests(
            status=filters.get("status"),
            request_type=filters.get("type"),
            assignee=filters.get("assignee"),
            source=filters.get("source"),
            search=filters.get("search"),
            date_from=filters.get("dateFrom"),
            date_to=filters.get("dateTo"),
            requester_subject=actor.user_id,
            global_scope=actor.is_analyst,
            page=int(filters.get("page", 1)),
            page_size=int(filters.get("pageSize", 25)),
            sort_by=filters.get("sortBy"),
            sort_dir=filters.get("sortDir"),
        )

    def _get_scoped(self, request_id: str, actor: PrcActor) -> dict[str, Any]:
        request = self._repo.get_request(request_id)
        if request is None:
            raise PrcNotFoundError("request", request_id)
        _scope_check(actor, request)
        return request

    def get_request_detail(
        self, request_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        request = self._get_scoped(request_id, actor)
        request["verifications"] = self._repo.list_verifications(request_id)
        return self._detail(request, actor, request_id=request_id)

    def get_timeline(
        self, request_id: str, *, actor: PrcActor, page: int, page_size: int
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        self._get_scoped(request_id, actor)
        return self._repo.list_events(request_id, page, page_size)

    def list_verifications(
        self, request_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        self._get_scoped(request_id, actor)
        items = self._repo.list_verifications(request_id)
        for item in items:
            item.pop("observed_fields", None)
        return {
            "items": items,
            "total": len(items),
            "routings": self._list_divergence_routings(request_id),
        }

    def _list_divergence_routings(
        self, request_id: str
    ) -> list[dict[str, Any]]:
        """Extrai decisões PRC-REF-021 dos eventos append-only."""
        page = self._repo.list_events(request_id, page=1, page_size=500)
        out: list[dict[str, Any]] = []
        for ev in page.get("items") or []:
            if ev.get("event_type") != "divergence_routed":
                continue
            meta = ev.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            if not isinstance(meta, dict):
                meta = {}
            out.append(
                {
                    "id": ev.get("id"),
                    "verificationId": meta.get("verificationId"),
                    "targetType": meta.get("targetType"),
                    "targetPath": meta.get("targetPath"),
                    "targetAttribute": meta.get("targetAttribute"),
                    "supplierKey": meta.get("supplierKey"),
                    "targetKey": meta.get("targetKey"),
                    "decision": meta.get("decision"),
                    "reason": ev.get("reason"),
                    "actorSubject": ev.get("actor_subject"),
                    "actorDisplayName": ev.get("actor_display_name"),
                    "occurredAt": ev.get("occurred_at"),
                    "routingStatus": meta.get("routingStatus"),
                    "informationRoundId": meta.get("informationRoundId"),
                }
            )
        return out

    def route_divergence(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        verification_id: str,
        target_type: str,
        target_path: str | None,
        supplier_key: dict[str, Any] | None,
        target_attribute: str | None,
        decision: str,
        reason: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """PRC-REF-021 — registra encaminhamento por item divergente.

        Não altera ``field_results``, MATCH, revisão, código oficial nem
        status terminal. ``REQUESTER_CORRECTION`` não concede escrita ao
        solicitante enquanto Core AuthZ estiver ``PENDING_OWNER``.
        """
        _require_actor_process(actor)
        if not actor.has_action_permission("route_divergence"):
            raise PrcForbiddenError(
                "Sem permissão para encaminhar divergências."
            )
        request = self._get_scoped(request_id, actor)
        if request["status"] not in DIVERGENCE_ROUTE_FROM:
            raise PrcStateConflictError("state_conflict")
        decision_u = (decision or "").strip().upper()
        if decision_u not in DIVERGENCE_ROUTE_DECISIONS:
            raise PrcValidationError(
                "decision inválida.",
                fields={"decision": ",".join(sorted(DIVERGENCE_ROUTE_DECISIONS))},
            )
        target_u = (target_type or "").strip().upper()
        if target_u not in DIVERGENCE_TARGET_TYPES:
            raise PrcValidationError(
                "targetType inválido.",
                fields={"targetType": ",".join(sorted(DIVERGENCE_TARGET_TYPES))},
            )
        reason_text = (reason or "").strip()[:1000]
        if len(reason_text) < 3:
            raise PrcValidationError(
                "Justificativa é obrigatória.",
                fields={"reason": "required"},
            )
        vid = (verification_id or "").strip()
        if not vid:
            raise PrcValidationError(
                "verificationId é obrigatório.",
                fields={"verificationId": "required"},
            )
        verifications = self._repo.list_verifications(request_id)
        if not any(str(v.get("id")) == vid for v in verifications):
            raise PrcNotFoundError("verification", vid)

        path = (target_path or "").strip() or None
        attr = (target_attribute or "").strip() or None
        supplier: dict[str, str] | None = None
        if target_u == "FIELD":
            if not path or path == "suppliers":
                raise PrcValidationError(
                    "targetPath SB1 é obrigatório.",
                    fields={"targetPath": "required"},
                )
            target_key = f"FIELD:{path}"
        else:
            code = str((supplier_key or {}).get("supplierCode") or "").strip()
            store = str((supplier_key or {}).get("store") or "").strip()
            if not code or not store:
                raise PrcValidationError(
                    "supplierKey.supplierCode/store obrigatórios.",
                    fields={"supplierKey": "required"},
                )
            supplier = {"supplierCode": code, "store": store}
            path = path or "suppliers"
            attr_key = attr or "link"
            target_key = f"SUPPLIER_LINK:{code}/{store}:{attr_key}"

        routing_status = {
            "REQUESTER_CORRECTION": "pending_owner",
            "ERP_MANUAL_CORRECTION": "recorded_external",
            "NEEDS_CLARIFICATION": "recorded",
        }[decision_u]

        fp = _fingerprint(
            {
                "action": "route_divergence",
                "request_id": request_id,
                "expected_version": expected_version,
                "verification_id": vid,
                "target_key": target_key,
                "decision": decision_u,
                "reason": reason_text,
            }
        )
        replay = self._idempotent_replay(
            actor=actor,
            operation="route_divergence",
            key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay

        updated = self._repo.apply_transition(
            request_id=request_id,
            expected_version=expected_version,
            allowed_from=DIVERGENCE_ROUTE_FROM,
            actor_label=actor.label or actor.user_id,
            actor_subject=actor.user_id,
            actor_email=actor.email,
            event_type="divergence_routed",
            next_status=request["status"],
            set_fields={},
            reason=reason_text,
            event_meta={
                "action": "route_divergence",
                "channel": actor.channel,
                "verificationId": vid,
                "targetType": target_u,
                "targetPath": path,
                "targetAttribute": attr,
                "supplierKey": supplier,
                "targetKey": target_key,
                "decision": decision_u,
                "routingStatus": routing_status,
                "informationRoundId": None,
            },
        )
        routing = {
            "id": None,
            "verificationId": vid,
            "targetType": target_u,
            "targetPath": path,
            "targetAttribute": attr,
            "supplierKey": supplier,
            "targetKey": target_key,
            "decision": decision_u,
            "reason": reason_text,
            "actorSubject": actor.user_id,
            "actorDisplayName": actor.label,
            "occurredAt": updated.get("updated_at"),
            "routingStatus": routing_status,
            "informationRoundId": None,
        }
        # Preenche id do evento mais recente matching.
        for item in reversed(self._list_divergence_routings(request_id)):
            if (
                item.get("targetKey") == target_key
                and item.get("verificationId") == vid
                and item.get("decision") == decision_u
            ):
                routing["id"] = item.get("id")
                routing["occurredAt"] = item.get("occurredAt")
                break

        response: dict[str, Any] = {
            "routing": routing,
            "caseVersion": int(updated.get("row_version") or expected_version + 1),
            "requesterWrite": None,
        }
        if decision_u == "REQUESTER_CORRECTION":
            response["requesterWrite"] = {
                "status": "PENDING_OWNER",
                "code": "ARCHITECTURE_DECISION_REQUIRED",
                "message": (
                    "Encaminhamento registrado. A escrita estruturada da "
                    "ficha pelo solicitante sem engineering.access exige "
                    "decisão Core/Coordination antes de ser habilitada."
                ),
            }
        self._idempotent_store(
            actor=actor,
            operation="route_divergence",
            key=idempotency_key,
            fingerprint=fp,
            request_id=request_id,
            status=200,
            payload=response,
        )
        return response

    def get_record(self, record_id: str, *, actor: PrcActor) -> dict[str, Any]:
        _require_actor_read(actor)
        if not actor.is_analyst:
            raise PrcForbiddenError(
                "Ficha técnica restrita a analistas autorizados."
            )
        record = self._repo.get_record(record_id)
        if record is None:
            raise PrcNotFoundError("record", record_id)
        return record

    def list_revisions(
        self, record_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        if not actor.is_analyst:
            raise PrcForbiddenError("Revisões restritas a analistas.")
        self.get_record(record_id, actor=actor)
        items = self._repo.list_revisions(record_id)
        index = [
            {
                "revisionNumber": r["revision_number"],
                "requestId": r["request_id"],
                "approvedBy": r["approved_by_subject"],
                "approvedAt": r["approved_at"],
                "changedPaths": [c.get("path") for c in r.get("changes", [])],
            }
            for r in items
        ]
        return {"items": index, "total": len(index)}

    def get_revision(
        self, record_id: str, revision_number: int, *, actor: PrcActor
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        if not actor.is_analyst:
            raise PrcForbiddenError("Revisões restritas a analistas.")
        revision = self._repo.get_revision(record_id, revision_number)
        if revision is None:
            raise PrcNotFoundError("revision", f"{record_id}@{revision_number}")
        return revision

    # --- WORKFLOW ACTIONS ----------------------------------------------------------

    def _apply(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        action: str,
        expected_version: int,
        reason: str | None,
        set_fields: dict[str, Any] | None = None,
        event_meta: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        fp_extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request = self._get_scoped(request_id, actor)
        if not actor.has_action_permission(action):
            raise PrcForbiddenError(
                f"Sem permissão para a ação '{action}'."
            )
        fp = _fingerprint(
            {
                "action": action,
                "request_id": request_id,
                "expected_version": expected_version,
                "reason": reason,
                **(fp_extra or {}),
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation=action, key=idempotency_key, fingerprint=fp
        )
        if replay is not None:
            return replay
        next_status = transition_for(action, request["status"])
        if next_status is None:
            raise PrcStateConflictError("state_conflict")
        fields = dict(set_fields or {})
        if action == "start":
            fields["assigned_to_subject"] = actor.user_id
            fields["assigned_to_display_name"] = actor.label
        meta = {"action": action, "channel": actor.channel}
        meta.update(event_meta or {})
        updated = self._repo.apply_transition(
            request_id=request_id,
            expected_version=expected_version,
            allowed_from=frozenset({request["status"]}),
            actor_label=actor.label or actor.user_id,
            actor_subject=actor.user_id,
            actor_email=actor.email,
            event_type=_EVENT_TYPE_BY_ACTION.get(action, action),
            next_status=next_status,
            set_fields=fields,
            reason=reason,
            event_meta=meta,
        )
        response = self._detail(
            {**updated, "verifications": []}, actor, request_id=request_id
        )
        self._idempotent_store(
            actor=actor,
            operation=action,
            key=idempotency_key,
            fingerprint=fp,
            request_id=request_id,
            status=200,
            payload=response,
        )
        return response

    def start_request(self, request_id: str, *, actor: PrcActor,
                      expected_version: int, reason: str | None = None,
                      idempotency_key: str | None = None) -> dict[str, Any]:
        return self._apply(
            request_id, actor=actor, action="start",
            expected_version=expected_version, reason=reason,
            idempotency_key=idempotency_key,
        )

    def request_information(
        self, request_id: str, *, actor: PrcActor, expected_version: int,
        reason: str | None = None,
        pending_fields: list[str] | None = None,
        questions: list[dict[str, Any]] | None = None,
        message: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """PRC-REF-019 — abre rodada de esclarecimento tipada.

        ``questions`` é o contrato novo; sem perguntas, o motivo legado
        (+ ``pending_fields``) é convertido em perguntas FIELD/GENERAL
        (compatibilidade com Portal/EVA anteriores). ``pending_fields`` do
        evento continua derivado dos alvos tipados.
        """
        request = self._get_scoped(request_id, actor)
        if not actor.has_action_permission("request_information"):
            raise PrcForbiddenError(
                "Sem permissão para a ação 'request_information'."
            )
        reason_text = (reason or "").strip()[:1000]
        if questions:
            normalized = info_rounds.validate_questions_payload(questions)
        else:
            if not reason_text:
                raise PrcValidationError(
                    "Motivo é obrigatório.", fields={"reason": "required"}
                )
            normalized = info_rounds.legacy_questions_from_reason(
                reason=reason_text, pending_fields=pending_fields
            )
        round_message = info_rounds.validate_message(
            message if message is not None else reason_text
        )
        derived_fields = info_rounds.pending_fields_from_questions(normalized)
        fp = _fingerprint(
            {
                "action": "request_information",
                "request_id": request_id,
                "expected_version": expected_version,
                "reason": reason_text,
                "message": round_message,
                "questions": [
                    {
                        "targetKey": q["target_key"],
                        "text": q["question_text"],
                    }
                    for q in normalized
                ],
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation="request_information",
            key=idempotency_key, fingerprint=fp,
        )
        if replay is not None:
            return replay
        next_status = transition_for("request_information", request["status"])
        if next_status is None:
            raise PrcStateConflictError("state_conflict")
        now = _now()
        result = self._repo.create_information_round(
            request_id=request_id,
            expected_version=expected_version,
            allowed_from=frozenset({request["status"]}),
            next_status=next_status,
            actor_label=actor.label or actor.user_id,
            actor_subject=actor.user_id,
            actor_email=actor.email,
            event_type=_EVENT_TYPE_BY_ACTION["request_information"],
            reason=reason_text or round_message,
            event_meta={
                "action": "request_information",
                "channel": actor.channel,
                "pending_fields": derived_fields,
            },
            round_row={
                "id": _uuid(),
                "origin_status": request["status"],
                "parent_round_id": None,
                "requested_by_subject": actor.user_id,
                "requested_by_display_name": actor.label,
                "requester_subject": request["requester_subject"],
                "message": round_message,
                "created_at": now,
                "updated_at": now,
            },
            questions=normalized,
        )
        response = self._detail(
            {**result["request"], "verifications": []},
            actor,
            request_id=request_id,
        )
        response["informationRound"] = info_rounds.public_round_view(
            result["round"], include_internal=True
        )
        self._idempotent_store(
            actor=actor, operation="request_information",
            key=idempotency_key, fingerprint=fp, request_id=request_id,
            status=200, payload=response,
        )
        return response

    def return_for_correction(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        targets: list[dict[str, Any]],
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """PRC-REF-022 — devolve campos tipados ao solicitante."""
        request = self._get_scoped(request_id, actor)
        if not actor.is_analyst:
            raise PrcForbiddenError(
                "Somente a Engenharia autorizada pode devolver para correção."
            )
        if not actor.has_action_permission("return_for_correction"):
            raise PrcForbiddenError(
                "Sem permissão para a ação 'return_for_correction'."
            )
        normalized = corr_returns.validate_return_targets(targets)
        # Identidade exata: alvos SUPPLIER_LINK devem existir na ficha —
        # devolução nunca cria vínculo nem referencia fornecedor externo.
        draft_suppliers = (
            (request.get("draft") or {}).get("technical_data") or {}
        ).get("suppliers") or []
        known_links = {
            (
                str(s.get("supplierCode") or "").strip(),
                str(s.get("store") or "").strip(),
            )
            for s in draft_suppliers
            if isinstance(s, dict)
        }
        for t in normalized:
            if t["target_type"] != "SUPPLIER_LINK":
                continue
            key = (
                t["supplier_key"]["supplierCode"],
                t["supplier_key"]["store"],
            )
            if key not in known_links:
                raise PrcValidationError(
                    f"Vínculo {key[0]}/{key[1]} não encontrado na ficha "
                    "técnica — devolução exige vínculo existente.",
                    fields={"targets": "supplier_link_not_found"},
                )
        reason_text = (reason or "").strip()[:1000] or None
        fp = _fingerprint(
            {
                "action": "return_for_correction",
                "request_id": request_id,
                "expected_version": expected_version,
                "targets": [
                    {
                        "targetKey": t["target_key"],
                        "reason": t["reason"],
                    }
                    for t in normalized
                ],
                "reason": reason_text,
            }
        )
        replay = self._idempotent_replay(
            actor=actor,
            operation="return_for_correction",
            key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay
        if request["status"] != "in_progress":
            raise PrcStateConflictError("state_conflict")
        result = self._repo.create_correction_return(
            request_id=request_id,
            expected_version=expected_version,
            actor_subject=actor.user_id,
            actor_label=actor.label or actor.user_id,
            actor_email=actor.email,
            reason=reason_text,
            event_meta={
                "action": "return_for_correction",
                "channel": actor.channel,
            },
            return_row={"id": _uuid()},
            targets=normalized,
        )
        response = self._detail(
            {**result["request"], "verifications": []},
            actor,
            request_id=request_id,
        )
        response["correctionReturn"] = corr_returns.public_return_view(
            result["return"]
        )
        self._idempotent_store(
            actor=actor,
            operation="return_for_correction",
            key=idempotency_key,
            fingerprint=fp,
            request_id=request_id,
            status=200,
            payload=response,
        )
        return response

    def update_returned_fields(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        changes: list[dict[str, Any]],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """PRC-REF-022 — solicitante corrige apenas alvos devolvidos."""
        request = self._get_scoped(request_id, actor)
        if request["requester_subject"] != actor.user_id:
            raise PrcForbiddenError(
                "Somente o solicitante do chamado pode corrigir os campos "
                "devolvidos."
            )
        if not actor.has_action_permission("save_returned_fields"):
            raise PrcForbiddenError(
                "Sem permissão para corrigir campos devolvidos."
            )
        fp = _fingerprint(
            {
                "action": "save_returned_fields",
                "request_id": request_id,
                "expected_version": expected_version,
                "changes": changes,
            }
        )
        replay = self._idempotent_replay(
            actor=actor,
            operation="save_returned_fields",
            key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay
        if request["status"] != "needs_correction":
            raise PrcStateConflictError("state_conflict")
        open_ret = self._repo.get_open_correction_return(
            request_id=request_id
        )
        if open_ret is None:
            raise PrcStateConflictError("correction_return_missing")
        ret_targets = open_ret.get("targets") or []
        validated = corr_returns.validate_returned_changes(
            targets=ret_targets,
            changes=changes,
        )
        # Reusa validação canônica de draft para paths/valores (exceto
        # confirmação, que não aplica patch de valor). O path agregado
        # `suppliers` é validado granularmente abaixo — nunca libera a
        # lista inteira.
        draft_like = [
            {
                "path": c["path"],
                "proposedValue": c["proposedValue"],
                "reason": c["reason"],
            }
            for c in validated
            if c["mode"] != "confirmed" and c["path"] != "suppliers"
        ]
        if draft_like:
            catalog.validate_update_changes(draft_like)
        supplier_targets = [
            t for t in ret_targets if t.get("target_type") == "SUPPLIER_LINK"
        ]
        addressed_supplier_keys: set[str] = set()
        current_suppliers = (
            (request.get("draft") or {}).get("technical_data") or {}
        ).get("suppliers") or []
        for idx, change in enumerate(validated):
            if change["path"] != "suppliers":
                continue
            if change["mode"] == "confirmed":
                # Confirmação explícita: o solicitante ratifica os
                # valores vigentes de todos os vínculos devolvidos.
                addressed_supplier_keys.update(
                    str(t.get("target_key") or "")
                    for t in supplier_targets
                )
                continue
            merged, addressed = corr_returns.validate_supplier_correction(
                targets=ret_targets,
                current_suppliers=current_suppliers,
                proposed=change["proposedValue"],
                change_index=idx,
            )
            change["proposedValue"] = merged
            addressed_supplier_keys.update(addressed)
        updated = self._repo.update_returned_fields(
            request_id=request_id,
            expected_version=expected_version,
            actor_subject=actor.user_id,
            actor_display_name=actor.label,
            actor_email=actor.email,
            changes=validated,
            addressed_supplier_keys=addressed_supplier_keys,
            event_meta={"channel": actor.channel},
        )
        response = self._detail(
            {**updated, "verifications": []},
            actor,
            request_id=request_id,
        )
        self._idempotent_store(
            actor=actor,
            operation="save_returned_fields",
            key=idempotency_key,
            fingerprint=fp,
            request_id=request_id,
            status=200,
            payload=response,
        )
        return response

    def resubmit_correction(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """PRC-REF-022 — reenvia correções e retorna a in_progress."""
        request = self._get_scoped(request_id, actor)
        if request["requester_subject"] != actor.user_id:
            raise PrcForbiddenError(
                "Somente o solicitante do chamado pode reenviar a correção."
            )
        if not actor.has_action_permission("resubmit_correction"):
            raise PrcForbiddenError(
                "Sem permissão para reenviar correção "
                "(ARCHITECTURE_DECISION_REQUIRED)."
            )
        fp = _fingerprint(
            {
                "action": "resubmit_correction",
                "request_id": request_id,
                "expected_version": expected_version,
            }
        )
        replay = self._idempotent_replay(
            actor=actor,
            operation="resubmit_correction",
            key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay
        if request["status"] != "needs_correction":
            raise PrcStateConflictError("state_conflict")
        open_ret = self._repo.get_open_correction_return(
            request_id=request_id
        )
        if open_ret is None:
            raise PrcStateConflictError("correction_return_missing")
        targets = open_ret.get("targets") or []
        if not corr_returns.all_targets_addressed(targets):
            raise PrcValidationError(
                "Trate todos os campos devolvidos antes de reenviar.",
                fields={"targets": "unaddressed"},
            )
        result = self._repo.resubmit_correction(
            request_id=request_id,
            expected_version=expected_version,
            actor_subject=actor.user_id,
            actor_label=actor.label or actor.user_id,
            actor_email=actor.email,
            event_meta={
                "action": "resubmit_correction",
                "channel": actor.channel,
            },
        )
        response = self._detail(
            {**result["request"], "verifications": []},
            actor,
            request_id=request_id,
        )
        response["correctionReturn"] = corr_returns.public_return_view(
            result["return"]
        )
        self._idempotent_store(
            actor=actor,
            operation="resubmit_correction",
            key=idempotency_key,
            fingerprint=fp,
            request_id=request_id,
            status=200,
            payload=response,
        )
        return response

    def list_correction_returns(
        self, request_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        self._get_scoped(request_id, actor)
        rows = self._repo.list_correction_returns(request_id=request_id)
        return {
            "items": [corr_returns.public_return_view(r) for r in rows],
            "total": len(rows),
        }

    def get_correction_return(
        self, request_id: str, return_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        self._get_scoped(request_id, actor)
        row = self._repo.get_correction_return(
            request_id=request_id, return_id=return_id
        )
        if row is None:
            raise PrcNotFoundError("correction_return", return_id)
        return corr_returns.public_return_view(row)

    def resume_request(self, request_id: str, *, actor: PrcActor,
                       expected_version: int, reason: str | None = None,
                       idempotency_key: str | None = None) -> dict[str, Any]:
        """Retoma o caso (``needs_information`` → ``in_progress``).

        PRC-REF-019: enquanto houver rodada de esclarecimento aberta
        (``awaiting_requester``/``awaiting_review``) o resume é bloqueado
        com ``state_conflict``. Única exceção: dispensa explícita do
        analista — ``reason`` iniciando com ``waiver:`` — registrada no
        evento (``information_waiver``) para auditoria. Escopo e permissão
        são validados antes do gate para não vazar a existência de rodadas.
        """
        self._get_scoped(request_id, actor)
        if not actor.has_action_permission("resume"):
            raise PrcForbiddenError("Sem permissão para a ação 'resume'.")
        rounds = self._repo.list_information_rounds(request_id=request_id)
        event_meta: dict[str, Any] | None = None
        if info_rounds.has_open_information_blocker(rounds):
            waiver = (reason or "").strip().lower().startswith("waiver:")
            if not waiver:
                raise PrcStateConflictError("information_round_open")
            open_ids = [
                r["id"]
                for r in rounds
                if r.get("status")
                in ("awaiting_requester", "awaiting_review")
            ]
            self._repo.resolve_open_information_rounds(
                request_id=request_id,
                actor_subject=actor.user_id,
                actor_display_name=actor.label,
                event=self._info_event(
                    actor,
                    "information.round_resolved",
                    meta={
                        "waiver": True,
                        "openRoundIds": open_ids,
                    },
                ),
            )
            event_meta = {
                "information_waiver": True,
                "open_round_ids": open_ids,
            }
        return self._apply(
            request_id, actor=actor, action="resume",
            expected_version=expected_version, reason=reason,
            event_meta=event_meta, idempotency_key=idempotency_key,
        )

    def submit_review(self, request_id: str, *, actor: PrcActor,
                      expected_version: int, reason: str | None = None,
                      idempotency_key: str | None = None) -> dict[str, Any]:
        """LEGADO — ``in_progress → under_review``.

        PRC-REF-020 remove a etapa operacional de revisão. O endpoint
        permanece por compatibilidade de consumidores antigos; não entra
        em ``allowedActions`` do fluxo novo. Preferir ``complete``.
        """
        request = self._get_scoped(request_id, actor)
        draft = request.get("draft") or {}
        data = draft.get("technical_data") or {}
        if request["request_type"] == "create":
            missing = [
                spec.path
                for spec in catalog.FIELD_SPECS
                if spec.required_create_intake
                and spec.path not in data
                or (
                    spec.required_create_intake
                    and spec.kind not in ("text", "suppliers")
                    and not str(data.get(spec.path) or "").strip()
                )
            ]
            if missing:
                raise PrcValidationError(
                    "Ficha técnica incompleta para revisão.",
                    fields={p: "required" for p in missing},
                )
        return self._apply(
            request_id, actor=actor, action="submit_review",
            expected_version=expected_version, reason=reason,
            idempotency_key=idempotency_key,
        )

    def return_to_attendance(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """PRC-REF-020 — reabre legado ``under_review`` → ``in_progress``."""
        return self._apply(
            request_id,
            actor=actor,
            action="return_to_attendance",
            expected_version=expected_version,
            reason=reason,
            idempotency_key=idempotency_key,
        )

    def reject_request(self, request_id: str, *, actor: PrcActor,
                       expected_version: int, reason: str,
                       idempotency_key: str | None = None) -> dict[str, Any]:
        if not (reason or "").strip():
            raise PrcValidationError(
                "Rejeição exige motivo.", fields={"reason": "required"}
            )
        return self._apply(
            request_id, actor=actor, action="reject",
            expected_version=expected_version,
            reason=reason.strip()[:1000],
            idempotency_key=idempotency_key,
        )

    def update_draft(
        self, request_id: str, *, actor: PrcActor, expected_version: int,
        changes: list[dict[str, Any]], idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        request = self._get_scoped(request_id, actor)
        if not actor.has_action_permission("edit_draft"):
            raise PrcForbiddenError("Sem permissão para editar o draft.")
        # FIX-08 — edição livre pré-atendimento é do criador do caso:
        # analista de terceiro não reescreve ficha alheia nem em
        # ``submitted``; o estado é revalidado atomicamente pelo CAS do
        # repositório (``submitted`` + expected_version).
        if actor.user_id != request.get("requester_subject"):
            raise PrcForbiddenError(
                "Somente o solicitante do caso pode editar a ficha."
            )
        validated = catalog.validate_update_changes(changes)
        # FIX-08 — em casos ``update`` a relação de fornecedores é
        # governada por ``supplierLinkChanges`` (verify compara ops vs
        # leitura oficial). A edição informa a lista final desejada;
        # o backend deriva e valida as ops contra o baseline oficial,
        # nunca confia em ops montadas no cliente.
        extra_draft_fields: dict[str, Any] | None = None
        if request.get("request_type") == "update":
            supplier_change = next(
                (c for c in validated if c["path"] == "suppliers"), None
            )
            if supplier_change is not None:
                baseline = request.get("official_baseline") or {}
                ops = catalog.derive_supplier_link_ops(
                    baseline.get("links") or [],
                    supplier_change["proposedValue"],
                )
                ops, ops_err = catalog.validate_supplier_link_changes(ops)
                if ops_err:
                    raise PrcValidationError(
                        ops_err, fields={"suppliers": "invalid"}
                    )
                baseline_err = (
                    sa5_baseline.validate_link_ops_against_baseline(
                        ops, baseline
                    )
                )
                if baseline_err:
                    raise PrcValidationError(
                        baseline_err,
                        fields={"suppliers": "baseline_precondition"},
                    )
                extra_draft_fields = {"supplierLinkChanges": ops}
        # CORRECTION-10 — edição de caso CREATE em ``submitted`` não pode
        # salvar estado final sem fornecedor (remoção do último vínculo).
        # A regra só dispara quando ``suppliers`` está no change set:
        # casos legados incompletos seguem legíveis/editáveis em outros
        # campos — sem deadlock retroativo.
        elif request.get("request_type") == "create":
            supplier_change = next(
                (c for c in validated if c["path"] == "suppliers"), None
            )
            if supplier_change is not None and not supplier_change[
                "proposedValue"
            ]:
                raise PrcValidationError(
                    "A ficha de cadastro exige ao menos um fornecedor.",
                    fields={"suppliers": "required"},
                )
        fp = _fingerprint(
            {
                "action": "update_draft",
                "request_id": request_id,
                "expected_version": expected_version,
                "changes": validated,
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation="update_draft",
            key=idempotency_key, fingerprint=fp,
        )
        if replay is not None:
            return replay
        updated = self._repo.update_draft(
            request_id=request_id,
            expected_version=expected_version,
            actor_subject=actor.user_id,
            changes=validated,
            extra_draft_fields=extra_draft_fields,
            event_meta={"channel": actor.channel},
            actor_display_name=actor.label,
            actor_email=actor.email,
        )
        response = self._detail(
            {**updated, "verifications": []}, actor, request_id=request_id
        )
        self._idempotent_store(
            actor=actor, operation="update_draft", key=idempotency_key,
            fingerprint=fp, request_id=request_id, status=200,
            payload=response,
        )
        return response

    async def _capture_update_baseline(
        self,
        *,
        actor: PrcActor,
        official_code: str,
        access_token: str | None,
        correlation_id: str,
        client_fingerprint: Any,
        require_links_complete: bool,
    ) -> dict[str, Any]:
        """D15 — lê e congela o estado oficial no momento do intake."""
        if self._reader is None:
            raise PrcOfficialError(
                "unavailable",
                "Leitor oficial não configurado para capturar baseline.",
            )
        if not (access_token or "").strip():
            raise PrcOfficialError(
                "unavailable",
                "Token de acesso ausente para leitura oficial do baseline.",
            )
        observed = await self._reader.read_product(
            access_token=access_token,
            request_id=correlation_id,
            official_code=official_code,
        )
        status = observed.get("status")
        if status != "available":
            kind = {
                "not_found": "not_found",
                "forbidden": "forbidden",
                "timeout": "timeout",
                "contract_error": "contract_error",
            }.get(status, "unavailable")
            raise PrcOfficialError(
                kind,
                "Baseline oficial indisponível — formalização bloqueada "
                f"({kind}).",
            )
        links_complete = bool(observed.get("suppliers_complete", True))
        if require_links_complete and not links_complete:
            raise PrcOfficialError(
                "unverifiable",
                "Consulta SA5 incompleta — baseline não pode comprovar "
                "ausência/presença de vínculos.",
            )
        captured = sa5_baseline.build_official_baseline(
            observed,
            official_code=official_code,
            captured_by=actor.user_id,
            correlation_id=correlation_id,
            captured_at=_now(),
        )
        client_fp = str(client_fingerprint or "").strip()
        if client_fp and client_fp != captured.get("fingerprint"):
            raise PrcConcurrencyError("official_context_stale")
        return captured

    # --- COMPLETE (verificação oficial + conclusão) — PRC-REF-020 ---------------

    async def complete_attendance(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        official_code: str | None,
        reason: str | None,
        access_token: str,
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Única operação de conclusão verificada (rótulo: Concluir atendimento).

        Pré-condição: ``in_progress`` (ou legado ``under_review``). Executa
        validação técnica + leitura oficial fresca + comparação integral;
        só então publica revisão e marca ``completed``. Falha bloqueante
        preserva o status atual (preferencialmente ``in_progress``) e
        registra a tentativa — sem revisão publicada.
        """
        return await self._complete_with_official_verification(
            request_id,
            actor=actor,
            expected_version=expected_version,
            official_code=official_code,
            reason=reason,
            access_token=access_token,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            action_name="complete",
        )

    async def verify_and_complete(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        official_code: str | None,
        reason: str | None,
        access_token: str,
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Alias legado de ``complete_attendance`` (mesmo use case)."""
        return await self._complete_with_official_verification(
            request_id,
            actor=actor,
            expected_version=expected_version,
            official_code=official_code,
            reason=reason,
            access_token=access_token,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            action_name="verify_and_complete",
        )

    async def _complete_with_official_verification(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        official_code: str | None,
        reason: str | None,
        access_token: str,
        correlation_id: str,
        idempotency_key: str | None = None,
        action_name: str = "complete",
    ) -> dict[str, Any]:
        _require_actor_verify(actor)
        request = self._get_scoped(request_id, actor)
        if request["status"] not in _COMPLETE_FROM:
            raise PrcStateConflictError("state_conflict")
        if not actor.has_action_permission(action_name):
            raise PrcForbiddenError(
                f"Sem permissão para a ação '{action_name}'."
            )
        # REF-019: não concluir com rodada de esclarecimento aberta.
        rounds = self._repo.list_information_rounds(request_id=request_id)
        if info_rounds.has_open_information_blocker(rounds):
            raise PrcStateConflictError("information_round_open")
        # PRC-REF-017 — CREATE exige código informado na conclusão;
        # UPDATE trava no código oficial da solicitação/baseline.
        #
        # Identidade CREATE: o contrato oficial (api-delpi → SB1/SA5)
        # não expõe proveniência de criação amarrada ao requestId.
        # Gate vigente = código informado + existência + correspondência
        # integral dos campos verificáveis. Proveniência inequívoca de
        # "criado neste atendimento" permanece PENDING_OWNER até o ERP
        # disponibilizar evidência autorizada (sem inventar campos).
        existing_code = (
            str(request.get("official_product_code") or "").strip()
        )
        provided = str(official_code or "").strip()
        if request["request_type"] == "update":
            if not existing_code:
                raise PrcValidationError(
                    "Solicitação UPDATE sem código oficial baseline.",
                    fields={"officialCode": "required"},
                )
            if provided and provided != existing_code:
                raise PrcValidationError(
                    "UPDATE não permite troca arbitrária de officialCode "
                    "na conclusão.",
                    fields={"officialCode": "immutable"},
                )
            code = existing_code
        else:
            code = provided or existing_code
            if not code:
                raise PrcValidationError(
                    "Informe o código oficial atribuído no TOTVS após o "
                    "cadastro manual.",
                    fields={"officialCode": "required"},
                )
        try:
            code = catalog.normalize_code(code, max_length=60)
        except PrcValidationError:
            raise PrcValidationError(
                "officialCode inválido.",
                fields={"officialCode": "invalid"},
            )
        if self._reader is None:
            raise PrcOfficialError(
                "unavailable", "Leitor oficial não configurado."
            )
        draft = request.get("draft") or {}
        data = draft.get("technical_data") or {}
        link_ops = data.get("supplierLinkChanges") or []
        # D15 — conclusão REMOVE permanece PENDING_OWNER mesmo com
        # ausência comprovável no read-back.
        if (
            sa5_baseline.remove_ops_present(link_ops)
            and not sa5_baseline.SA5_REMOVE_COMPLETION_ALLOWED
        ):
            raise PrcStateConflictError(
                "remove_completion_pending_owner"
            )
        expected_paths = self._expected_verify_paths(request, data)
        if not expected_paths and (
            (draft.get("changed_paths") or [])
            or (data.get("supplierLinkChanges") or [])
        ):
            raise PrcStateConflictError(
                "integrity_error: solicitação com mudanças efetivas sem "
                "conjunto de verificação."
            )
        # PRC-REF-022-FIX-01 — gate PN: nenhum vínculo registrado ou
        # alterado pode ser ratificado sem partNumber válido. Vínculos
        # intocados pelo caso preservam o legado. Fail-closed antes da
        # leitura oficial.
        if "suppliers" in expected_paths:
            baseline_links = (
                (request.get("official_baseline") or {}).get("links")
                or []
            )
            pn_err = sa5_baseline.validate_completion_part_numbers(
                draft_suppliers=data.get("suppliers") or [],
                link_ops=link_ops,
                baseline_links=baseline_links,
            )
            if pn_err:
                raise PrcValidationError(
                    pn_err,
                    fields={"suppliers": "partNumber_required"},
                )
        observed = await self._reader.read_product(
            access_token=access_token,
            request_id=correlation_id,
            official_code=code,
        )
        status = observed.get("status")
        if status != "available":
            kind = {
                "not_found": "not_found",
                "forbidden": "forbidden",
                "timeout": "timeout",
                "contract_error": "contract_error",
            }.get(status, "unavailable")
            verification = self._persist_verification(
                request_id=request_id, actor=actor, official_code=code,
                expected_paths=expected_paths, result=kind,
                field_results={}, observed=None,
                correlation_id=correlation_id,
            )
            self._reopen_legacy_review_after_failed_complete(
                request_id, actor=actor, expected_version=expected_version,
            )
            raise PrcOfficialError(
                kind,
                "Produto não confirmado na fonte oficial "
                f"({kind}).",
                verification=verification,
            )
        field_results, all_ok, has_unverifiable = self._compare(
            request, data, expected_paths, observed
        )
        if not all_ok:
            result = "unverifiable" if has_unverifiable else "mismatched"
            verification = self._persist_verification(
                request_id=request_id, actor=actor, official_code=code,
                expected_paths=expected_paths, result=result,
                field_results=field_results,
                observed={
                    "product": observed.get("product"),
                    "suppliers": observed.get("suppliers"),
                },
                correlation_id=correlation_id,
            )
            self._reopen_legacy_review_after_failed_complete(
                request_id, actor=actor, expected_version=expected_version,
            )
            if has_unverifiable:
                raise PrcOfficialError(
                    "unverifiable",
                    "Campos sem leitura oficial autorizada impedem a "
                    "conclusão.",
                    verification=verification,
                    field_results=field_results,
                )
            raise PrcOfficialError(
                "mismatch",
                "Divergência entre a ficha técnica e o cadastro oficial.",
                verification=verification,
                field_results=field_results,
            )
        verification_payload = {
            "official_product_code": code,
            "requested_by_subject": actor.user_id,
            "checked_at": _now(),
            "official_source": catalog.OFFICIAL_SOURCE,
            "result": "matched",
            "expected_fields": expected_paths,
            "observed_fields": {
                "product": observed.get("product"),
                "suppliers": observed.get("suppliers"),
            },
            "field_results": field_results,
            "evidence_fingerprint": _fingerprint(
                {
                    "code": code,
                    "expected": expected_paths,
                    "observed": observed.get("product"),
                    "suppliers": observed.get("suppliers"),
                }
            ),
            "correlation_id": correlation_id,
        }
        snapshot = self._build_snapshot(request, data)
        changes = self._revision_changes(request, data)
        try:
            outcome = self._repo.complete_request(
                request_id=request_id,
                expected_version=expected_version,
                actor_subject=actor.user_id,
                actor_display_name=actor.label,
                actor_email=actor.email,
                official_code=code,
                official_source=catalog.OFFICIAL_SOURCE,
                base_revision=request.get("base_revision_number"),
                revision_snapshot=snapshot,
                revision_changes=changes,
                verification=verification_payload,
                reason=reason,
                event_meta={"channel": actor.channel},
            )
        except PrcStateConflictError:
            raise
        record = outcome["record"]
        revision = outcome["revision"]
        self._emit_change(
            request_id, reason=action_name, actor=actor
        )
        return {
            "status": "completed",
            "requestId": request_id,
            "recordId": record["id"],
            "revisionNumber": revision["revision_number"],
            "verifiedAt": verification_payload["checked_at"],
            "verificationId": outcome["verification"]["id"],
            "officialCode": code,
        }

    def _expected_verify_paths(
        self, request: dict, draft_data: dict[str, Any]
    ) -> list[str]:
        if request["request_type"] == "create":
            return [
                spec.path
                for spec in catalog.FIELD_SPECS
                if spec.path != "officialProductCode"
                and spec.path in draft_data
            ]
        paths = [
            spec.path
            for spec in catalog.FIELD_SPECS
            if spec.path != "officialProductCode"
            and any(
                c.get("path") == spec.path
                for c in (request.get("draft") or {}).get("changed_paths", [])
            )
        ]
        # P0-D13: ops SA5 entram no conjunto obrigatório de verificação
        # mesmo sem change escalar "suppliers" — senão a solicitação
        # concluiria sem nenhuma comparação.
        if (draft_data.get("supplierLinkChanges")
                and "suppliers" not in paths):
            paths.append("suppliers")
        return paths

    def _compare(
        self,
        request: dict,
        draft_data: dict[str, Any],
        expected_paths: list[str],
        observed: dict[str, Any],
    ) -> tuple[dict[str, Any], bool, bool]:
        product = observed.get("product") or {}
        suppliers = observed.get("suppliers") or []
        # PRC-REF-017 — baseline/antes para coluna UPDATE na evidência.
        baseline = request.get("official_baseline") or {}
        baseline_fields = (
            (baseline.get("fields") or {})
            if isinstance(baseline, dict) else {}
        )
        field_results: dict[str, Any] = {}
        all_ok = True
        has_unverifiable = False
        for path in expected_paths:
            spec = catalog.FIELD_INDEX[path]
            previous_value = None
            if request.get("request_type") == "update":
                entry = baseline_fields.get(path)
                if isinstance(entry, dict) and "value" in entry:
                    previous_value = entry.get("value")
                else:
                    for ch in (request.get("draft") or {}).get(
                        "changed_paths", []
                    ) or []:
                        if ch.get("path") == path and "originalValue" in ch:
                            previous_value = ch.get("originalValue")
                            break
            if not spec.verifiable:
                field_results[path] = {
                    "result": "unverifiable",
                    "officialField": spec.official_field,
                    "reason": "contract_gap",
                    "previous": previous_value,
                    "expected": draft_data.get(path),
                    "observed": None,
                }
                all_ok = False
                has_unverifiable = True
                continue
            if spec.kind == "suppliers":
                link_ops = draft_data.get("supplierLinkChanges")
                if link_ops:
                    comparison = compare_link_ops(
                        link_ops, suppliers,
                        complete=observed.get("suppliers_complete", True),
                    )
                else:
                    comparison = catalog.compare_suppliers(
                        draft_data.get(path) or [], suppliers
                    )
                field_results[path] = {
                    "result": comparison["result"],
                    "officialField": "SA5",
                    "detail": comparison["detail"],
                    "previous": baseline.get("links") or baseline.get("suppliers"),
                    "expected": draft_data.get(path) or link_ops,
                    "observed": suppliers,
                }
                if comparison["result"] != "matched":
                    all_ok = False
                continue
            observed_value = product.get(spec.official_field)
            if observed_value is None:
                field_results[path] = {
                    "result": "unverifiable",
                    "officialField": spec.official_field,
                    "reason": "field_absent",
                    "previous": previous_value,
                    "expected": draft_data.get(path),
                    "observed": None,
                }
                all_ok = False
                has_unverifiable = True
                continue
            expected_value = draft_data.get(path)
            matched = catalog.scalar_values_match(
                spec, expected_value, observed_value
            )
            field_results[path] = {
                "result": "matched" if matched else "mismatched",
                "officialField": spec.official_field,
                "previous": previous_value,
                "expected": expected_value,
                "observed": observed_value,
                "reason": None if matched else "mismatch",
            }
            if not matched:
                all_ok = False
        return field_results, all_ok, has_unverifiable

    def _persist_verification(
        self,
        *,
        request_id: str,
        actor: PrcActor,
        official_code: str,
        expected_paths: list[str],
        result: str,
        field_results: dict[str, Any],
        observed: dict[str, Any] | None,
        correlation_id: str,
    ) -> dict[str, Any]:
        return self._repo.insert_verification(
            request_id=request_id,
            verification={
                "official_product_code": official_code,
                "requested_by_subject": actor.user_id,
                "checked_at": _now(),
                "official_source": catalog.OFFICIAL_SOURCE,
                "result": result,
                "expected_fields": expected_paths,
                "observed_fields": observed,
                "field_results": field_results,
                "evidence_fingerprint": _fingerprint(
                    {"code": official_code, "result": result,
                     "fields": field_results}
                ),
                "correlation_id": correlation_id,
                "error_code": result if result != "matched" else None,
            },
        )

    def _reopen_legacy_review_after_failed_complete(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
    ) -> None:
        """PRC-REF-020 — falha de conclusão em legado ``under_review``
        reabre para ``in_progress`` (atendimento permanece aberto)."""
        current = self._repo.get_request(request_id)
        if not current or current.get("status") != "under_review":
            return
        try:
            self._apply(
                request_id,
                actor=actor,
                action="return_to_attendance",
                expected_version=int(
                    current.get("row_version") or expected_version
                ),
                reason=(
                    "PRC-REF-020: verificação oficial bloqueou a conclusão "
                    "— atendimento reaberto."
                ),
            )
        except PrcStateConflictError:
            # Concorrência: status já mudou; falha de verificação permanece.
            return
        except PrcConcurrencyError:
            return

    def _build_snapshot(
        self, request: dict, draft_data: dict[str, Any]
    ) -> dict[str, Any]:
        snapshot = dict(draft_data)
        if request["request_type"] == "create":
            snapshot.pop("officialProductCode", None)
        return snapshot

    def _revision_changes(
        self, request: dict, draft_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if request["request_type"] == "create":
            return [
                {
                    "path": p,
                    "before": None,
                    "after": v,
                    "reason": "initial_registration",
                }
                for p, v in sorted(draft_data.items())
                if p != "officialProductCode"
            ]
        record = self._repo.get_record_by_official_code(
            official_source=catalog.OFFICIAL_SOURCE,
            official_code=request.get("official_product_code") or "",
        )
        before = {}
        if record is not None:
            current = self._repo.get_revision(
                record["id"], int(record["current_revision_number"])
            )
            before = (current or {}).get("technical_snapshot") or {}
        return [
            {
                "path": c["path"],
                "before": before.get(c["path"]),
                "after": draft_data.get(c["path"]),
                "reason": c.get("reason", ""),
            }
            for c in (request.get("draft") or {}).get("changed_paths", [])
        ]

    # --- REFERENCE DATA + OUTBOUND ---------------------------------------------------

    async def edit_context(
        self,
        *,
        actor: PrcActor,
        official_code: str,
        access_token: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Contexto oficial de edição (D12): valores atuais SB1 +
        vínculos SA5 completos, via leitor oficial delegado."""
        _require_actor_read(actor)
        code = official_code.strip()
        if not code:
            raise PrcValidationError(
                "officialCode é obrigatório.",
                fields={"officialCode": "required"},
            )
        if self._reader is None:
            raise PrcOfficialError(
                "unavailable", "Leitor oficial não configurado."
            )
        observed = await self._reader.read_product(
            access_token=access_token,
            request_id=correlation_id,
            official_code=code,
        )
        if observed.get("status") != "available":
            return {
                "status": observed.get("status"),
                "reason": observed.get("reason"),
                "officialCode": code,
            }
        captured = sa5_baseline.build_official_baseline(
            observed,
            official_code=code,
            captured_by=actor.user_id,
            correlation_id=correlation_id,
            captured_at=_now(),
        )
        return {
            "status": "available",
            "officialCode": code,
            "readAt": captured["readAt"],
            "officialSource": catalog.OFFICIAL_SOURCE,
            "baselineVersion": captured["baselineVersion"],
            "sourceContractVersion": captured["sourceContractVersion"],
            "fingerprint": captured["fingerprint"],
            "fields": {
                path: {
                    "value": meta.get("value"),
                    "officialField": meta.get("officialField"),
                }
                for path, meta in (captured.get("fields") or {}).items()
            },
            "links": [
                {
                    "supplierCode": item["supplierCode"],
                    "store": item["store"],
                    "supplierName": item.get("supplierName") or "",
                    "supplierShortName": item.get("supplierShortName") or "",
                    "partNumber": item.get("partNumber") or "",
                    "catalogNumber": item.get("catalogNumber") or "",
                }
                for item in (captured.get("links") or [])
            ],
            "linksComplete": bool(captured.get("linksComplete")),
            "removeCompletionPolicy": (
                sa5_baseline.SA5_REMOVE_COMPLETION_POLICY
            ),
        }

    def reference_data(self, *, actor: PrcActor) -> dict[str, Any]:
        _require_actor_read(actor)
        return {
            "schemaVersion": catalog.PAYLOAD_SCHEMA_VERSION,
            "productTypes": list(catalog.PRODUCT_TYPES),
            "requestTypes": list(REQUEST_TYPES),
            "statuses": [
                "submitted", "in_progress", "needs_information",
                "under_review", "completed", "rejected",
            ],
            "sources": list(self._sources),
            "fields": [
                {
                    "path": s.path,
                    "kind": s.kind,
                    "requiredCreateIntake": s.required_create_intake,
                    "verifiable": s.verifiable,
                    "officialField": s.official_field,
                    "enumValues": list(s.enum_values) or None,
                    "maxLength": s.max_length,
                    "note": s.note or None,
                }
                for s in catalog.FIELD_SPECS
            ],
            "editableDraftPaths": sorted(catalog.EDITABLE_DRAFT_PATHS),
            "supplierKeys": {
                "required": list(catalog.SUPPLIER_REQUIRED_KEYS),
                "optional": list(catalog.SUPPLIER_OPTIONAL_KEYS),
            },
            "permissions": {
                "access": "engineering.access",
                "manager": "engineering.manager",
            },
        }

    def outbound_request(
        self, request_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        request = self._get_scoped(request_id, actor)
        result: dict[str, Any] = {
            "requestId": request["id"],
            "requestType": request["request_type"],
            "status": request["status"],
            "source": request["source"],
            "externalRequestId": request.get("external_request_id"),
            "officialCode": request.get("official_product_code"),
            "createdAt": request["created_at"],
            "completedAt": request.get("completed_at"),
        }
        if request["status"] == "completed" and request.get(
            "completed_record_id"
        ):
            record = self._repo.get_record(request["completed_record_id"])
            if record:
                result["verifiedAt"] = record["last_official_verified_at"]
                result["revisionNumber"] = record[
                    "current_revision_number"
                ]
                result["recordId"] = record["id"]
        verifs = self._repo.list_verifications(request_id)
        if verifs:
            last = verifs[-1]
            result["lastVerification"] = {
                "result": last["result"],
                "checkedAt": last["checked_at"],
            }
        return result

    def outbound_list(
        self, *, actor: PrcActor, source: str | None, page: int, page_size: int
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        if actor.is_analyst:
            requester = None
        else:
            requester = actor.user_id
        result = self._repo.list_requests(
            source=source,
            requester_subject=requester,
            global_scope=actor.is_analyst,
            page=page,
            page_size=page_size,
        )
        return {
            "items": [
                {
                    "requestId": i["id"],
                    "requestType": i["requestType"],
                    "status": i["status"],
                    "source": i["source"],
                    "createdAt": i["createdAt"],
                    "officialCode": i["officialCode"],
                }
                for i in result["items"]
            ],
            "page": result["page"],
            "pageSize": result["pageSize"],
            "total": result["total"],
        }

    # --- ATTENDANCE FLAGS (D16) -----------------------------------------------

    def _flag_actor_gate(self, actor: PrcActor) -> None:
        """Bandeiras são operacionais — exige process (access)."""
        _require_actor_process(actor)

    def list_flags(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        status: str | None = None,
        subject: str | None = None,
        target_path: str | None = None,
        target_attribute: str | None = None,
        supplier_code: str | None = None,
        store: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        self._flag_actor_gate(actor)
        self._get_scoped(request_id, actor)
        if status is not None and status not in ("OPEN", "RESOLVED", "all"):
            raise PrcValidationError(
                "status inválido.", fields={"status": "enum"}
            )
        filt = None if status in (None, "all") else status
        raw = self._repo.list_flags(
            request_id=request_id,
            status=filt,
            subject=subject,
            target_path=target_path,
            target_attribute=target_attribute,
            supplier_code=supplier_code,
            store=store,
            page=page,
            page_size=page_size,
        )
        return {
            "items": [
                attendance_flags.public_flag(item) for item in raw["items"]
            ],
            "page": raw["page"],
            "pageSize": raw["pageSize"],
            "total": raw["total"],
            "openCount": raw["openCount"],
            "resolvedCount": raw["resolvedCount"],
            "hasMore": raw["hasMore"],
        }

    def list_flags_cross_case(
        self,
        *,
        actor: PrcActor,
        status: str | None = None,
        subject: str | None = None,
        target_path: str | None = None,
        target_attribute: str | None = None,
        product_code: str | None = None,
        request_id: str | None = None,
        request_type: str | None = None,
        request_status: str | None = None,
        assignee: str | None = None,
        supplier_code: str | None = None,
        store: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        """Consulta transversal com AuthZ por caso no servidor."""
        self._flag_actor_gate(actor)
        if status is not None and status not in ("OPEN", "RESOLVED", "all"):
            raise PrcValidationError(
                "status inválido.", fields={"status": "enum"}
            )
        filt = None if status in (None, "all") else status
        accessible_ids: list[str] | None = None
        if not actor.is_analyst:
            # Escopo do solicitante: IDs dos próprios casos.
            owned = self._repo.list_requests(
                page=1, page_size=5000,
                requester_subject=actor.user_id,
                global_scope=False,
            )
            accessible_ids = [str(i["id"]) for i in owned.get("items") or []]
        raw = self._repo.list_flags_cross_case(
            accessible_request_ids=accessible_ids,
            global_scope=actor.is_analyst,
            status=filt,
            subject=subject,
            target_path=target_path,
            target_attribute=target_attribute,
            product_code=product_code,
            request_id=request_id,
            request_type=request_type,
            request_status=request_status,
            assignee=assignee,
            supplier_code=supplier_code,
            store=store,
            created_from=created_from,
            created_to=created_to,
            page=page,
            page_size=page_size,
        )
        items = []
        for item in raw["items"]:
            pub = attendance_flags.public_flag(item)
            pub["productCode"] = item.get("product_code")
            pub["requestType"] = item.get("request_type")
            pub["requestStatus"] = item.get("request_status")
            pub["productDescription"] = item.get("product_description")
            items.append(pub)
        return {
            "items": items,
            "page": raw["page"],
            "pageSize": raw["pageSize"],
            "total": raw["total"],
            "openCount": raw["openCount"],
            "resolvedCount": raw["resolvedCount"],
            "distinctRequestCount": raw["distinctRequestCount"],
            "distinctProductCount": raw["distinctProductCount"],
            "hasMore": raw["hasMore"],
        }

    def summarize_flags_cross_case(
        self,
        *,
        actor: PrcActor,
        group_by: str = "request",
        status: str | None = None,
        subject: str | None = None,
        target_path: str | None = None,
        target_attribute: str | None = None,
        product_code: str | None = None,
        request_status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        self._flag_actor_gate(actor)
        if status is not None and status not in ("OPEN", "RESOLVED", "all"):
            raise PrcValidationError(
                "status inválido.", fields={"status": "enum"}
            )
        filt = None if status in (None, "all") else status
        accessible_ids: list[str] | None = None
        if not actor.is_analyst:
            owned = self._repo.list_requests(
                page=1, page_size=5000,
                requester_subject=actor.user_id,
                global_scope=False,
            )
            accessible_ids = [str(i["id"]) for i in owned.get("items") or []]
        return self._repo.summarize_flags_cross_case(
            accessible_request_ids=accessible_ids,
            global_scope=actor.is_analyst,
            group_by=group_by,
            status=filt,
            subject=subject,
            target_path=target_path,
            target_attribute=target_attribute,
            product_code=product_code,
            request_status=request_status,
            page=page,
            page_size=page_size,
        )

    def get_flag(
        self, request_id: str, flag_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        self._flag_actor_gate(actor)
        self._get_scoped(request_id, actor)
        row = self._repo.get_flag(request_id=request_id, flag_id=flag_id)
        if row is None:
            raise PrcNotFoundError("flag", flag_id)
        return attendance_flags.public_flag(row)

    def create_flag(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        title: str,
        description: str,
        subject: str = "FIELD",
        target_path: str | None = None,
        supplier_key: dict | None = None,
        target_attribute: str | None = None,
        idempotency_key: str | None = None,
        allow_general: bool = False,
    ) -> dict[str, Any]:
        self._flag_actor_gate(actor)
        request = self._get_scoped(request_id, actor)
        if (
            request["status"] in ("completed", "rejected")
            and not attendance_flags.FLAG_MUTATION_AFTER_TERMINAL
        ):
            raise PrcStateConflictError("state_conflict")
        now = _now()
        flag_id = _uuid()
        payload = attendance_flags.validate_flag_payload(
            title=title,
            description=description,
            subject=subject,
            target_path=target_path,
            supplier_key=supplier_key,
            target_attribute=target_attribute,
            allow_general=allow_general,
            flag_id=flag_id,
        )
        fp = _fingerprint(
            {
                "request_id": request_id,
                "op": "flag_create",
                "payload": payload,
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation="flag_create", key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay
        existing = self._repo.find_open_flag_by_target(
            request_id=request_id, target_key=payload["targetKey"],
        )
        if existing is not None:
            raise PrcStateConflictError("open_flag_exists")
        row = {
            "id": flag_id,
            "request_id": request_id,
            "title": payload["title"],
            "description": payload["description"],
            "status": "OPEN",
            "subject": payload["subject"],
            "target_path": payload.get("targetPath"),
            "target_attribute": payload.get("targetAttribute"),
            "supplier_key": payload.get("supplierKey"),
            "target_key": payload["targetKey"],
            "row_version": 1,
            "created_by_subject": actor.user_id,
            "created_by_display_name": actor.label,
            "created_at": now,
            "updated_by_subject": actor.user_id,
            "updated_by_display_name": actor.label,
            "updated_at": now,
            "resolved_by_subject": None,
            "resolved_by_display_name": None,
            "resolved_at": None,
            "deleted_by_subject": None,
            "deleted_by_display_name": None,
            "deleted_at": None,
        }
        event = {
            "event_type": "flag.created",
            "actor_subject": actor.user_id,
            "actor_display_name": actor.label,
            "actor_email": actor.email,
            "reason": None,
            "metadata": {
                "channel": actor.channel,
                "flagId": flag_id,
                "title": payload["title"],
                "subject": payload["subject"],
                "targetPath": payload.get("targetPath"),
                "targetAttribute": payload.get("targetAttribute"),
                "targetKey": payload["targetKey"],
            },
            "previous_status": None,
            "next_status": "OPEN",
        }
        created = self._repo.create_flag(flag=row, event=event)
        response = attendance_flags.public_flag(created)
        self._idempotent_store(
            actor=actor, operation="flag_create", key=idempotency_key,
            fingerprint=fp, request_id=request_id, status=201,
            payload=response,
        )
        return response

    def update_flag(
        self,
        request_id: str,
        flag_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        title: str | None = None,
        description: str | None = None,
        subject: str | None = None,
        target_path: Any = ...,
        supplier_key: Any = ...,
        target_attribute: Any = ...,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Edita título/descrição. Alvo é imutável (REF-01)."""
        self._flag_actor_gate(actor)
        self._get_scoped(request_id, actor)
        current = self._repo.get_flag(request_id=request_id, flag_id=flag_id)
        if current is None:
            raise PrcNotFoundError("flag", flag_id)
        # Rejeitar tentativa de retarget via PATCH comum.
        if subject is not None and subject != current.get("subject"):
            raise PrcValidationError(
                "Alvo da bandeira é imutável; use operação de retarget.",
                fields={"subject": "immutable"},
            )
        if target_path is not ... and target_path != current.get("target_path"):
            raise PrcValidationError(
                "Alvo da bandeira é imutável; use operação de retarget.",
                fields={"targetPath": "immutable"},
            )
        if (
            supplier_key is not ...
            and supplier_key != current.get("supplier_key")
        ):
            raise PrcValidationError(
                "Alvo da bandeira é imutável; use operação de retarget.",
                fields={"supplierKey": "immutable"},
            )
        if (
            target_attribute is not ...
            and target_attribute != current.get("target_attribute")
        ):
            raise PrcValidationError(
                "Alvo da bandeira é imutável; use operação de retarget.",
                fields={"targetAttribute": "immutable"},
            )
        payload = attendance_flags.validate_flag_payload(
            title=title if title is not None else current["title"],
            description=(
                description if description is not None
                else current["description"]
            ),
            subject=current["subject"],
            target_path=current.get("target_path"),
            supplier_key=current.get("supplier_key"),
            target_attribute=current.get("target_attribute"),
            allow_general=current["subject"] == "GENERAL",
            flag_id=flag_id,
        )
        fp = _fingerprint(
            {
                "request_id": request_id,
                "flag_id": flag_id,
                "op": "flag_update",
                "expected_version": expected_version,
                "payload": {
                    "title": payload["title"],
                    "description": payload["description"],
                },
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation="flag_update", key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay
        patch = {
            "title": payload["title"],
            "description": payload["description"],
        }
        event = {
            "event_type": "flag.updated",
            "actor_subject": actor.user_id,
            "actor_display_name": actor.label,
            "actor_email": actor.email,
            "reason": None,
            "metadata": {
                "channel": actor.channel,
                "flagId": flag_id,
                "after": {"title": patch["title"]},
            },
            "previous_status": current["status"],
            "next_status": current["status"],
        }
        updated = self._repo.update_flag(
            request_id=request_id,
            flag_id=flag_id,
            expected_version=expected_version,
            patch=patch,
            actor_subject=actor.user_id,
            actor_display_name=actor.label,
            event=event,
        )
        response = attendance_flags.public_flag(updated)
        self._idempotent_store(
            actor=actor, operation="flag_update", key=idempotency_key,
            fingerprint=fp, request_id=request_id, status=200,
            payload=response,
        )
        return response

    def resolve_flag(
        self,
        request_id: str,
        flag_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return self._transition_flag(
            request_id, flag_id, actor=actor,
            expected_version=expected_version, next_status="RESOLVED",
            event_type="flag.resolved", reason=reason,
            idempotency_key=idempotency_key, operation="flag_resolve",
        )

    def reopen_flag(
        self,
        request_id: str,
        flag_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return self._transition_flag(
            request_id, flag_id, actor=actor,
            expected_version=expected_version, next_status="OPEN",
            event_type="flag.reopened", reason=reason,
            idempotency_key=idempotency_key, operation="flag_reopen",
        )

    def _transition_flag(
        self,
        request_id: str,
        flag_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        next_status: str,
        event_type: str,
        reason: str | None,
        idempotency_key: str | None,
        operation: str,
    ) -> dict[str, Any]:
        self._flag_actor_gate(actor)
        self._get_scoped(request_id, actor)
        fp = _fingerprint(
            {
                "request_id": request_id,
                "flag_id": flag_id,
                "op": operation,
                "expected_version": expected_version,
                "next_status": next_status,
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation=operation, key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay
        event = {
            "event_type": event_type,
            "actor_subject": actor.user_id,
            "actor_display_name": actor.label,
            "actor_email": actor.email,
            "reason": reason,
            "metadata": {
                "channel": actor.channel,
                "flagId": flag_id,
            },
            "previous_status": None,
            "next_status": next_status,
        }
        updated = self._repo.transition_flag(
            request_id=request_id,
            flag_id=flag_id,
            expected_version=expected_version,
            next_status=next_status,
            actor_subject=actor.user_id,
            actor_display_name=actor.label,
            event=event,
        )
        response = attendance_flags.public_flag(updated)
        self._idempotent_store(
            actor=actor, operation=operation, key=idempotency_key,
            fingerprint=fp, request_id=request_id, status=200,
            payload=response,
        )
        return response

    def delete_flag(
        self,
        request_id: str,
        flag_id: str,
        *,
        actor: PrcActor,
        expected_version: int,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        self._flag_actor_gate(actor)
        self._get_scoped(request_id, actor)
        fp = _fingerprint(
            {
                "request_id": request_id,
                "flag_id": flag_id,
                "op": "flag_delete",
                "expected_version": expected_version,
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation="flag_delete", key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay
        event = {
            "event_type": "flag.deleted",
            "actor_subject": actor.user_id,
            "actor_display_name": actor.label,
            "actor_email": actor.email,
            "reason": None,
            "metadata": {
                "channel": actor.channel,
                "flagId": flag_id,
            },
            "previous_status": None,
            "next_status": None,
        }
        deleted = self._repo.soft_delete_flag(
            request_id=request_id,
            flag_id=flag_id,
            expected_version=expected_version,
            actor_subject=actor.user_id,
            actor_display_name=actor.label,
            event=event,
        )
        response = {
            "id": deleted["id"],
            "requestId": request_id,
            "deleted": True,
            "version": int(deleted["row_version"]),
        }
        self._idempotent_store(
            actor=actor, operation="flag_delete", key=idempotency_key,
            fingerprint=fp, request_id=request_id, status=200,
            payload=response,
        )
        return response

    # --- INFORMATION ROUNDS (PRC-REF-019) --------------------------------------
    #
    # AuthZ (backend decide; cliente nunca é autoridade):
    # - analista (``is_analyst``): abre rodada, aceita, pede complemento e
    #   lista/lê todas as rodadas dos casos no seu escopo;
    # - draft/submit: SOMENTE o solicitante do caso (``actor.user_id ==
    #   request.requester_subject``), mesmo que o ator também seja analista,
    #   e somente em rodada ``awaiting_requester`` destinada a ele;
    # - leitura por solicitante (escopo do caso) devolve as rodadas; as
    #   bandeiras D16 são recurso separado e nunca entram nesta view.

    @staticmethod
    def _require_info_analyst(actor: PrcActor) -> None:
        _require_actor_process(actor)
        if not actor.is_analyst:
            raise PrcForbiddenError(
                "Operação restrita a analistas autorizados."
            )

    def _require_info_requester(
        self, request_id: str, actor: PrcActor
    ) -> dict[str, Any]:
        """Escopo + identidade do solicitante do caso (draft/submit)."""
        _require_actor_read(actor)
        request = self._get_scoped(request_id, actor)
        if request["requester_subject"] != actor.user_id:
            raise PrcForbiddenError(
                "Somente o solicitante do caso pode responder."
            )
        return request

    def _load_info_round_or_404(
        self, request_id: str, round_id: str
    ) -> dict[str, Any]:
        rnd = self._repo.get_information_round(
            request_id=request_id, round_id=round_id
        )
        if rnd is None:
            raise PrcNotFoundError("information_round", round_id)
        return rnd

    def _load_requester_round(
        self, request_id: str, round_id: str, actor: PrcActor
    ) -> dict[str, Any]:
        """Rodada aguardando o solicitante e destinada ao ator."""
        rnd = self._load_info_round_or_404(request_id, round_id)
        if rnd.get("requester_subject") != actor.user_id:
            raise PrcForbiddenError("Rodada não destinada ao ator.")
        if not info_rounds.round_allows_requester_write(rnd["status"]):
            raise PrcStateConflictError("state_conflict")
        return rnd

    @staticmethod
    def _info_event(
        actor: PrcActor,
        event_type: str,
        meta: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        return {
            "event_type": event_type,
            "actor_subject": actor.user_id,
            "actor_display_name": actor.label,
            "actor_email": actor.email,
            "reason": reason,
            "metadata": {"channel": actor.channel, **(meta or {})},
        }

    @staticmethod
    def _normalize_answers(
        answers: Any, *, for_submit: bool
    ) -> list[dict[str, str]]:
        """Normaliza ``answers[]`` (``questionId`` + ``text``).

        Rascunho aceita texto vazio (limpa a resposta); envio exige texto
        não vazio em cada item informado — a completude por pergunta é
        validada atomicamente pelo repositório (payload + rascunhos).
        """
        if answers is None:
            answers = []
        if not isinstance(answers, list):
            raise PrcValidationError(
                "answers deve ser uma lista.", fields={"answers": "type"}
            )
        if not answers and not for_submit:
            raise PrcValidationError(
                "Informe ao menos uma resposta.",
                fields={"answers": "required"},
            )
        out: list[dict[str, str]] = []
        seen: set[str] = set()
        for idx, raw in enumerate(answers):
            if not isinstance(raw, dict):
                raise PrcValidationError(
                    f"Resposta {idx + 1} inválida.",
                    fields={f"answers[{idx}]": "type"},
                )
            qid = str(
                raw.get("questionId") or raw.get("question_id") or ""
            ).strip()
            if not qid:
                raise PrcValidationError(
                    "questionId é obrigatório.",
                    fields={f"answers[{idx}].questionId": "required"},
                )
            if qid in seen:
                raise PrcValidationError(
                    "Pergunta repetida no payload.",
                    fields={f"answers[{idx}].questionId": "duplicate"},
                )
            seen.add(qid)
            field_key = f"answers[{idx}].text"
            if for_submit:
                text = info_rounds.validate_answer_text(
                    raw.get("text"), field_key=field_key
                )
            else:
                text = str(raw.get("text") or "").strip()
                if len(text) > info_rounds.ANSWER_TEXT_MAX:
                    raise PrcValidationError(
                        "Resposta excede "
                        f"{info_rounds.ANSWER_TEXT_MAX} caracteres.",
                        fields={field_key: "max_length"},
                    )
            out.append({"question_id": qid, "text": text})
        return out

    def list_information_rounds(
        self, request_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        self._get_scoped(request_id, actor)
        rounds = self._repo.list_information_rounds(request_id=request_id)
        return {
            "items": [
                info_rounds.public_round_view(
                    r, include_internal=actor.is_analyst
                )
                for r in rounds
            ],
            "total": len(rounds),
            "hasOpenBlocker": info_rounds.has_open_information_blocker(
                rounds
            ),
        }

    def get_information_round(
        self, request_id: str, round_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        _require_actor_read(actor)
        self._get_scoped(request_id, actor)
        rnd = self._load_info_round_or_404(request_id, round_id)
        return info_rounds.public_round_view(
            rnd, include_internal=actor.is_analyst
        )

    def _save_answers(
        self,
        request_id: str,
        round_id: str,
        *,
        actor: PrcActor,
        expected_round_version: int,
        answers: Any,
        idempotency_key: str | None,
        submit: bool,
    ) -> dict[str, Any]:
        self._require_info_requester(request_id, actor)
        normalized = self._normalize_answers(answers, for_submit=submit)
        operation = "information_submit" if submit else "information_draft"
        fp = _fingerprint(
            {
                "request_id": request_id,
                "round_id": round_id,
                "op": operation,
                "expected_round_version": expected_round_version,
                "answers": normalized,
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation=operation, key=idempotency_key,
            fingerprint=fp,
        )
        if replay is not None:
            return replay
        # Replay antes do gate de estado: reenvio idempotente após sucesso.
        self._load_requester_round(request_id, round_id, actor)
        event = self._info_event(
            actor,
            "information.answers_submitted" if submit
            else "information.answers_drafted",
            meta={"roundId": round_id},
        )
        repo_fn = (
            self._repo.submit_information_answers if submit
            else self._repo.save_information_answers_draft
        )
        saved = repo_fn(
            request_id=request_id,
            round_id=round_id,
            expected_round_version=expected_round_version,
            actor_subject=actor.user_id,
            answers=normalized,
            event=event,
        )
        response = info_rounds.public_round_view(saved)
        self._idempotent_store(
            actor=actor, operation=operation, key=idempotency_key,
            fingerprint=fp, request_id=request_id, status=200,
            payload=response,
        )
        return response

    def draft_information_answers(
        self,
        request_id: str,
        round_id: str,
        *,
        actor: PrcActor,
        expected_round_version: int,
        answers: list[dict[str, Any]],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Salva rascunho de respostas (somente o solicitante do caso)."""
        return self._save_answers(
            request_id, round_id, actor=actor,
            expected_round_version=expected_round_version,
            answers=answers, idempotency_key=idempotency_key, submit=False,
        )

    def submit_information_answers(
        self,
        request_id: str,
        round_id: str,
        *,
        actor: PrcActor,
        expected_round_version: int,
        answers: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Envia respostas (todas as perguntas exigem texto não vazio)."""
        return self._save_answers(
            request_id, round_id, actor=actor,
            expected_round_version=expected_round_version,
            answers=answers, idempotency_key=idempotency_key, submit=True,
        )

    def accept_information_question(
        self,
        request_id: str,
        round_id: str,
        question_id: str,
        *,
        actor: PrcActor,
        expected_round_version: int,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Analista aceita o esclarecimento de uma pergunta."""
        self._require_info_analyst(actor)
        self._get_scoped(request_id, actor)
        fp = _fingerprint(
            {
                "request_id": request_id,
                "round_id": round_id,
                "question_id": question_id,
                "op": "information_accept",
                "expected_round_version": expected_round_version,
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation="information_accept",
            key=idempotency_key, fingerprint=fp,
        )
        if replay is not None:
            return replay
        rnd = self._load_info_round_or_404(request_id, round_id)
        if not info_rounds.round_allows_analyst_review(rnd["status"]):
            raise PrcStateConflictError("state_conflict")
        saved = self._repo.accept_information_question(
            request_id=request_id,
            round_id=round_id,
            question_id=question_id,
            expected_round_version=expected_round_version,
            actor_subject=actor.user_id,
            actor_display_name=actor.label,
            event=self._info_event(
                actor, "information.question_accepted",
                meta={"roundId": round_id, "questionId": question_id},
            ),
        )
        response = info_rounds.public_round_view(
            saved, include_internal=True
        )
        self._idempotent_store(
            actor=actor, operation="information_accept",
            key=idempotency_key, fingerprint=fp, request_id=request_id,
            status=200, payload=response,
        )
        return response

    def request_information_follow_up(
        self,
        request_id: str,
        parent_round_id: str,
        *,
        actor: PrcActor,
        expected_parent_version: int,
        questions: list[dict[str, Any]],
        follow_up_question_ids: list[str],
        message: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Analista pede complemento: marca perguntas do pai como
        ``follow_up_requested`` e abre nova rodada (caso permanece
        ``needs_information``)."""
        self._require_info_analyst(actor)
        request = self._get_scoped(request_id, actor)
        normalized = info_rounds.validate_questions_payload(questions)
        if not isinstance(follow_up_question_ids, list):
            raise PrcValidationError(
                "followUpQuestionIds deve ser uma lista.",
                fields={"followUpQuestionIds": "type"},
            )
        target_ids: list[str] = []
        for raw in follow_up_question_ids:
            qid = str(raw or "").strip()
            if qid and qid not in target_ids:
                target_ids.append(qid)
        if not target_ids:
            raise PrcValidationError(
                "Informe ao menos uma pergunta para complemento.",
                fields={"followUpQuestionIds": "required"},
            )
        round_message = info_rounds.validate_message(message)
        fp = _fingerprint(
            {
                "request_id": request_id,
                "parent_round_id": parent_round_id,
                "op": "information_follow_up",
                "expected_parent_version": expected_parent_version,
                "message": round_message,
                "followUpQuestionIds": sorted(target_ids),
                "questions": [
                    {
                        "targetKey": q["target_key"],
                        "text": q["question_text"],
                    }
                    for q in normalized
                ],
            }
        )
        replay = self._idempotent_replay(
            actor=actor, operation="information_follow_up",
            key=idempotency_key, fingerprint=fp,
        )
        if replay is not None:
            return replay
        # Gates de estado após o replay idempotente.
        if request["status"] != "needs_information":
            raise PrcStateConflictError("state_conflict")
        parent = self._load_info_round_or_404(request_id, parent_round_id)
        if not info_rounds.round_allows_analyst_review(parent["status"]):
            raise PrcStateConflictError("state_conflict")
        parent_questions = {q["id"]: q for q in parent.get("questions") or []}
        for qid in target_ids:
            question = parent_questions.get(qid)
            if question is None:
                raise PrcNotFoundError("information_question", qid)
            if question.get("status") != "submitted":
                raise PrcStateConflictError("state_conflict")
        now = _now()
        created = self._repo.create_information_follow_up(
            request_id=request_id,
            parent_round_id=parent_round_id,
            expected_parent_version=expected_parent_version,
            actor_label=actor.label or actor.user_id,
            actor_subject=actor.user_id,
            actor_email=actor.email,
            event=self._info_event(
                actor, "information.follow_up_requested",
                meta={"pending_fields": (
                    info_rounds.pending_fields_from_questions(normalized)
                )},
                reason=round_message,
            ),
            round_row={
                "id": _uuid(),
                "origin_status": request["status"],
                "parent_round_id": parent_round_id,
                "requested_by_subject": actor.user_id,
                "requested_by_display_name": actor.label,
                "requester_subject": request["requester_subject"],
                "message": round_message,
                "created_at": now,
                "updated_at": now,
            },
            questions=normalized,
            follow_up_question_ids=target_ids,
        )
        response = {
            "parentRound": info_rounds.public_round_view(
                created["parentRound"], include_internal=True
            ),
            "round": info_rounds.public_round_view(
                created["round"], include_internal=True
            ),
        }
        self._idempotent_store(
            actor=actor, operation="information_follow_up",
            key=idempotency_key, fingerprint=fp, request_id=request_id,
            status=201, payload=response,
        )
        return response

    # --- PRC-REF-023 — documentos opcionais de apoio ---------------------

    def _require_attachment_storage(self):
        if self._storage is None:
            raise PrcValidationError(
                "Armazenamento de documentos não configurado.",
                fields={"attachments": "storage_unavailable"},
            )
        return self._storage

    def list_attachments(
        self, request_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        request = self._get_scoped(request_id, actor)
        rows = self._repo.list_attachments(request_id=request_id)
        visible = [
            r for r in rows
            if r["state"] in ("AVAILABLE", "PENDING_SCAN", "REJECTED")
        ]
        return {
            "requestId": request_id,
            "attachments": [attachments_mod.attachment_to_api(r) for r in visible],
            "canUpload": self._can_upload_attachment(request, actor),
        }

    def _can_upload_attachment(self, request: dict, actor: PrcActor) -> bool:
        return (
            actor.user_id == request.get("requester_subject")
            and request.get("status") in attachments_mod.ATTACHMENT_UPLOAD_STATUSES
        )

    def upload_attachment(
        self,
        request_id: str,
        *,
        actor: PrcActor,
        filename: str | None,
        content: bytes,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Upload governado: valida por conteúdo → grava bytes → persiste
        vínculo. Só o solicitante do caso anexa (estados aprovados).
        Dedup idempotente por (caso, sha256, nome)."""
        request = self._get_scoped(request_id, actor)
        storage = self._require_attachment_storage()
        if actor.user_id != request.get("requester_subject"):
            raise PrcForbiddenError(
                "Somente o solicitante do caso pode anexar documentos."
            )
        if request.get("status") not in attachments_mod.ATTACHMENT_UPLOAD_STATUSES:
            raise PrcStateConflictError(
                "attachments_not_allowed_state"
            )
        existing = self._repo.list_attachments(request_id=request_id)
        try:
            meta = attachments_mod.validate_attachment(
                filename=filename,
                content=content,
                current_count=len(existing),
            )
        except ValueError as exc:
            code = str(exc)
            raise PrcValidationError(
                attachments_mod.attachment_error(code),
                fields={"file": code},
            ) from exc
        dup = self._repo.find_attachment_by_hash(
            request_id=request_id,
            sha256=str(meta["sha256"]),
            original_file_name=str(meta["original_file_name"]),
        )
        if dup is not None:
            return {
                "attachment": attachments_mod.attachment_to_api(dup),
                "deduplicated": True,
            }
        attachment_id = _uuid()
        storage_key = f"{request_id}/{attachment_id}{meta['extension']}"
        try:
            storage.save(storage_key, content)
        except Exception as exc:
            raise PrcValidationError(
                "Storage de documentos indisponível no momento.",
                fields={"file": "storage_unavailable"},
            ) from exc
        row = {
            "id": attachment_id,
            "request_id": request_id,
            "original_file_name": meta["original_file_name"],
            "media_type": meta["media_type"],
            "size_bytes": meta["size_bytes"],
            "sha256": meta["sha256"],
            "storage_key": storage_key,
            "state": "AVAILABLE",
            "uploaded_by_subject": actor.user_id,
            "uploaded_by_display_name": actor.label,
            "uploaded_by_email": actor.email,
            "correlation_id": correlation_id,
            "created_at": _now(),
        }
        try:
            row = self._repo.create_attachment(attachment=row)
        except Exception:
            # Falha parcial: bytes gravados sem vínculo → limpar órfão.
            try:
                storage.delete(storage_key)
            except Exception:
                pass
            raise
        self._emit_change(
            request_id, reason="attachment_upload", actor=actor
        )
        return {
            "attachment": attachments_mod.attachment_to_api(row),
            "deduplicated": False,
        }

    def download_attachment(
        self, request_id: str, attachment_id: str, *, actor: PrcActor
    ) -> dict[str, Any]:
        """Retorna metadado + handle de bytes para streaming autenticado.
        Estado AVAILABLE apenas; identidade composta request+attachment."""
        self._get_scoped(request_id, actor)
        storage = self._require_attachment_storage()
        row = self._repo.get_attachment(
            request_id=request_id, attachment_id=attachment_id
        )
        if row is None:
            raise PrcNotFoundError("attachment", attachment_id)
        if row["state"] != "AVAILABLE":
            raise PrcStateConflictError("attachment_not_available")
        try:
            handle = storage.open_path(row["storage_key"])
        except Exception as exc:
            raise PrcValidationError(
                "Arquivo indisponível no storage.",
                fields={"file": "storage_unavailable"},
            ) from exc
        return {
            "meta": attachments_mod.attachment_to_api(row),
            "handle": handle,
        }


_FIELD_MAP = {
    "partNumber": "supplier_part_number",
    "catalogNumber": "catalog_code",
}


def compare_link_ops(
    ops: list[dict[str, Any]],
    observed: list[dict[str, Any]],
    *,
    complete: bool = True,
) -> dict[str, Any]:
    """Verificação seletiva de ops granulares SA5 (D12 / PRC-REF-020-UX-01).

    `update`: o vínculo oficial deve existir único e cada atributo
    informado deve bater. `add`: o vínculo deve existir (criado
    manualmente) com os atributos propostos. Vínculos fora do change
    set nunca reprovam a verificação. Conjunto oficial incompleto →
    unverifiable (não é possível comprovar a relação).

    ``detail`` permanece compatível (``key``/``result``) e adiciona
    ``supplierCode``, ``store``, ``operation``, ``attributes`` tipados
    para diagnóstico UX — sem comparação no cliente.
    """
    detail: list[dict[str, Any]] = []
    result = "matched"
    if not complete:
        return {
            "result": "unverifiable",
            "detail": [{
                "result": "official_links_incomplete",
                "reasonCode": "official_links_incomplete",
            }],
        }
    by_key: dict[tuple[str, str], list[dict]] = {}
    for item in observed or []:
        if isinstance(item, dict):
            key = (
                str(item.get("supplier_code") or "").strip(),
                str(item.get("supplier_store") or "").strip(),
            )
            by_key.setdefault(key, []).append(item)
    for op in ops or []:
        code = str(op["key"]["supplierCode"]).strip()
        store = str(op["key"]["store"]).strip()
        key = (code, store)
        operation = str(op.get("operation") or "")
        label = f"{operation}:{code}.{store}"
        base = {
            "key": label,
            "supplierCode": code,
            "store": store,
            "operation": operation,
            "supplierKey": {"supplierCode": code, "store": store},
        }
        found = by_key.get(key, [])
        if operation == "remove":
            if not found:
                detail.append({**base, "result": "matched", "attributes": []})
            else:
                result = "mismatched"
                detail.append({
                    **base,
                    "result": "still_present_official",
                    "reasonCode": "still_present_official",
                    "attributes": [],
                })
            continue
        if not found:
            result = "mismatched"
            detail.append({
                **base,
                "result": "missing_in_official",
                "reasonCode": "missing_in_official",
                "attributes": [],
            })
            continue
        if len(found) > 1:
            result = "mismatched"
            detail.append({
                **base,
                "result": "ambiguous_official",
                "reasonCode": "ambiguous_official",
                "attributes": [],
            })
            continue
        link = found[0]
        attributes: list[dict[str, Any]] = []
        bad_tokens: list[str] = []
        for field, official_key in _FIELD_MAP.items():
            if field not in op["fields"]:
                continue
            exp = (op["fields"][field] or "").strip()
            if official_key not in link:
                result = "mismatched"
                bad_tokens.append(f"{field}:unverifiable")
                attributes.append({
                    "attribute": field,
                    "expected": exp,
                    "observed": None,
                    "result": "unverifiable",
                    "reasonCode": "field_absent",
                })
                continue
            obs_raw = link.get(official_key)
            obs = str(obs_raw if obs_raw is not None else "").strip()
            attr_result = "matched" if exp == obs else "mismatched"
            if attr_result != "matched":
                result = "mismatched"
                bad_tokens.append(f"{field}:mismatched")
            attributes.append({
                "attribute": field,
                "expected": exp,
                "observed": obs,
                "result": attr_result,
                "reasonCode": (
                    "mismatch" if attr_result == "mismatched" else None
                ),
            })
        link_result = "mismatched" if bad_tokens else "matched"
        if bad_tokens:
            result = "mismatched"
        detail.append({
            **base,
            "result": ",".join(bad_tokens) if bad_tokens else "matched",
            "linkResult": link_result,
            "fields": [a["attribute"] for a in attributes
                       if a["result"] != "matched"],
            "attributes": attributes,
        })
    return {"result": result, "detail": detail}
