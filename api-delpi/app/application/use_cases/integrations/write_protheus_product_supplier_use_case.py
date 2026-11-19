"""SA5 product-supplier link writes via delpiprodforn — gated, no retry.

Three governed actions share one pipeline: create (POST /incluir),
update (PUT /alterar) and delete (DELETE /excluir) of the MATA061
model link. Identity is the full model key; attrs cover the complete
SX3 editable catalog (113 fields) — the upstream model enforces the
form-field intersection.

Read-back: after the upstream ACK the link is re-read through the
governed SQL repository (read-only) — create/update must find the link
with matching sent attrs (CONFIRMED); delete must find it absent.
"""

from __future__ import annotations

from typing import Any, Literal, Mapping
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
    validate_product_code,
)
from app.application.services.integrations.protheus_product_supplier_payload import (
    build_upstream_product_supplier_body,
    normalize_product_supplier_attrs,
    normalize_product_supplier_identity,
    product_supplier_url,
    snapshot_value_matches,
)
from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
)
from app.application.services.integrations.protheus_write_tracker import (
    ProtheusWriteTracker,
    RESOURCE_PRODUCT_SUPPLIER,
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

Action = Literal["create", "update", "delete"]

_UPSTREAM_METHOD = {"create": "incluir", "update": "alterar", "delete": "excluir"}
_HTTP_METHOD = {"create": "POST", "update": "PUT", "delete": "DELETE"}


class WriteProtheusProductSupplierUseCase:
    def __init__(
        self,
        *,
        params_repository: ProtheusIntegrationParamsRepository,
        token_service: ProtheusTokenService,
        gateway: ProtheusRestGateway,
        identity_gateway: CoreProtheusIdentityGateway,
        supplier_link_repository,
        tracker: IntegrationTrackingService | None = None,
    ) -> None:
        self._params_repository = params_repository
        self._token_service = token_service
        self._gateway = gateway
        self._identity_gateway = identity_gateway
        self._link_repository = supplier_link_repository
        self._write_tracker = ProtheusWriteTracker(tracker)

    def execute(
        self,
        *,
        action: Action,
        actor_user_id: UUID,
        product_code: str,
        supplier: Mapping[str, Any],
        attributes: Mapping[str, Any] | None = None,
        caller_app: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        if action not in _UPSTREAM_METHOD:
            raise _err("Ação de vínculo inválida.", "PROTHEUS_PRODUCT_SUPPLIER_ACTION_INVALID")
        normalized_code = validate_product_code(product_code)
        identity = normalize_product_supplier_identity(supplier)
        attrs = (
            None
            if action == "delete"
            else normalize_product_supplier_attrs(
                attributes, require_all=(action == "create")
            )
        )

        if not settings.PROTHEUS_PRODUCT_SUPPLIER_WRITE_ENABLED:
            log_info(
                "protheus_product_supplier_write_blocked_by_feature_gate "
                f"actor_user_id={actor_user_id} product_code={normalized_code} "
                f"action={action}"
            )
            raise ProtheusRestError(
                "Escrita de vínculo produto-fornecedor desabilitada neste "
                "ambiente (PROTHEUS_PRODUCT_SUPPLIER_WRITE_ENABLED=false). "
                "Nenhuma escrita foi enviada ao ERP.",
                code="PROTHEUS_PRODUCT_SUPPLIER_WRITE_DISABLED",
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

        resource_key = _link_key(normalized_code, identity)
        body = build_upstream_product_supplier_body(
            product_code=normalized_code,
            identity=identity,
            attrs=attrs,
            codusr=codusr,
        )
        url = product_supplier_url(config, _UPSTREAM_METHOD[action])
        token = self._token_service.get_valid_token(config)

        operation_id = self._write_tracker.begin(
            action=action,
            method=_HTTP_METHOD[action],
            resource=RESOURCE_PRODUCT_SUPPLIER,
            resource_key=resource_key,
            environment_key=environment_key,
            caller_app=caller_app,
            actor_user_id=actor_user_id,
            codusr=codusr,
            request_fields=dict(identity) | dict(attrs or {}),
            outbound_body=body,
            correlation_id=correlation_id,
            request_id=request_id,
        )

        try:
            upstream = self._gateway.write_product_supplier(
                method=_HTTP_METHOD[action],
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
            operation_id, upstream=upstream, resource_key=resource_key
        )

        log_info(
            "protheus_product_supplier_write_submitted "
            f"actor_user_id={actor_user_id} key={resource_key} "
            f"action={action} operation_id={operation_id}"
        )

        # Read-back via governed SQL snapshot (read-only).
        confirmation = "ACKNOWLEDGED"
        divergent: list[str] = []
        try:
            after = self._link_repository.get_link_snapshot(
                product_code=normalized_code,
                supplier_code=identity["A5_FORNECE"],
                supplier_store=identity["A5_LOJA"],
                manufacturer_code=identity["A5_FABR"],
                manufacturer_store=identity["A5_FALOJA"],
                grade_reference=identity["A5_REFGRD"],
            )
            if action == "delete":
                if after is None:
                    confirmation = "CONFIRMED"
                else:
                    divergent = ["link_still_present"]
            elif after is None:
                divergent = sorted((attrs or {}).keys()) or ["link_missing"]
            else:
                for field, expected in (attrs or {}).items():
                    if not snapshot_value_matches(field, after.get(field), expected):
                        divergent.append(field)
                if not divergent:
                    confirmation = "CONFIRMED"
        except Exception:  # noqa: BLE001 — read-back failure never hides the write
            divergent = sorted((attrs or {}).keys()) or ["readback_failed"]

        result: dict[str, Any] = {
            "product_code": normalized_code,
            "link_key": resource_key,
            "action": action,
            "codusr": codusr,
            "confirmation": confirmation,
            "operation_id": operation_id,
            **upstream,
        }
        if attrs:
            result["fields_sent"] = sorted(attrs.keys())
        if divergent:
            result["readback_divergent_fields"] = divergent
        if not ack_recorded:
            result["tracking_warning"] = "acknowledgement_record_failed"
        return result


def _link_key(product_code: str, identity: Mapping[str, str]) -> str:
    return (
        f"{product_code}x{identity['A5_FORNECE']}/{identity['A5_LOJA']}"
        f"-{identity['A5_FABR']}/{identity['A5_FALOJA']}"
        f"@{identity['A5_REFGRD']}"
    )


def _err(message: str, code: str, status: int = 422) -> ProtheusRestError:
    return ProtheusRestError(message, code=code, status_code=status, recoverable=False)
