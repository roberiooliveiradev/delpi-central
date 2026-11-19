"""Update an existing Protheus product via delpiproduto — gated, no retry.

Every attempt is registered in the integration execution tracker BEFORE the
upstream call (fail closed). The resolved actor identity (Core/JWT) travels
upstream as the `codusr` meta-field — outside the B1_* catalog — for the
`AIF_ZCDUSR` audit stamp, and is kept in the tracking ledger too; clients
can never inject it (forbidden identity keys are rejected at the edge).

Partial-update contract (v2): the client sends only the fields to change;
this surface reads the current SB1 snapshot (governed SQL read), merges
the delta and always sends the complete representation upstream — the
ExecAuto never receives an omission that could zero a column. After the
upstream ACK we read the record back: matching changed fields promote the
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
    merge_product_update_fields,
    normalize_product_update_fields,
    product_update_url,
    repair_legacy_combo_values,
    snapshot_value_matches,
    validate_product_code,
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


class UpdateProtheusProductUseCase:
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
        product_code: str,
        product: Mapping[str, Any],
        caller_app: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_code = validate_product_code(product_code)
        fields = normalize_product_update_fields(product)

        if not settings.PROTHEUS_PRODUCT_UPDATE_ENABLED:
            log_info(
                "protheus_product_update_blocked_by_feature_gate "
                f"actor_user_id={actor_user_id} product_code={normalized_code}"
            )
            raise ProtheusRestError(
                "Alteração de produto Protheus desabilitada neste ambiente "
                "(PROTHEUS_PRODUCT_UPDATE_ENABLED=false). "
                "Nenhuma escrita foi enviada ao ERP.",
                code="PROTHEUS_PRODUCT_UPDATE_DISABLED",
                status_code=503,
                recoverable=False,
            )

        # Ator real resolvido via Core — enviado upstream como meta-campo
        # `codusr` para auditoria AIF_ZCDUSR (DLP04I01) e no ledger.
        codusr = resolve_actor_codusr(self._identity_gateway, actor_user_id)
        raw = self._params_repository.load_raw_params()
        config = resolve_protheus_rest_config(raw)
        assert_protheus_write_target(
            config, settings.PROTHEUS_REST_EXPECTED_BASE_URL
        )
        environment_key = environment_key_from_config(
            config, settings.INTRANET_PARAMS_AMBIENTE or ""
        )

        # Snapshot governado (read-only SQL) → merge do delta → body completo.
        # A representação parcial nunca vai ao ExecAuto (risco de zeramento).
        snapshot = self._product_repository.get_product_snapshot(normalized_code)
        if snapshot is None:
            raise ProtheusRestError(
                "Produto não encontrado na base TOTVS deste ambiente.",
                code="PROTHEUS_PRODUCT_NOT_FOUND",
                status_code=404,
                recoverable=False,
            )
        merged = merge_product_update_fields(snapshot=snapshot, changes=fields)

        # Reparo de valor legado fora do combo X3: o ExecAuto revalida
        # TODO campo enviado (FWNOLIST em literal "S"/"N" legado em
        # combos 1=Sim;2=Não). Só equivalências inequívocas de rótulo
        # são reparadas; o restante segue para validação oficial.
        # Reparos ficam auditados no resultado e no ledger (outbound).
        repairs: dict[str, dict[str, str]] = {}
        try:
            combo_map = self._product_repository.get_x3_combo_map()
        except Exception:  # noqa: BLE001 — falha de leitura SX3 não deve
            # mascarar o write: sem mapa não há reparo; o upstream decide.
            combo_map = {}
        if combo_map:
            merged, repairs = repair_legacy_combo_values(merged, combo_map)
            if repairs:
                log_info(
                    "protheus_product_update_legacy_combo_repair "
                    f"product_code={normalized_code} repairs={repairs}"
                )

        token = self._token_service.get_valid_token(config)
        body = build_upstream_product_update_body(
            product_code=normalized_code, fields=merged, codusr=codusr
        )
        url = product_update_url(config)

        # Tracking persists CREATED + SENDING before any upstream byte.
        operation_id = self._write_tracker.begin(
            action="update",
            method="PUT",
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
            upstream = self._gateway.update_product(
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
            "protheus_product_update_submitted "
            f"actor_user_id={actor_user_id} product_code={normalized_code} "
            f"operation_id={operation_id}"
        )

        # Read-back: divergência mantém ACKNOWLEDGED; match promove CONFIRMED.
        # Compara TODOS os campos merged (representação completa enviada),
        # não só o delta — campo não alterado zerado/corrompido pelo
        # ExecAuto também é divergência a investigar.
        confirmation = "ACKNOWLEDGED"
        divergent: list[str] = []
        try:
            after = self._product_repository.get_product_snapshot(normalized_code)
            if after is None:
                divergent = sorted(merged.keys())
            else:
                for field, expected in merged.items():
                    if not snapshot_value_matches(field, after.get(field), expected):
                        divergent.append(field)
            if not divergent:
                confirmation = "CONFIRMED"
        except Exception:  # noqa: BLE001 — read-back failure never hides the write
            divergent = sorted(merged.keys())

        result: dict[str, Any] = {
            "product_code": normalized_code,
            "codusr": codusr,
            "fields_sent": sorted(fields.keys()),
            "fields_merged": len(merged),
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
