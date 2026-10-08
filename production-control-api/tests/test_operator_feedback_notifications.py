"""C6 — Notificações Minha DELPI via Core API para Operator Feedback.

Cobre: payloads PCP/Alimentador, filtro de filial (requiredPermissionCodes),
uma notificação para N materiais, ausência de dados sensíveis, best-effort
(falha da Core nunca desfaz o feedback) e a não-duplicidade (conflict e
honeypot não disparam).
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx
import pytest

from production_control_app.application.services.operator_feedback_notification_service import (  # noqa: E501
    OperatorFeedbackNotificationService,
)
from production_control_app.application.services.operator_feedback_service import (  # noqa: E501
    OperatorFeedbackService,
)
from production_control_app.application.services.public_operator_feedback_service import (  # noqa: E501
    PublicOperatorFeedbackService,
)
from production_control_app.domain.errors import (
    NotificationGatewayContractError,
    NotificationGatewayUnauthorized,
    NotificationGatewayUnavailable,
    OperatorFeedbackConflict,
)
from production_control_app.infrastructure.gateways.core_api_notification_gateway import (  # noqa: E501
    CoreApiNotificationGateway,
)
from tests.test_operator_feedback import FakeOperatorFeedbackRepository
from tests.test_operator_feedback_public_api import (
    FakeMachineLoad,
    FakeOperationMaterials,
    FakeSessionResolver,
    _context,
    _sd4_material,
    _session,
)


class GatewaySpy:
    """Spy que pode falhar — verifica payload + best-effort."""

    def __init__(self, *, error: Exception | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.error = error

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(payload)
        if self.error is not None:
            raise self.error
        return {"createdCount": 1}


def _feedback(**overrides: Any) -> dict[str, Any]:
    base = {
        "id": str(uuid.uuid4()),
        "branch": "01",
        "production_order": "24640401002",
        "operation_code": "03",
        "reported_work_center": "CT-63",
        "feedback_type": "cannot_produce",
        "reason_code": "missing_material",
        "operator_code": "001234",
        "operator_name": "Maria Silva",
        "note": "não localizado na bancada",
        "status": "open",
    }
    base.update(overrides)
    return base


# --- payloads ---------------------------------------------------------------


def test_pcp_payload_shape_and_branch_filter() -> None:
    spy = GatewaySpy()
    svc = OperatorFeedbackNotificationService(gateway=spy)
    svc.notify_feedback_created(feedback=_feedback(), material_count=0)

    assert len(spy.calls) == 1
    p = spy.calls[0]
    assert p["title"] == "Novo impedimento na produção"
    assert "OP 24640401002" in p["message"]
    assert "CT-63" in p["message"]
    assert "Falta de matéria-prima" in p["message"]
    assert p["type"] == "warning"
    assert p["category"] == "production_control_operator_feedback"
    assert p["presentation"] == "text"
    assert p["sourceApp"] == "production-control"
    assert p["permissionCodes"] == ["production-control.machine-load.view"]
    assert p["requiredPermissionCodes"] == [
        "production-control.view.filial-01"
    ]
    assert p["action"]["type"] == "portal_route"
    assert p["action"]["label"] == "Abrir Carga Máquina"
    assert (
        p["action"]["target"]
        == "/apps/production-control/machine-load?branch=01&locate=24640401002"
    )
    assert p["metadata"]["event"] == "operator_feedback_created"
    assert p["metadata"]["feedbackId"] == _feedback_id(p)


def _feedback_id(payload: dict[str, Any]) -> Any:
    return payload["metadata"]["feedbackId"]


def test_branch_02_maps_to_filial_02() -> None:
    spy = GatewaySpy()
    svc = OperatorFeedbackNotificationService(gateway=spy)
    svc.notify_feedback_created(
        feedback=_feedback(branch="02"), material_count=1
    )
    assert spy.calls[0]["requiredPermissionCodes"] == [
        "production-control.view.filial-02"
    ]
    assert "branch=02" in spy.calls[0]["action"]["target"]
    assert spy.calls[1]["requiredPermissionCodes"] == [
        "production-control.view.filial-02"
    ]


def test_missing_material_with_items_also_notifies_line_feeder() -> None:
    spy = GatewaySpy()
    svc = OperatorFeedbackNotificationService(gateway=spy)
    svc.notify_feedback_created(feedback=_feedback(), material_count=2)

    assert len(spy.calls) == 2  # UMA notificação para N materiais
    feeder = spy.calls[1]
    assert feeder["title"] == "Solicitação urgente de material"
    assert "2 materiais" in feeder["message"]
    assert "CT-63" in feeder["message"]
    assert feeder["category"] == "production_control_line_feeder_urgent"
    assert feeder["permissionCodes"] == ["production-control.line-feeder.view"]
    assert feeder["requiredPermissionCodes"] == [
        "production-control.view.filial-01"
    ]
    assert (
        feeder["action"]["target"]
        == "/apps/production-control/line-feeder?branch=01"
    )
    assert feeder["metadata"]["event"] == (
        "operator_feedback_material_request_created"
    )
    assert feeder["metadata"]["materialCount"] == 2


def test_missing_material_without_items_notifies_only_pcp() -> None:
    spy = GatewaySpy()
    svc = OperatorFeedbackNotificationService(gateway=spy)
    svc.notify_feedback_created(feedback=_feedback(), material_count=0)
    assert len(spy.calls) == 1
    assert spy.calls[0]["category"] == "production_control_operator_feedback"


def test_other_reason_never_notifies_line_feeder() -> None:
    spy = GatewaySpy()
    svc = OperatorFeedbackNotificationService(gateway=spy)
    svc.notify_feedback_created(
        feedback=_feedback(reason_code="other_reason"), material_count=3
    )
    assert len(spy.calls) == 1


def test_payloads_carry_no_sensitive_data() -> None:
    import json

    spy = GatewaySpy()
    svc = OperatorFeedbackNotificationService(gateway=spy)
    svc.notify_feedback_created(feedback=_feedback(), material_count=1)
    blob = json.dumps(spy.calls, ensure_ascii=False)
    for forbidden in (
        "001234",           # matrícula do operador
        "Maria Silva",      # nome do operador
        "não localizado",   # observação livre
        "sess-token",       # token de sessão
        "operatorCode",     # campo de identidade do operador
        "operatorName",
        "operator_code",
        "operator_name",
    ):
        assert forbidden not in blob


def test_unknown_branch_dispatches_nothing() -> None:
    spy = GatewaySpy()
    svc = OperatorFeedbackNotificationService(gateway=spy)
    svc.notify_feedback_created(feedback=_feedback(branch="99"))
    assert spy.calls == []


def test_gateway_error_does_not_propagate_and_second_payload_still_goes() -> (
    None
):
    spy = GatewaySpy(error=NotificationGatewayUnavailable("down"))
    svc = OperatorFeedbackNotificationService(gateway=spy)
    # não deve levantar
    svc.notify_feedback_created(feedback=_feedback(), material_count=2)
    assert len(spy.calls) == 2


def test_none_gateway_is_noop() -> None:
    svc = OperatorFeedbackNotificationService(gateway=None)
    svc.notify_feedback_created(feedback=_feedback(), material_count=2)


# --- gateway HTTP -----------------------------------------------------------


def _gateway(handler) -> CoreApiNotificationGateway:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return CoreApiNotificationGateway(
        base_url="http://core-api:8000",
        service_token="token-secreto",
        timeout=1,
        client=client,
    )


def test_gateway_posts_contract_with_service_token() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["token"] = request.headers.get("X-Delpi-Service-Token")
        seen["accept"] = request.headers.get("Accept")
        return httpx.Response(201, json={"createdCount": 2})

    gw = _gateway(handler)
    out = gw.dispatch({"title": "t", "message": "m"})
    assert seen["url"] == "http://core-api:8000/integrations/notifications"
    assert seen["token"] == "token-secreto"
    assert seen["accept"] == "application/json"
    assert out["createdCount"] == 2


def test_gateway_401_maps_to_unauthorized() -> None:
    gw = _gateway(lambda r: httpx.Response(401, json={"error": "x"}))
    with pytest.raises(NotificationGatewayUnauthorized):
        gw.dispatch({"title": "t"})


def test_gateway_403_maps_to_unauthorized() -> None:
    gw = _gateway(lambda r: httpx.Response(403, json={"error": "x"}))
    with pytest.raises(NotificationGatewayUnauthorized):
        gw.dispatch({"title": "t"})


def test_gateway_5xx_maps_to_unavailable() -> None:
    gw = _gateway(lambda r: httpx.Response(503, json={"error": "x"}))
    with pytest.raises(NotificationGatewayUnavailable):
        gw.dispatch({"title": "t"})


def test_gateway_timeout_maps_to_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout")

    gw = _gateway(handler)
    with pytest.raises(NotificationGatewayUnavailable):
        gw.dispatch({"title": "t"})


def test_gateway_4xx_maps_to_contract_error() -> None:
    gw = _gateway(lambda r: httpx.Response(422, json={"error": "x"}))
    with pytest.raises(NotificationGatewayContractError):
        gw.dispatch({"title": "t"})


def test_gateway_non_dict_response_maps_to_contract_error() -> None:
    gw = _gateway(lambda r: httpx.Response(200, json=["not-a-dict"]))
    with pytest.raises(NotificationGatewayContractError):
        gw.dispatch({"title": "t"})


def test_gateway_without_config_is_unavailable() -> None:
    gw = CoreApiNotificationGateway(base_url="", service_token="", client=None)
    with pytest.raises(NotificationGatewayUnavailable):
        gw.dispatch({"title": "t"})


# --- integração com a criação do feedback ------------------------------------


def _public_svc(
    notifications: Any | None,
    *,
    notify: Any | None = None,
) -> tuple[PublicOperatorFeedbackService, FakeOperatorFeedbackRepository]:
    repo = FakeOperatorFeedbackRepository()
    svc = PublicOperatorFeedbackService(
        run_service=FakeSessionResolver(_session()),
        machine_load=FakeMachineLoad(_context()),
        feedbacks=OperatorFeedbackService(feedbacks=repo),
        run_lookup=lambda **kwargs: None,
        notify=notify,
        operation_materials=FakeOperationMaterials(
            [_sd4_material("10081234"), _sd4_material("10085678")]
        ),
        feedback_materials=repo,
        notifications=notifications,
    )
    return svc, repo


def _report(svc: PublicOperatorFeedbackService, **overrides: Any) -> Any:
    kwargs = {
        "session_token": "sess-token",
        "production_order": "24640401002",
        "operation_code": "03",
        "feedback_type": "cannot_produce",
        "reason_code": "missing_material",
        "note": "Falta terminal",
        "material_codes": ["10081234"],
    }
    kwargs.update(overrides)
    return svc.report(**kwargs)


def test_report_notifies_pcp_and_feeder_once() -> None:
    spy = GatewaySpy()
    svc, _ = _public_svc(
        OperatorFeedbackNotificationService(gateway=spy)
    )
    _report(svc)
    categories = [c["category"] for c in spy.calls]
    assert categories == [
        "production_control_operator_feedback",
        "production_control_line_feeder_urgent",
    ]


def test_invalid_reason_fails_before_any_notification() -> None:
    spy = GatewaySpy()
    svc, _ = _public_svc(
        OperatorFeedbackNotificationService(gateway=spy)
    )
    with pytest.raises(Exception):
        _report(svc, reason_code="cannot_start", material_codes=None)
    assert spy.calls == []


def test_conflict_retry_does_not_notify_again() -> None:
    spy = GatewaySpy()
    svc, _ = _public_svc(
        OperatorFeedbackNotificationService(gateway=spy)
    )
    _report(svc)
    assert len(spy.calls) == 2
    with pytest.raises(OperatorFeedbackConflict):
        _report(svc)
    assert len(spy.calls) == 2  # nenhuma notificação extra


def test_notification_failure_keeps_feedback_created() -> None:
    spy = GatewaySpy(error=NotificationGatewayUnavailable("down"))
    svc, repo = _public_svc(
        OperatorFeedbackNotificationService(gateway=spy)
    )
    item = _report(svc)
    assert item["status"] == "open"
    assert repo.rows  # feedback permanece persistido


def test_notification_exception_inside_service_is_contained() -> None:
    class ExplodingNotifications:
        def notify_feedback_created(self, **kwargs: Any) -> None:
            raise RuntimeError("boom")

    svc, repo = _public_svc(ExplodingNotifications())
    item = _report(svc)
    assert item["status"] == "open"
