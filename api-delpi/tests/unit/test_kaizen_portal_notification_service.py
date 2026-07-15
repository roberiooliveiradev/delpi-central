from unittest.mock import MagicMock, patch

from app.application.services import kaizen_portal_notification_service as svc


def test_notify_public_suggestion_skips_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr(svc.settings, "KAIZEN_NOTIFICATIONS_ENABLED", False)
    assert svc.notify_public_suggestion_created(record={"id": "abc", "title": "T"}) is False


def test_notify_public_suggestion_posts_permission_code(monkeypatch) -> None:
    monkeypatch.setattr(svc.settings, "KAIZEN_NOTIFICATIONS_ENABLED", True)
    monkeypatch.setattr(svc.settings, "CORE_API_BASE_URL", "http://core.test")
    monkeypatch.setattr(svc.settings, "CORE_API_INTEGRATIONS_SERVICE_TOKEN", "token")

    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    with patch.object(svc.httpx, "Client", return_value=mock_client):
        ok = svc.notify_public_suggestion_created(
            record={
                "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "title": "CT-33: reduzir setup",
                "accountable": "Maria",
                "sector": "Produtivo",
            }
        )

    assert ok is True
    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["permissionCodes"] == ["cadastro-kaizen.notify-suggestions"]
    assert payload["category"] == "cadastro_kaizen"
    assert payload["metadata"]["event"] == "kaizen_suggestion_created"
    assert "detalhe/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" in payload["action"]["target"]
