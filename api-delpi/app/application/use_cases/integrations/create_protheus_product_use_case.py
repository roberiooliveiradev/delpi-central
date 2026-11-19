"""Create a new Protheus product via delpiproduto /incluir — gated, no retry.

Same governance as the update path: every attempt is tracked BEFORE the
upstream call, the actor identity resolved from Core/JWT travels upstream
as the `codusr` meta-field (AIF_ZCDUSR audit) and the write target is
pinned by PROTHEUS_REST_EXPECTED_BASE_URL.

Create contract: the caller supplies B1_COD plus the eligible catalog
fields for the new record — the official routine (MATA010 ExecAuto,
operation 3) applies its own defaults for omitted columns, so no snapshot
merge exists here. An existing SB1 record for the code is a deterministic
409 conflict — create never silently becomes an overwrite. After the
upstream ACK we read the record back: matching sent fields promote the
result to CONFIRMED; divergence stays ACKNOWLEDGED for manual review.
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
from app.application.services.integrations.protheus_product_payload import (
    build_upstream_product_update_body,
    normalize_product_create_fields,
    product_create_url,
    repair_legacy_combo_values,
    snapshot_value_matches,
)
from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
)
from app.application.services.integrations.protheus_write_tracker import (
    ProtheusWriteTracker,
    RESOURCE_PRODUCT,
    environment_key_from_config,
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


class CreateProtheusProductUseCase:
    def __init__(
        self,
        *,
        params_repository: ProtheusIntegrationParamsRepository,
        token_service: ProtheusTokenService,
        gateway: ProtheusRestGateway,
        identity_gateway: CoreProtheusIdentityGateway,
        product_repository,
        tracker: IntegrationTrackingService | None = None,
    ) -> None:
        self._params_repository = params_repository
        self._token_service = token_service
        self._gateway = gateway
        self._identity_gateway = identity_gateway
        self._product_repository = product_repository
        self._write_tracker = ProtheusWriteTracker(tracker)

    def execute(
        self,
        *,
        actor_user_id: UUID,
        product: Mapping[str, Any],
        caller_app: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_code, fields = normalize_product_create_fields(product)

        if not settings.PROTHEUS_PRODUCT_CREATE_ENABLED:
            log_info(
                "protheus_product_create_blocked_by_feature_gate "
                f"actor_user_id={actor_user_id} product_code={normalized_code}"
            )
            raise ProtheusRestError(
                "Criação de produto Protheus desabilitada neste ambiente "
                "(PROTHEUS_PRODUCT_CREATE_ENABLED=false). "
                "Nenhuma escrita foi enviada ao ERP.",
                code="PROTHEUS_PRODUCT_CREATE_DISABLED",
                status_code=503,
                recoverable=False,
            )

        codusr = resolve_actor_codusr(self._identity_gateway, actor_user_id)
        raw = self._params_repository.load_raw_params()
        config = resolve_protheus_rest_config(raw)
        assert_protheus_write_target(
            config, settings.PROTHEUS_REST_EXPECTED_BASE_URL
        )
        environment_key = environment_key_from_config(
            config, settings.INTRANET_PARAMS_AMBIENTE or ""
        )

        # Fail-closed conflict: create must never overwrite an existing SB1.
        if self._product_repository.get_product_snapshot(normalized_code) is not None:
            raise ProtheusRestError(
                "Já existe produto cadastrado com este código na base TOTVS "
                "deste ambiente.",
                code="PROTHEUS_PRODUCT_ALREADY_EXISTS",
                status_code=409,
                recoverable=False,
            )

        # Reparo de literal legado fora do combo X3 — mesma regra do
        # update (literal Sim/Não → única chave de rótulo equivalente);
        # valores sem equivalência seguem para a validação oficial.
        repairs: dict[str, dict[str, str]] = {}
        try:
            combo_map = self._product_repository.get_x3_combo_map()
        except Exception:  # noqa: BLE001 — leitura SX3 nunca mascara o write
            combo_map = {}
        if combo_map:
            fields, repairs = repair_legacy_combo_values(fields, combo_map)
            if repairs:
                log_info(
                    "protheus_product_create_legacy_combo_repair "
                    f"product_code={normalized_code} repairs={repairs}"
                )

        token = self._token_service.get_valid_token(config)
        body = build_upstream_product_update_body(
            product_code=normalized_code, fields=fields, codusr=codusr
        )
        url = product_create_url(config)

        operation_id = self._write_tracker.begin(
            action="create",
            method="POST",
            resource=RESOURCE_PRODUCT,
            resource_key=normalized_code,
            environment_key=environment_key,
            caller_app=caller_app,
            actor_user_id=actor_user_id,
            codusr=codusr,
            request_fields=fields,
            outbound_body=body,
            correlation_id=correlation_id,
            request_id=request_id,
        )

        try:
            upstream = self._gateway.create_product(
                url=url,
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
            operation_id, upstream=upstream, resource_key=normalized_code
        )

        log_info(
            "protheus_product_create_submitted "
            f"actor_user_id={actor_user_id} product_code={normalized_code} "
            f"operation_id={operation_id}"
        )

        # Read-back: record must exist and sent fields must match.
        confirmation = "ACKNOWLEDGED"
        divergent: list[str] = []
        try:
            after = self._product_repository.get_product_snapshot(normalized_code)
            if after is None:
                divergent = sorted(fields.keys())
            else:
                for field, expected in fields.items():
                    if not snapshot_value_matches(field, after.get(field), expected):
                        divergent.append(field)
            if not divergent:
                confirmation = "CONFIRMED"
        except Exception:  # noqa: BLE001 — read-back failure never hides the write
            divergent = sorted(fields.keys())

        result: dict[str, Any] = {
            "product_code": normalized_code,
            "codusr": codusr,
            "fields_sent": sorted(fields.keys()),
            "confirmation": confirmation,
            "operation_id": operation_id,
            **upstream,
        }
        if divergent:
            result["readback_divergent_fields"] = divergent
        if repairs:
            result["legacy_combo_repairs"] = repairs
        if not ack_recorded:
            result["tracking_warning"] = "acknowledgement_record_failed"
        return result
