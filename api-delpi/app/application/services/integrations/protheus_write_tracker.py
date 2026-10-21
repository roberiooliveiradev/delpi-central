"""Bridge between Protheus supplier write use cases and execution tracking.

Guarantees:
- CREATED + SENDING committed before any upstream byte (fail closed).
- Deterministic upstream failures -> REJECTED; uncertain -> UNKNOWN.
- Tracking failures AFTER a possible send never trigger a write retry and
  never masquerade as success — they surface as tracking_warning.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping
from urllib.parse import urlparse
from uuid import UUID

from app.application.services.integration_tracking.payload_sanitizer import (
    build_outbound_payload,
    build_request_payload,
    build_response_payload,
    canonical_hash,
)
from app.application.services.integration_tracking.tracking_service import (
    IntegrationTrackingService,
)
from app.domain.integrations.integration_operation import (
    IntegrationTrackingError,
)
from app.domain.integrations.protheus_rest import (
    ProtheusRestConfig,
    ProtheusRestError,
)

logger = logging.getLogger(__name__)

# Errors where the write may have reached the upstream server — outcome
# indeterminate, operation must become UNKNOWN and never be auto-retried.
INDETERMINATE_ERROR_CODES = frozenset(
    {
        "PROTHEUS_TIMEOUT",
        "PROTHEUS_UNAVAILABLE",
        "PROTHEUS_UPSTREAM_ERROR",
    }
)

INTEGRATION_KEY = "protheus"
RESOURCE_SUPPLIER = "supplier"


def environment_key_from_config(config: ProtheusRestConfig, params_ambiente: str) -> str:
    """Logical environment identity — no credentials, just ambiente + host."""
    parsed = urlparse(config.suppliers_base_url)
    host = parsed.netloc or "unknown"
    ambiente = str(params_ambiente or "unknown").strip() or "unknown"
    return f"ambiente:{ambiente}@{host}"


class ProtheusWriteTracker:
    """Orchestrates tracking around one Protheus write call."""

    def __init__(self, tracker: IntegrationTrackingService | None) -> None:
        self._tracker = tracker

    def _require_tracker(self) -> IntegrationTrackingService:
        if self._tracker is None:
            raise ProtheusRestError(
                "Rastreio de execução Protheus indisponível nesta instância.",
                code="PROTHEUS_TRACKING_UNAVAILABLE",
                status_code=503,
                recoverable=False,
            )
        return self._tracker

    def begin(
        self,
        *,
        action: str,
        method: str,
        resource_key: str | None,
        environment_key: str,
        caller_app: str | None,
        actor_user_id: UUID,
        codusr: str,
        request_fields: Mapping[str, Any],
        outbound_body: dict[str, Any],
        correlation_id: str | None,
        request_id: str | None,
    ) -> str:
        """Persist CREATED then SENDING. Any failure aborts before send."""
        tracker = self._require_tracker()
        request_payload = build_request_payload(dict(request_fields))
        outbound_payload = build_outbound_payload(
            method=method,
            resource=RESOURCE_SUPPLIER,
            resource_key=resource_key,
            body=outbound_body,
        )
        try:
            operation_id = tracker.begin_operation(
                integration=INTEGRATION_KEY,
                resource=RESOURCE_SUPPLIER,
                action=action,
                resource_key=resource_key,
                environment_key=environment_key,
                company_scope=None,
                caller_app=caller_app,
                actor_subject=str(actor_user_id),
                protheus_user_id=codusr,
                authorization_context=None,
                request_payload=request_payload,
                outbound_payload=outbound_payload,
                request_hash=canonical_hash(
                    {
                        "action": action,
                        "resource": RESOURCE_SUPPLIER,
                        "resource_key": resource_key,
                        "fields": dict(request_fields),
                    }
                ),
                outbound_hash=canonical_hash(outbound_body),
                correlation_id=correlation_id,
                request_id=request_id,
            )
            tracker.mark_sending(operation_id)
        except IntegrationTrackingError as exc:
            raise ProtheusRestError(
                "Falha ao registrar a operação de escrita antes do envio. "
                "Nenhuma requisição foi enviada ao Protheus.",
                code="PROTHEUS_TRACKING_UNAVAILABLE",
                status_code=503,
                recoverable=False,
            ) from exc
        return operation_id

    def record_send_failure(
        self, operation_id: str | None, exc: BaseException
    ) -> None:
        """Best-effort outcome classification. Never re-raises."""
        if operation_id is None or self._tracker is None:
            return
        try:
            if isinstance(exc, ProtheusRestError) and (
                exc.code in INDETERMINATE_ERROR_CODES
                or (exc.status_code or 0) >= 500
            ):
                self._tracker.mark_outcome_unknown(
                    operation_id,
                    http_status=None,
                    code=exc.code or "PROTHEUS_UPSTREAM_ERROR",
                    message=str(exc),
                )
            elif isinstance(exc, ProtheusRestError):
                self._tracker.record_rejected(
                    operation_id,
                    http_status=exc.status_code,
                    code=exc.code or "PROTHEUS_UPSTREAM_REJECTION",
                    message=str(exc),
                )
            else:
                # Non-mapped failure after a possible send: indeterminate.
                self._tracker.mark_outcome_unknown(
                    operation_id,
                    http_status=None,
                    code="PROTHEUS_SEND_UNKNOWN",
                    message=str(exc),
                )
        except Exception:
            logger.exception(
                "integration_tracking outcome_record_failed "
                "operation_id=%s — operation remains SENDING (indeterminate)",
                operation_id,
            )

    def record_ack(
        self,
        operation_id: str | None,
        *,
        upstream: Mapping[str, Any],
        resource_key: str | None,
    ) -> bool:
        """Record ACKNOWLEDGED. Returns False when recording failed."""
        if operation_id is None or self._tracker is None:
            return False
        try:
            self._tracker.record_acknowledged(
                operation_id,
                http_status=upstream.get("http_status"),
                response_payload=build_response_payload(
                    http_status=upstream.get("http_status"),
                    body=upstream.get("upstream")
                    if isinstance(upstream.get("upstream"), dict)
                    else upstream,
                ),
                resource_key=resource_key,
            )
            return True
        except Exception:
            logger.exception(
                "integration_tracking ack_record_failed operation_id=%s",
                operation_id,
            )
            return False

    def record_confirmation_failure(
        self, operation_id: str | None, exc: BaseException
    ) -> None:
        if operation_id is None or self._tracker is None:
            return
        try:
            code = getattr(exc, "code", None) or "CONFIRMATION_READ_FAILED"
            self._tracker.record_confirmation_failure(
                operation_id, code=str(code), message=str(exc)
            )
        except Exception:
            logger.exception(
                "integration_tracking confirmation_event_failed "
                "operation_id=%s",
                operation_id,
            )

    def confirm(
        self,
        operation_id: str | None,
        *,
        checked_fields: list[str],
        result: str,
    ) -> bool:
        if operation_id is None or self._tracker is None:
            return False
        try:
            self._tracker.confirm(
                operation_id, checked_fields=checked_fields, result=result
            )
            return True
        except Exception:
            logger.exception(
                "integration_tracking confirm_failed operation_id=%s",
                operation_id,
            )
            return False

    def require_reconciliation(
        self, operation_id: str | None, *, code: str, message: str
    ) -> bool:
        if operation_id is None or self._tracker is None:
            return False
        try:
            self._tracker.require_reconciliation(
                operation_id, code=code, message=message
            )
            return True
        except Exception:
            logger.exception(
                "integration_tracking reconciliation_flag_failed "
                "operation_id=%s",
                operation_id,
            )
            return False


def extract_supplier_fields(payload: Any) -> dict[str, Any]:
    """Best-effort extraction of the supplier object from a GET response."""
    if not isinstance(payload, dict):
        return {}
    for key in ("fornecedor", "supplier", "data"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            return nested
    return payload


def compare_sent_fields(
    sent: Mapping[str, Any], read_back: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare normalized sent values vs read-back values.

    Returns {"verifiable": [...], "matched": [...], "mismatched": [...],
    "missing": [...]}. A field absent from the read-back cannot be verified
    (it is not evidence of mismatch).
    """
    matched: list[str] = []
    mismatched: list[str] = []
    missing: list[str] = []
    for field, expected in sent.items():
        if field not in read_back:
            missing.append(field)
            continue
        actual = read_back.get(field)
        if str(actual if actual is not None else "").strip() == str(
            expected if expected is not None else ""
        ).strip():
            matched.append(field)
        else:
            mismatched.append(field)
    return {
        "verifiable": matched + mismatched,
        "matched": matched,
        "mismatched": mismatched,
        "missing": missing,
    }
