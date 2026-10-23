"""Create Protheus supplier via REST — identity from Core; write behind feature gate.

Every attempt is registered in the integration execution tracker BEFORE the
upstream call (fail closed). POST upstream does not return A2_COD, so the
operation stays ACKNOWLEDGED until external reconciliation supplies the key.
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
    assert_protheus_write_target,
    resolve_protheus_rest_config,
)
from app.application.services.integrations.protheus_supplier_create_payload import (
    build_upstream_create_body,
    normalize_supplier_fields,
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
from app.domain.integrations.supplier_change_provenance import (
    build_supplier_field_provenance,
)
from app.infrastructure.gateways.core_protheus_identity_gateway import (
    CoreProtheusIdentityGateway,
)
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway
from app.infrastructure.persistence.intranet.protheus_integration_params_repository import (
    ProtheusIntegrationParamsRepository,
)
from app.utils.logger import log_info


class CreateProtheusRestSupplierUseCase:
    def __init__(
        self,
        *,
        params_repository: ProtheusIntegrationParamsRepository,
        token_service: ProtheusTokenService,
        gateway: ProtheusRestGateway,
        identity_gateway: CoreProtheusIdentityGateway,
        tracker: IntegrationTrackingService | None = None,
        field_normalizer: Any = None,
    ) -> None:
        self._params_repository = params_repository
        self._token_service = token_service
        self._gateway = gateway
        self._identity_gateway = identity_gateway
        self._write_tracker = ProtheusWriteTracker(tracker)
        # Canonical contract by default; authorized homologation assays may
        # inject the experimental (widened) normalizer — public routes never do.
        self._field_normalizer = field_normalizer or normalize_supplier_fields

    def execute(
        self,
        *,
        actor_user_id: UUID,
        fornecedor: Mapping[str, Any],
        caller_app: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        change_context: Any = None,
    ) -> dict[str, Any]:
        normalized = self._field_normalizer(fornecedor)

        if not settings.PROTHEUS_SUPPLIER_CREATE_ENABLED:
            log_info(
                "protheus_supplier_create_blocked_by_feature_gate "
                f"actor_user_id={actor_user_id}"
            )
            raise ProtheusRestError(
                "Criação de fornecedor Protheus desabilitada neste ambiente "
                "(PROTHEUS_SUPPLIER_CREATE_ENABLED=false). "
                "Nenhuma escrita foi enviada ao ERP.",
                code="PROTHEUS_SUPPLIER_CREATE_DISABLED",
                status_code=503,
                recoverable=False,
            )

        codusr = resolve_actor_codusr(self._identity_gateway, actor_user_id)
        body = build_upstream_create_body(codusr=codusr, fornecedor=normalized)
        raw = self._params_repository.load_raw_params()
        config = resolve_protheus_rest_config(raw)
        assert_protheus_write_target(
            config, settings.PROTHEUS_REST_EXPECTED_BASE_URL
        )
        environment_key = environment_key_from_config(
            config, settings.INTRANET_PARAMS_AMBIENTE or ""
        )
        provenance = build_supplier_field_provenance(
            change_context,
            sent_fields=normalized,
            # POST may not know the final A2_COD until upstream assigns it;
            # the operation resource_key is reconciled at ACK time.
            supplier_code=None,
            supplier_store=normalized.get("supplier_store"),
            environment_key=environment_key,
            caller_app=caller_app,
            actor_subject=str(actor_user_id),
        )
        token = self._token_service.get_valid_token(config)

        # Tracking persists CREATED + SENDING before any upstream byte.
        operation_id = self._write_tracker.begin(
            action="create",
            method="POST",
            resource_key=None,
            environment_key=environment_key,
            caller_app=caller_app,
            actor_user_id=actor_user_id,
            codusr=codusr,
            request_fields=normalized,
            outbound_body=body,
            correlation_id=correlation_id,
            request_id=request_id,
            field_provenance=provenance,
        )

        try:
            upstream = self._gateway.create_supplier(
                config, body=body, access_token=token
            )
        except ProtheusRestError as exc:
            # Never auto-retry the write POST (non-idempotent). Invalidate stale
            # token cache so the next authorized attempt can refresh OAuth.
            if exc.code == "PROTHEUS_TOKEN_INVALID":
                self._token_service.invalidate()
            self._write_tracker.record_send_failure(operation_id, exc)
            raise
        except Exception as exc:  # noqa: BLE001 — send may have started
            self._write_tracker.record_send_failure(operation_id, exc)
            raise

        # Upstream may return the generated key — capture it for reconciliation.
        resource_key = None
        supplier_code = upstream.get("supplier_code")
        supplier_store = upstream.get("supplier_store")
        if supplier_code and supplier_store:
            resource_key = f"{supplier_code}{supplier_store}"

        ack_recorded = self._write_tracker.record_ack(
            operation_id, upstream=upstream, resource_key=resource_key
        )

        log_info(
            "protheus_supplier_create_submitted "
            f"actor_user_id={actor_user_id} operation_id={operation_id} "
            f"creation_confirmed={upstream.get('creation_confirmed')}"
        )
        result = {
            "codusr": codusr,
            "supplier_store": normalized.get("supplier_store"),
            "operation_id": operation_id,
            **upstream,
        }
        if not ack_recorded:
            result["tracking_warning"] = "acknowledgement_record_failed"
            return result

        if resource_key:
            # Upstream returned the generated key — verify by read-after-write.
            result.update(
                self._confirm_creation(
                    config=config,
                    resource_key=resource_key,
                    fields=normalized,
                    access_token=token,
                    operation_id=operation_id,
                )
            )
        # Sem chave retornada: operação permanece ACKNOWLEDGED e a
        # reconciliação depende de consulta externa (documentado no contrato).
        return result

    def _confirm_creation(
        self,
        *,
        config,
        resource_key: str,
        fields: Mapping[str, Any],
        access_token: str,
        operation_id: str,
    ) -> dict[str, Any]:
        outcome: dict[str, Any] = {
            "creation_confirmed": False,
            "persistence_proven": False,
        }
        try:
            read_back = self._gateway.get_supplier(
                config, supplier_id=resource_key, access_token=access_token
            )
        except ProtheusRestError as exc:
            if exc.code == "PROTHEUS_TOKEN_INVALID":
                self._token_service.invalidate()
                try:
                    token = self._token_service.get_valid_token(config)
                    read_back = self._gateway.get_supplier(
                        config,
                        supplier_id=resource_key,
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

        comparison = compare_sent_fields(
            fields, extract_supplier_fields(read_back)
        )
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
            outcome["creation_confirmed"] = True
            outcome["persistence_proven"] = True
        else:
            outcome["tracking_warning"] = "confirmation_record_failed"
        return outcome
