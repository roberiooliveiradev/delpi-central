"""Supplier write provenance — transversal contract v1 (domain layer).

Records, per write operation and per field sent, where the information came
from and how the change was initiated. The ``integration_tracking`` schema
remains the authority for operational state; provenance rows are immutable
facts of intent bound to ``operation_id``.

Identity is server-side: ``actor_subject`` and ``initiating_client_id`` are
derived from validated credentials and are never accepted from the request
body.

v1 fail-closed policy:
- Client-claimable source types: ``MANUAL_USER_INPUT``, ``INTERNAL_SYSTEM``,
  ``IMPORT``.
- ``GOVERNMENT_API``, ``THIRD_PARTY_API`` and ``AUTOMATION_RULE`` are
  rejected until a server-verifiable evidence contract exists — an
  unverifiable claim must never be recorded as a proven official source.
- ``UNKNOWN_LEGACY`` is server-assigned to writes without ``change_context``;
  it is not client-claimable.
- Claimable change modes: ``MANUAL_DIRECT``, ``SYSTEM_SYNC``, ``IMPORT_JOB``.
- ``EXTERNAL_SUGGESTION_*`` and ``AUTOMATED_BY_APPROVED_POLICY`` are rejected
  in v1 — they require verifiable external evidence or an approved policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from app.domain.integrations.protheus_rest import ProtheusRestError

PROVENANCE_SCHEMA_VERSION = "1"

_MAX_KEY = 60
_MAX_ID = 120
_MAX_REF = 300


class ProvenanceSourceType(StrEnum):
    MANUAL_USER_INPUT = "MANUAL_USER_INPUT"
    GOVERNMENT_API = "GOVERNMENT_API"
    THIRD_PARTY_API = "THIRD_PARTY_API"
    INTERNAL_SYSTEM = "INTERNAL_SYSTEM"
    IMPORT = "IMPORT"
    AUTOMATION_RULE = "AUTOMATION_RULE"
    UNKNOWN_LEGACY = "UNKNOWN_LEGACY"


class SupplierChangeMode(StrEnum):
    MANUAL_DIRECT = "MANUAL_DIRECT"
    EXTERNAL_SUGGESTION_USER_APPROVED = "EXTERNAL_SUGGESTION_USER_APPROVED"
    BULK_SUGGESTION_USER_APPROVED = "BULK_SUGGESTION_USER_APPROVED"
    AUTOMATED_BY_APPROVED_POLICY = "AUTOMATED_BY_APPROVED_POLICY"
    SYSTEM_SYNC = "SYSTEM_SYNC"
    IMPORT_JOB = "IMPORT_JOB"


# v1: only self-attestable sources are claimable. External-official claims
# require a verifiable evidence contract that does not exist yet.
_CLAIMABLE_SOURCE_TYPES = frozenset(
    {
        ProvenanceSourceType.MANUAL_USER_INPUT,
        ProvenanceSourceType.INTERNAL_SYSTEM,
        ProvenanceSourceType.IMPORT,
    }
)

_SOURCE_ID_REQUIRED = frozenset(
    {
        ProvenanceSourceType.INTERNAL_SYSTEM,
        ProvenanceSourceType.IMPORT,
    }
)

_CLAIMABLE_CHANGE_MODES = frozenset(
    {
        SupplierChangeMode.MANUAL_DIRECT,
        SupplierChangeMode.SYSTEM_SYNC,
        SupplierChangeMode.IMPORT_JOB,
    }
)

# Identity and automation metadata are derived server-side; a client must
# never attest them for itself.
_FORBIDDEN_CONTEXT_KEYS = frozenset(
    {
        "initiating_client_id",
        "actor_subject",
        "approver_subject",
        "caller_app",
        "user_id",
        "client_id",
        "policy_id",
    }
)


def _raise(message: str, code: str) -> None:
    raise ProtheusRestError(
        message,
        code=code,
        status_code=422,
        recoverable=False,
    )


def _bounded_text(value: Any, *, limit: int, field: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or len(text) > limit:
        _raise(
            f"Metadado de proveniência inválido: {field}.",
            "PROVENANCE_METADATA_INVALID",
        )
    return text


def _retrieved_at(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        _raise(
            "source_retrieved_at deve ser um timestamp ISO-8601.",
            "PROVENANCE_METADATA_INVALID",
        )
    return text


@dataclass(frozen=True, slots=True)
class FieldProvenanceInput:
    """Validated provenance declaration for one sent field."""

    field_key: str
    source_type: ProvenanceSourceType
    source_id: str | None = None
    source_reference: str | None = None
    source_retrieved_at: str | None = None
    decision_id: str | None = None


@dataclass(frozen=True, slots=True)
class ChangeContext:
    """Validated operation-level provenance context (contract v1)."""

    change_mode: SupplierChangeMode
    reason_code: str | None
    review_id: str | None
    field_provenance: tuple[FieldProvenanceInput, ...]


def parse_change_context(
    raw: Any, *, sent_fields: set[str]
) -> ChangeContext:
    """Validate the optional ``change_context`` object of a write request.

    ``sent_fields`` is the post-normalization allowlisted field set — the
    exact keys that will reach the upstream payload. Every declared
    ``field_key`` must belong to it.
    """
    if not isinstance(raw, Mapping):
        _raise(
            "change_context deve ser um objeto JSON.",
            "PROVENANCE_CONTEXT_INVALID",
        )

    forbidden = _FORBIDDEN_CONTEXT_KEYS & {
        str(k).strip().lower() for k in raw.keys()
    }
    if forbidden:
        _raise(
            "Identidade do ator/cliente ou política de automação não podem "
            "ser declaradas pelo consumidor: " + ", ".join(sorted(forbidden)),
            "PROVENANCE_IDENTITY_CLIENT_FORBIDDEN",
        )

    if str(raw.get("schema_version", "")).strip() != PROVENANCE_SCHEMA_VERSION:
        _raise(
            "schema_version de proveniência não suportado.",
            "PROVENANCE_SCHEMA_VERSION_UNSUPPORTED",
        )

    raw_mode = raw.get("change_mode")
    try:
        change_mode = SupplierChangeMode(str(raw_mode))
    except ValueError:
        _raise(
            "change_mode de proveniência inválido.",
            "PROVENANCE_CHANGE_MODE_INVALID",
        )
    if change_mode not in _CLAIMABLE_CHANGE_MODES:
        _raise(
            "change_mode exige evidência ou política aprovada ainda não "
            f"contratada: {change_mode.value}.",
            "PROVENANCE_CHANGE_MODE_NOT_AUTHORIZED",
        )

    entries = raw.get("field_provenance")
    if not isinstance(entries, list) or not entries:
        _raise(
            "field_provenance é obrigatório quando change_context é enviado.",
            "PROVENANCE_FIELD_METADATA_REQUIRED",
        )

    seen: set[str] = set()
    parsed: list[FieldProvenanceInput] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            _raise(
                "Cada item de field_provenance deve ser um objeto.",
                "PROVENANCE_CONTEXT_INVALID",
            )
        field_key = str(entry.get("field_key") or "").strip()
        if not field_key or len(field_key) > _MAX_KEY:
            _raise(
                "field_key de proveniência inválido.",
                "PROVENANCE_METADATA_INVALID",
            )
        if field_key not in sent_fields:
            _raise(
                "Proveniência declarada para campo ausente do payload "
                f"efetivo: {field_key}.",
                "PROVENANCE_FIELD_NOT_IN_PAYLOAD",
            )
        if field_key in seen:
            _raise(
                f"Proveniência duplicada para o campo {field_key}.",
                "PROVENANCE_FIELD_DUPLICATED",
            )
        seen.add(field_key)

        try:
            source_type = ProvenanceSourceType(str(entry.get("source_type")))
        except ValueError:
            _raise(
                "source_type de proveniência inválido.",
                "PROVENANCE_SOURCE_INVALID",
            )
        if source_type not in _CLAIMABLE_SOURCE_TYPES:
            _raise(
                "source_type exige evidência verificável no servidor ainda "
                f"não contratada: {source_type.value}.",
                "PROVENANCE_SOURCE_NOT_VERIFIABLE",
            )

        source_id = _bounded_text(
            entry.get("source_id"), limit=_MAX_ID, field="source_id"
        )
        if source_type in _SOURCE_ID_REQUIRED and source_id is None:
            _raise(
                f"source_id é obrigatório para {source_type.value}.",
                "PROVENANCE_SOURCE_ID_REQUIRED",
            )

        parsed.append(
            FieldProvenanceInput(
                field_key=field_key,
                source_type=source_type,
                source_id=source_id,
                source_reference=_bounded_text(
                    entry.get("source_reference"),
                    limit=_MAX_REF,
                    field="source_reference",
                ),
                source_retrieved_at=_retrieved_at(
                    entry.get("source_retrieved_at")
                ),
                decision_id=_bounded_text(
                    entry.get("decision_id"), limit=_MAX_ID, field="decision_id"
                ),
            )
        )

    return ChangeContext(
        change_mode=change_mode,
        reason_code=_bounded_text(
            raw.get("reason_code"), limit=_MAX_ID, field="reason_code"
        ),
        review_id=_bounded_text(
            raw.get("review_id"), limit=_MAX_ID, field="review_id"
        ),
        field_provenance=tuple(parsed),
    )


def build_supplier_field_provenance(
    change_context: Any,
    *,
    sent_fields: Mapping[str, Any],
    supplier_code: str | None,
    supplier_store: str | None,
    environment_key: str | None,
    caller_app: str | None,
    actor_subject: str | None,
) -> list[dict[str, Any]]:
    """Return persistence-ready provenance records for a write operation.

    ``change_context=None`` classifies every sent field as
    ``UNKNOWN_LEGACY`` — proven, declared unknown, never invented.
    """
    context = (
        parse_change_context(change_context, sent_fields=set(sent_fields))
        if change_context is not None
        else None
    )
    base: dict[str, Any] = {
        "supplier_code": supplier_code,
        "supplier_store": supplier_store,
        "environment_key": environment_key,
        "initiating_client_id": caller_app,
        "actor_subject": actor_subject,
        "change_mode": context.change_mode.value if context else None,
        "reason_code": context.reason_code if context else None,
        "review_id": context.review_id if context else None,
    }
    if context is None:
        return [
            {
                **base,
                "field_key": field_key,
                "source_type": ProvenanceSourceType.UNKNOWN_LEGACY.value,
                "source_id": None,
                "source_reference": None,
                "source_retrieved_at": None,
                "decision_id": None,
            }
            for field_key in sorted(sent_fields)
        ]
    return [
        {
            **base,
            "field_key": item.field_key,
            "source_type": item.source_type.value,
            "source_id": item.source_id,
            "source_reference": item.source_reference,
            "source_retrieved_at": item.source_retrieved_at,
            "decision_id": item.decision_id,
        }
        for item in context.field_provenance
    ]
