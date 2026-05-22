from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.revisao_workflow_notification_service import (
    RevisaoWorkflowNotificationService,
)
from tm_app.infrastructure.integrations.core_notifications_client import CoreNotificationsClient


def _revisao_row():
    return {
        "revisao_id": "11111111-1111-1111-1111-111111111111",
        "processo_id": "22222222-2222-2222-2222-222222222222",
        "versao_revisao": 3,
    }


@patch.object(CoreNotificationsClient, "dispatch", return_value={"createdCount": 1})
@patch(
    "tm_app.application.services.revisao_workflow_notification_service.settings.TM_WORKFLOW_APPROVER_EMAILS",
    "aprovador@delpi.com.br",
)
@patch(
    "tm_app.application.services.revisao_workflow_notification_service.settings.TM_PORTAL_ROUTE",
    "/apps/transformometro",
)
def test_notify_submitted_sends_to_approvers(mock_dispatch):
    client = CoreNotificationsClient(enabled=True)
    client._base_url = "http://core-api:8000/core-api"
    client._token = "secret"

    with patch.object(
        RevisaoWorkflowNotificationService, "_processo_label", return_value="PROC-0001 — Teste"
    ):
        RevisaoWorkflowNotificationService(client).notify_submitted(
            _revisao_row(),
            actor_email="autor@delpi.com.br",
        )

    mock_dispatch.assert_called_once()
    payload = mock_dispatch.call_args[0][0]
    assert payload["category"] == "transformometro"
    assert payload["emails"] == ["aprovador@delpi.com.br"]
    assert "revisao:submitted" in payload["metadata"]["event"]
    assert payload["metadata"]["deepPath"].endswith(
        "/processos/22222222-2222-2222-2222-222222222222/revisoes/11111111-1111-1111-1111-111111111111"
    )


@patch.object(CoreNotificationsClient, "dispatch", return_value={"createdCount": 1})
@patch(
    "tm_app.application.services.revisao_workflow_notification_service.AuditRepository"
)
@patch(
    "tm_app.application.services.revisao_workflow_notification_service.settings.TM_PORTAL_ROUTE",
    "/apps/transformometro",
)
def test_notify_decision_sends_to_submitter(mock_audit_cls, mock_dispatch):
    mock_audit_cls.return_value.fetch_one.return_value = {
        "user_email": "submitter@delpi.com.br",
    }

    client = CoreNotificationsClient(enabled=True)
    client._base_url = "http://core-api:8000/core-api"
    client._token = "secret"

    with patch.object(
        RevisaoWorkflowNotificationService, "_processo_label", return_value="PROC-0001"
    ):
        RevisaoWorkflowNotificationService(client).notify_decision(
            _revisao_row(),
            decision="aprovada",
            actor_email="gestor@delpi.com.br",
        )

    mock_dispatch.assert_called_once()
    payload = mock_dispatch.call_args[0][0]
    assert payload["type"] == "success"
    assert payload["emails"] == ["submitter@delpi.com.br"]
    assert payload["metadata"]["event"] == "revisao:aprovada"


@patch.object(CoreNotificationsClient, "dispatch")
def test_notify_submitted_skips_when_not_configured(mock_dispatch):
    client = CoreNotificationsClient(enabled=False)
    RevisaoWorkflowNotificationService(client).notify_submitted(
        _revisao_row(),
        actor_email="a@b.com",
    )
    mock_dispatch.assert_not_called()
