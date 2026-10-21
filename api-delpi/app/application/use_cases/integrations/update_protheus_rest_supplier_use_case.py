"""Update an existing Protheus supplier via REST — gated, no automatic retry.

Every attempt is registered in the integration execution tracker BEFORE the
upstream call (fail closed). ACK is never presented as persistence proof;
when read-after-write evidence matches, the operation is CONFIRMED.
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from app.application.services.integration_tracking.tracking_service import (
    IntegrationTrackingService,
)
from app.application.services.integrations.protheus_actor_codusr import (
    resolve_actor_codusr,
)
from app.application.services.integrations.protheus_path_resolver import (
    resolve_protheus_rest_config,
)
from app.application.services.integrations.protheus_supplier_update_payload import (
    build_upstream_update_body,
    normalize_supplier_update_fields,
    validate_supplier_id,
)
from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
)
from app.application.services.integrations.protheus_write_tracker import (
    ProtheusWriteTracker,
    compare_sent_fields,
    environment_key_from_config,
    extract_supplier_fields,
)
from app.config import settings
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.infrastructure.gateways.core_protheus_identity_gateway import (
    CoreProtheusIdentityGateway,
)
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway
from app.infrastructure.persistence.intranet.protheus_integration_params_repository import (
    ProtheusIntegrationParamsRepository,
)
from app.utils.logger import log_info


class UpdateProtheusRestSupplierUseCase:
    def __init__(
        self,
        *,
        params_repository: ProtheusIntegrationParamsRepository,
        token_service: ProtheusTokenService,
        gateway: ProtheusRestGateway,
        identity_gateway: CoreProtheusIdentityGateway,
        tracker: IntegrationTrackingService | None = None,
    ) -> None:
        self._params_repository = params_repository
        self._token_service = token_service
        self._gateway = gateway
        self._identity_gateway = identity_gateway
        self._write_tracker = ProtheusWriteTracker(tracker)

    def execute(
        self,
        *,
        actor_user_id: UUID,
        supplier_id: str,
        fornecedor: Mapping[str, Any],
        caller_app: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_id = validate_supplier_id(supplier_id)
        fields = normalize_supplier_update_fields(fornecedor)

        if not settings.PROTHEUS_SUPPLIER_UPDATE_ENABLED:
            log_info(
                "protheus_supplier_update_blocked_by_feature_gate "
                f"actor_user_id={actor_user_id} supplier_id={normalized_id}"
            )
            raise ProtheusRestError(
                "Alteração de fornecedor Protheus desabilitada neste ambiente "
                "(PROTHEUS_SUPPLIER_UPDATE_ENABLED=false). "
                "Nenhuma escrita foi enviada ao ERP.",
                code="PROTHEUS_SUPPLIER_UPDATE_DISABLED",
                status_code=503,
                recoverable=False,
            )

        codusr = resolve_actor_codusr(self._identity_gateway, actor_user_id)
        body = build_upstream_update_body(codusr=codusr, fields=fields)
        raw = self._params_repository.load_raw_params()
        config = resolve_protheus_rest_config(raw)
        token = self._token_service.get_valid_token(config)

        # Tracking persists CREATED + SENDING before any upstream byte.
        operation_id = self._write_tracker.begin(
            action="update",
            method="PUT",
            resource_key=normalized_id,
            environment_key=environment_key_from_config(
                config, settings.INTRANET_PARAMS_AMBIENTE or ""
            ),
            caller_app=caller_app,
            actor_user_id=actor_user_id,
            codusr=codusr,
            request_fields=fields,
            outbound_body=body,
            correlation_id=correlation_id,
            request_id=request_id,
        )

        try:
            upstream = self._gateway.update_supplier(
                config,
                supplier_id=normalized_id,
                body=body,
                access_token=token,
            )
        except ProtheusRestError as exc:
            if exc.code == "PROTHEUS_TOKEN_INVALID":
                self._token_service.invalidate()
            self._write_tracker.record_send_failure(operation_id, exc)
            raise
        except Exception as exc:  # noqa: BLE001 — send may have started
            self._write_tracker.record_send_failure(operation_id, exc)
            raise

        ack_recorded = self._write_tracker.record_ack(
            operation_id, upstream=upstream, resource_key=normalized_id
        )

        confirmation = self._confirm_persistence(
            config=config,
            supplier_id=normalized_id,
            fields=fields,
            access_token=token,
            operation_id=operation_id,
            ack_recorded=ack_recorded,
        )

        log_info(
            "protheus_supplier_update_submitted "
            f"actor_user_id={actor_user_id} supplier_id={normalized_id} "
            f"operation_id={operation_id} "
            f"update_confirmed={confirmation.get('update_confirmed')}"
        )
        return {
            "supplier_id": normalized_id,
            "codusr": codusr,
            "fields_sent": sorted(fields.keys()),
            "operation_id": operation_id,
            **upstream,
            **confirmation,
        }

    def _confirm_persistence(
        self,
        *,
        config,
        supplier_id: str,
        fields: Mapping[str, Any],
        access_token: str,
        operation_id: str,
        ack_recorded: bool,
    ) -> dict[str, Any]:
        """Read-after-write: GET the supplier and compare the sent fields.

        - All sent fields verifiable and matched -> CONFIRMED.
        - Any verifiable mismatch -> RECONCILIATION_REQUIRED.
        - Read failure / unverifiable -> stays ACKNOWLEDGED (+ event).
        """
        outcome: dict[str, Any] = {
            "update_confirmed": False,
            "persistence_proven": False,
        }
        if not ack_recorded:
            outcome["tracking_warning"] = "acknowledgement_record_failed"
            return outcome

        try:
            read_back = self._gateway.get_supplier(
                config, supplier_id=supplier_id, access_token=access_token
            )
        except ProtheusRestError as exc:
            if exc.code == "PROTHEUS_TOKEN_INVALID":
                self._token_service.invalidate()
                try:
                    token = self._token_service.get_valid_token(config)
                    read_back = self._gateway.get_supplier(
                        config,
                        supplier_id=supplier_id,
                        access_token=token,
                    )
                except ProtheusRestError as retry_exc:
                    self._write_tracker.record_confirmation_failure(
                        operation_id, retry_exc
                    )
                    outcome["tracking_warning"] = "confirmation_read_failed"
                    return outcome
            else:
                self._write_tracker.record_confirmation_failure(
                    operation_id, exc
                )
                outcome["tracking_warning"] = "confirmation_read_failed"
                return outcome

        comparison = compare_sent_fields(fields, extract_supplier_fields(read_back))
        if comparison["mismatched"]:
            self._write_tracker.require_reconciliation(
                operation_id,
                code="CONFIRMATION_MISMATCH",
                message=(
                    "Read-after-write divergiu nos campos: "
                    + ", ".join(comparison["mismatched"])
                ),
            )
            outcome["tracking_warning"] = "confirmation_mismatch"
            outcome["mismatched_fields"] = comparison["mismatched"]
            return outcome
        if not comparison["verifiable"]:
            # Nothing could be compared — inconclusive, stays ACKNOWLEDGED.
            self._write_tracker.record_confirmation_failure(
                operation_id,
                ProtheusRestError(
                    "Leitura pós-escrita não retornou campos verificáveis.",
                    code="CONFIRMATION_NO_EVIDENCE",
                    status_code=502,
                    recoverable=True,
                ),
            )
            outcome["tracking_warning"] = "confirmation_inconclusive"
            return outcome

        confirmed = self._write_tracker.confirm(
            operation_id,
            checked_fields=comparison["matched"],
            result="MATCH",
        )
        if confirmed:
            outcome["update_confirmed"] = True
            outcome["persistence_proven"] = True
        else:
            outcome["tracking_warning"] = "confirmation_record_failed"
        return outcome
