"""Testes do notify OpenAPI → consumidores."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.services.openapi_consumer_notify_service import (
    OpenApiConsumerNotifyService,
)


def test_list_targets_defaults() -> None:
    service = OpenApiConsumerNotifyService()
    targets = {item["name"]: item["url"] for item in service.list_targets()}
    assert "chat" in targets
    assert "tv" in targets
    assert "sync-api-delpi" in targets["chat"]
    assert "openapi/sync" in targets["tv"]


def test_notify_all_skips_without_token(monkeypatch) -> None:
    monkeypatch.delenv("API_DELPI_INTERNAL_SERVICE_TOKEN", raising=False)
    monkeypatch.setenv("OPENAPI_CONSUMER_NOTIFY_ENABLED", "true")
    report = OpenApiConsumerNotifyService().notify_all()
    assert report["ok"] is False
    assert report.get("skipped") is True


def test_notify_all_posts_to_targets(monkeypatch) -> None:
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "secret-token")
    monkeypatch.setenv("OPENAPI_CONSUMER_NOTIFY_ENABLED", "true")
    monkeypatch.setenv(
        "OPENAPI_CONSUMER_CHAT_SYNC_URL",
        "http://chat.test/chat/internal/openapi/sync-api-delpi",
    )
    monkeypatch.setenv(
        "OPENAPI_CONSUMER_TV_SYNC_URL",
        "http://tv.test/data/openapi/sync",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True}

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        report = OpenApiConsumerNotifyService().notify_all()

    assert report["ok"] is True
    assert len(report["results"]) == 2
    assert mock_client.post.call_count == 2
    first_headers = mock_client.post.call_args_list[0].kwargs["headers"]
    assert first_headers["X-Delpi-Service-Token"] == "secret-token"
    chat_url = mock_client.post.call_args_list[0].args[0]
    assert "updateSchema=1" in chat_url


def test_notify_disabled(monkeypatch) -> None:
    monkeypatch.setenv("OPENAPI_CONSUMER_NOTIFY_ENABLED", "false")
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "secret")
    report = OpenApiConsumerNotifyService().notify_all()
    assert report["ok"] is True
    assert report.get("skipped") is True


def test_chat_sync_url_updates_schema_by_default(monkeypatch) -> None:
    monkeypatch.delenv("OPENAPI_CONSUMER_CHAT_SYNC_URL", raising=False)
    monkeypatch.delenv("OPENAPI_CONSUMER_CHAT_SKIP_EMBEDDINGS", raising=False)
    url = OpenApiConsumerNotifyService().chat_sync_url()
    assert "updateSchema=1" in url
    assert "skipEmbeddings=0" in url


def test_chat_sync_url_can_skip_embeddings(monkeypatch) -> None:
    monkeypatch.setenv("OPENAPI_CONSUMER_CHAT_SKIP_EMBEDDINGS", "true")
    url = OpenApiConsumerNotifyService().chat_sync_url()
    assert "updateSchema=1" in url
    assert "skipEmbeddings=1" in url
