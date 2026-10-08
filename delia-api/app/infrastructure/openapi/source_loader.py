"""Governed OpenAPI source loader — composition wiring.

ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01 (ledger §6.130):
builds one OpenApiCapabilitySource from settings. The declarations file
is the governed semantic contract (versioned JSON, reviewed like code):
it maps operationIds to capability_id/semantic_name/operation_character.
Without it the source is absent — never heuristic exposure.

Wire mechanics (document fetch, invocation) stay in this package.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.capability_provision.openapi_provider import (
    OpenApiCapabilitySource,
)
from app.domain.capability_catalog.model import OperationCharacter
from app.domain.specialist_interop.model import SpecialistOutcome
from app.infrastructure.openapi.capability_catalog_adapter import (
    CapabilityDeclaration,
    project_openapi_document,
)
from app.infrastructure.openapi.http_invoker import (
    _OPENAPI_FETCH_TIMEOUT_SECONDS,
    HttpOpenApiInvoker,
    fetch_openapi_document,
)

_logger = logging.getLogger(__name__)

MAX_DECLARATIONS = 64
_DECLARATION_KEYS = frozenset(
    {
        "operation_id",
        "capability_id",
        "semantic_name",
        "operation_character",
        "idempotency_semantics",
        "reversible",
        "required_postcondition",
    }
)


def load_declarations(
    path: str,
) -> tuple[tuple[CapabilityDeclaration, ...], str, str, str]:
    """Parse the governed declarations file — fail closed.

    Returns (declarations, owner, contract_id, display_name)."""
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, Mapping):
        raise CapabilityProviderError(
            "openapi_declarations_invalid", "declarations not an object"
        )
    owner = str(data.get("owner") or "").strip()
    contract_id = str(data.get("contract_id") or "").strip()
    display_name = str(data.get("display_name") or "").strip()
    items = data.get("declarations")
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise CapabilityProviderError(
            "openapi_declarations_invalid", "declarations must be a list"
        )
    items = list(items)[:MAX_DECLARATIONS]
    declarations: list[CapabilityDeclaration] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise CapabilityProviderError(
                "openapi_declarations_invalid",
                f"declaration[{index}] must be an object",
            )
        extra = set(item) - _DECLARATION_KEYS
        if extra:
            raise CapabilityProviderError(
                "openapi_declarations_invalid",
                f"declaration[{index}] unsupported fields: {sorted(extra)}",
            )
        try:
            character = OperationCharacter(
                str(item.get("operation_character") or "")
            )
        except ValueError as exc:
            raise CapabilityProviderError(
                "openapi_declarations_invalid",
                f"declaration[{index}] unknown operation_character",
            ) from exc
        declarations.append(
            CapabilityDeclaration(
                operation_id=str(item.get("operation_id") or ""),
                capability_id=str(item.get("capability_id") or ""),
                semantic_name=str(item.get("semantic_name") or ""),
                operation_character=character,
                idempotency_semantics=(
                    str(item["idempotency_semantics"])
                    if item.get("idempotency_semantics") is not None
                    else None
                ),
                reversible=(
                    bool(item["reversible"])
                    if item.get("reversible") is not None
                    else None
                ),
                required_postcondition=(
                    str(item["required_postcondition"])
                    if item.get("required_postcondition") is not None
                    else None
                ),
            )
        )
    return (
        tuple(declarations),
        owner,
        contract_id,
        display_name,
    )


def build_openapi_source(
    *,
    source_id: str,
    base_url: str,
    declarations_path: str,
    http_get: Callable,
    subject_bearer_getter: Callable[[], str | None],
    timeout_seconds: float,
) -> OpenApiCapabilitySource | None:
    """Build one governed OpenAPI source — None when config is absent."""
    if not (base_url and declarations_path):
        return None
    try:
        declarations, owner, contract_id, display_name = load_declarations(
            declarations_path
        )
    except Exception as exc:
        _logger.warning(
            "openapi_source_unavailable source=%s reason=%s",
            source_id,
            "declarations_invalid",
        )
        return None
    if not (owner and contract_id):
        _logger.warning(
            "openapi_source_unavailable source=%s reason=%s",
            source_id,
            "declarations_missing_identity",
        )
        return None

    def projector(timeout_seconds: float | None = None):
        # Caller-bound reduction ceiling (LOOP-03R2A-R1): the fetch
        # stage max is shortened, never lengthened.
        effective = (
            _OPENAPI_FETCH_TIMEOUT_SECONDS
            if timeout_seconds is None
            else min(
                float(timeout_seconds), _OPENAPI_FETCH_TIMEOUT_SECONDS
            )
        )
        document = fetch_openapi_document(
            base_url, http_get=http_get, timeout_seconds=effective
        )
        return project_openapi_document(
            document,
            source_owner=owner,
            source_contract_id=contract_id,
            declarations=declarations,
        ).capabilities

    invoker = HttpOpenApiInvoker(
        base_url,
        source_id=source_id,
        subject_bearer_getter=subject_bearer_getter,
        http_get=http_get,
        timeout_seconds=timeout_seconds,
    )
    return OpenApiCapabilitySource(
        source_id=source_id,
        owner_ref=owner,
        display_name=display_name or source_id,
        projector=projector,
        invoker=invoker,
    )
