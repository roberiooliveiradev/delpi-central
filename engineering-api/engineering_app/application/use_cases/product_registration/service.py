"""Use cases do Product Registration — intake, fila, workflow, verify.

Regras do contrato §5–§8: solicitação ≠ cadastro; draft ≠ revisão;
revisão imutável só nasce de verificação ``matched``; alteração seletiva
nunca exige ficha inteira; rejeição não toca a ficha vigente; falha de
verificação nunca publica revisão.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from engineering_app.application.ports.product_registration import (
    OfficialProductReaderPort,
    ProductRegistrationRepository,
)
from engineering_app.domain.product_registration import catalog
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
    REQUEST_TYPES,
    PrcActor,
    transition_for,
)

_ALLOWED_SOURCES_DEFAULT = (
    "portal-engineering",
    "eva",
    "engineering-test",
)

_EVENT_TYPE_BY_ACTION = {
    "start": "started",
    "request_information": "information_requested",
    "resume": "resumed",
    "submit_review": "submitted_for_review",
    "reject": "rejected",
}


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


class ProductRegistrationService:
    """Casos de uso do módulo — mesma implementação REST/EVA."""

    def __init__(
        self,
        repository: ProductRegistrationRepository,
        *,
        official_reader: OfficialProductReaderPort | None = None,
        allowed_sources: tuple[str, ...] | None = None,
    ) -> None:
        self._repo = repository
        self._reader = official_reader
        self._sources = allowed_sources or _ALLOWED_SOURCES_DEFAULT

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
        if not key:
            return
        self._repo.save_idempotent(
            actor_or_source=actor.user_id,
            operation=operation,
            idempotency_key=key,
            request_fingerprint=fingerprint,
            request_id=request_id,
            response_status=status,
            response_payload=payload,
        )

    # --- INTAKE ------------------------------------------------------------------

    def submit_request(
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
            }
            if not changes and not link_ops:
                raise PrcValidationError(
                    "UPDATE exige ao menos uma alteração efetiva.",
                    fields={"changes": "required"},
                )

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
        return _request_detail(request, actor)

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
        return {"items": items, "total": len(items)}

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
        response = _request_detail(
            {**updated, "verifications": []}, actor
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
        reason: str, pending_fields: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not (reason or "").strip():
            raise PrcValidationError(
                "Motivo é obrigatório.", fields={"reason": "required"}
            )
        meta = {"pending_fields": list(pending_fields or [])}
        return self._apply(
            request_id, actor=actor, action="request_information",
            expected_version=expected_version,
            reason=reason.strip()[:1000], event_meta=meta,
            idempotency_key=idempotency_key,
        )

    def resume_request(self, request_id: str, *, actor: PrcActor,
                       expected_version: int, reason: str | None = None,
                       idempotency_key: str | None = None) -> dict[str, Any]:
        return self._apply(
            request_id, actor=actor, action="resume",
            expected_version=expected_version, reason=reason,
            idempotency_key=idempotency_key,
        )

    def submit_review(self, request_id: str, *, actor: PrcActor,
                      expected_version: int, reason: str | None = None,
                      idempotency_key: str | None = None) -> dict[str, Any]:
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
        _require_actor_process(actor)
        request = self._get_scoped(request_id, actor)
        if not actor.has_action_permission("edit_draft"):
            raise PrcForbiddenError("Sem permissão para editar o draft.")
        validated = catalog.validate_update_changes(changes)
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
            event_meta={"channel": actor.channel},
            actor_display_name=actor.label,
            actor_email=actor.email,
        )
        response = _request_detail({**updated, "verifications": []}, actor)
        self._idempotent_store(
            actor=actor, operation="update_draft", key=idempotency_key,
            fingerprint=fp, request_id=request_id, status=200,
            payload=response,
        )
        return response

    # --- VERIFY AND COMPLETE --------------------------------------------------------

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
        _require_actor_verify(actor)
        request = self._get_scoped(request_id, actor)
        if request["status"] != "under_review":
            raise PrcStateConflictError("state_conflict")
        code = (official_code or request.get("official_product_code") or "")
        if not code.strip():
            raise PrcValidationError(
                "officialCode obrigatório para verificação.",
                fields={"officialCode": "required"},
            )
        code = code.strip()
        if self._reader is None:
            raise PrcOfficialError(
                "unavailable", "Leitor oficial não configurado."
            )
        draft = request.get("draft") or {}
        data = draft.get("technical_data") or {}
        expected_paths = self._expected_verify_paths(request, data)
        if not expected_paths and (
            (draft.get("changed_paths") or [])
            or (data.get("supplierLinkChanges") or [])
        ):
            raise PrcStateConflictError(
                "integrity_error: solicitação com mudanças efetivas sem "
                "conjunto de verificação."
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
                "Divergência entre a ficha aprovada e o cadastro oficial.",
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
        field_results: dict[str, Any] = {}
        all_ok = True
        has_unverifiable = False
        for path in expected_paths:
            spec = catalog.FIELD_INDEX[path]
            if not spec.verifiable:
                field_results[path] = {
                    "result": "unverifiable",
                    "officialField": spec.official_field,
                    "reason": "contract_gap",
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
                "expected": expected_value,
                "observed": observed_value,
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
        product = observed.get("product") or {}
        links = [
            {
                "supplierCode": str(i.get("supplier_code") or ""),
                "store": str(i.get("supplier_store") or ""),
                "supplierName": str(i.get("supplier_name") or ""),
                "supplierShortName": str(
                    i.get("supplier_short_name") or ""
                ),
                "partNumber": str(i.get("supplier_part_number") or ""),
                "catalogNumber": str(i.get("catalog_code") or ""),
            }
            for i in (observed.get("suppliers") or [])
            if isinstance(i, dict)
        ]
        fields = {
            spec.path: {
                "value": product.get(spec.official_field),
                "officialField": spec.official_field,
            }
            for spec in catalog.FIELD_SPECS
            if spec.official_field and spec.kind != "suppliers"
        }
        return {
            "status": "available",
            "officialCode": code,
            "readAt": _now(),
            "officialSource": catalog.OFFICIAL_SOURCE,
            "fields": fields,
            "links": links,
            "linksComplete": bool(observed.get("suppliers_complete")),
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
    """Verificação seletiva de ops granulares SA5 (D12).

    `update`: o vínculo oficial deve existir único e cada atributo
    informado deve bater. `add`: o vínculo deve existir (criado
    manualmente) com os atributos propostos. Vínculos fora do change
    set nunca reprovam a verificação. Conjunto oficial incompleto →
    unverifiable (não é possível comprovar a relação).
    """
    detail: list[dict[str, Any]] = []
    result = "matched"
    if not complete:
        return {
            "result": "unverifiable",
            "detail": [{"result": "official_links_incomplete"}],
        }
    by_key: dict[tuple[str, str], list[dict]] = {}
    for item in observed or []:
        if isinstance(item, dict):
            key = (
                str(item.get("supplier_code") or "").strip(),
                str(item.get("supplier_store") or "").strip(),
            )
            by_key.setdefault(key, []).append(item)
    for i, op in enumerate(ops or []):
        key = (
            str(op["key"]["supplierCode"]).strip(),
            str(op["key"]["store"]).strip(),
        )
        label = f"{op['operation']}:{key[0]}.{key[1]}"
        found = by_key.get(key, [])
        if op["operation"] == "remove":
            # pós-condição da remoção: ausência oficial comprovada.
            if not found:
                detail.append({"key": label, "result": "matched"})
            else:
                result = "mismatched"
                detail.append(
                    {"key": label, "result": "still_present_official"}
                )
            continue
        if not found:
            result = "mismatched"
            detail.append({"key": label, "result": "missing_in_official"})
            continue
        if len(found) > 1:
            result = "mismatched"
            detail.append({"key": label, "result": "ambiguous_official"})
            continue
        link = found[0]
        bad = []
        for field, official_key in _FIELD_MAP.items():
            if field not in op["fields"]:
                continue
            if official_key not in link:
                result = "mismatched"
                bad.append(f"{field}:unverifiable")
                continue
            exp = (op["fields"][field] or "").strip()
            obs = str(link.get(official_key) or "").strip()
            if exp != obs:
                bad.append(f"{field}:mismatched")
        if bad:
            result = "mismatched"
            detail.append({"key": label, "result": ",".join(bad)})
        else:
            detail.append({"key": label, "result": "matched"})
    return {"result": result, "detail": detail}
