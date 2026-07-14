from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from app.application.security import api_delpi_permissions as perms
from app.application.services.canal_denuncia_email_content_service import (
    EMAIL_SUBJECT,
    build_denuncia_email_html,
)
from app.application.use_cases.canal_denuncia.create_anonymous_denuncia_use_case import (
    CreateAnonymousDenunciaUseCase,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.canal_denuncia.postgres_canal_denuncia_repository import (
    PostgresCanalDenunciaRepository,
)
from app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GRAPH_SCOPE,
    GraphMailError,
    MicrosoftGraphMailClient,
    sanitize_graph_error,
)


class CanalDenunciaProbeRepo(PostgresCanalDenunciaRepository):
    def __init__(self) -> None:
        object.__setattr__(self, "inserted", [])
        object.__setattr__(self, "email_updates", [])
        object.__setattr__(self, "fail", False)

    def create_anonymous_denuncia(self, *, description: str) -> dict[str, Any]:
        normalized = description.strip()
        if len(normalized) < 10:
            raise PluginsRepositoryError(
                "A descrição da denúncia deve ter ao menos 10 caracteres."
            )
        if self.fail:
            raise PluginsRepositoryError("Falha ao registrar a denúncia.")
        self.inserted.append(normalized)
        return {
            "id": "11111111-1111-1111-1111-111111111111",
            "description": normalized,
            "created_at": datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc),
            "email_status": "pending",
            "email_attempts": 0,
        }

    def mark_email_sent(self, *, denuncia_id: str) -> None:
        self.email_updates.append({"id": denuncia_id, "status": "sent", "error": None})

    def mark_email_failed(self, *, denuncia_id: str, error_message: str) -> None:
        self.email_updates.append(
            {"id": denuncia_id, "status": "failed", "error": error_message}
        )


def _configured_mail_client(http_client: Any) -> MicrosoftGraphMailClient:
    return MicrosoftGraphMailClient(
        tenant_id="tenant-id",
        client_id="client-id",
        client_secret="client-secret",
        sender="canal-denuncia@delpi.com.br",
        recipient="ouvidoria@delpi.com.br",
        http_client=http_client,
    )


def test_canal_denuncia_access_permission_constant() -> None:
    assert perms.CANAL_DENUNCIA_ACCESS == "canal-denuncia.access"
    assert perms.CANAL_DENUNCIA_ACCESS in perms.CANAL_DENUNCIA_SUBMIT_PERMISSIONS
    assert len(perms.CANAL_DENUNCIA_SUBMIT_PERMISSIONS) == 1


def test_create_anonymous_denuncia_rejects_short_description() -> None:
    repo = CanalDenunciaProbeRepo()
    mail = _configured_mail_client(MagicMock())
    with pytest.raises(PluginsRepositoryError, match="10 caracteres"):
        CreateAnonymousDenunciaUseCase(repo, mail).execute(description="curto")
    assert repo.inserted == []
    assert repo.email_updates == []


def test_graph_token_uses_client_credentials() -> None:
    http_client = MagicMock()
    http_client.post.return_value = httpx.Response(
        200,
        json={"access_token": "tok-abc"},
        request=httpx.Request("POST", "https://login.microsoftonline.com/x/oauth2/v2.0/token"),
    )
    client = _configured_mail_client(http_client)

    token = client.get_access_token()

    assert token == "tok-abc"
    kwargs = http_client.post.call_args.kwargs
    assert kwargs["data"]["grant_type"] == "client_credentials"
    assert kwargs["data"]["scope"] == GRAPH_SCOPE
    assert kwargs["data"]["client_id"] == "client-id"
    assert "tenant-id" in http_client.post.call_args.args[0]


def test_graph_send_mail_uses_configured_sender_and_recipient() -> None:
    http_client = MagicMock()
    http_client.post.side_effect = [
        httpx.Response(
            200,
            json={"access_token": "tok-abc"},
            request=httpx.Request("POST", "https://example/token"),
        ),
        httpx.Response(
            202,
            request=httpx.Request("POST", "https://graph.microsoft.com/v1.0/users/x/sendMail"),
        ),
    ]
    client = _configured_mail_client(http_client)
    client.send_mail(subject=EMAIL_SUBJECT, html_body="<p>ok</p>")

    send_call = http_client.post.call_args_list[1]
    assert "users/canal-denuncia@delpi.com.br/sendMail" in send_call.args[0]
    payload = send_call.kwargs["json"]
    assert payload["saveToSentItems"] is True
    assert payload["message"]["toRecipients"][0]["emailAddress"]["address"] == (
        "ouvidoria@delpi.com.br"
    )
    assert payload["message"]["subject"] == EMAIL_SUBJECT


def test_denuncia_email_html_escapes_user_content() -> None:
    html_body = build_denuncia_email_html(
        description='<script>alert("x")</script> & conduta',
        created_at=datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc),
    )
    assert "<script>" not in html_body
    assert "&lt;script&gt;" in html_body
    assert "&amp;" in html_body
    assert "11111111-1111-1111-1111-111111111111" not in html_body


def test_create_success_marks_email_sent_and_hides_delivery_fields() -> None:
    repo = CanalDenunciaProbeRepo()
    http_client = MagicMock()
    http_client.post.side_effect = [
        httpx.Response(
            200,
            json={"access_token": "tok"},
            request=httpx.Request("POST", "https://example/token"),
        ),
        httpx.Response(
            202,
            request=httpx.Request("POST", "https://graph.microsoft.com/sendMail"),
        ),
    ]
    result = CreateAnonymousDenunciaUseCase(
        repo, _configured_mail_client(http_client)
    ).execute(description="Relato anônimo de conduta inadequada no setor.")

    assert result == {
        "id": "11111111-1111-1111-1111-111111111111",
        "createdAt": "2026-07-14T12:00:00+00:00",
    }
    assert "emailStatus" not in result
    assert "emailLastError" not in result
    assert repo.email_updates == [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "status": "sent",
            "error": None,
        }
    ]


def test_graph_failure_keeps_denuncia_and_marks_failed() -> None:
    repo = CanalDenunciaProbeRepo()
    http_client = MagicMock()
    http_client.post.side_effect = httpx.TimeoutException("timeout")

    result = CreateAnonymousDenunciaUseCase(
        repo, _configured_mail_client(http_client)
    ).execute(description="Relato anônimo de conduta inadequada no setor.")

    assert result["id"] == "11111111-1111-1111-1111-111111111111"
    assert "emailStatus" not in result
    assert "emailLastError" not in result
    assert len(repo.inserted) == 1
    assert repo.email_updates[0]["status"] == "failed"
    assert repo.email_updates[0]["error"]


def test_missing_graph_config_marks_failed_without_secrets() -> None:
    repo = CanalDenunciaProbeRepo()
    mail = MicrosoftGraphMailClient(
        tenant_id=None,
        client_id=None,
        client_secret="super-secret-value",
        sender="canal-denuncia@delpi.com.br",
        recipient="ouvidoria@delpi.com.br",
        http_client=MagicMock(),
    )

    result = CreateAnonymousDenunciaUseCase(repo, mail).execute(
        description="Relato anônimo de conduta inadequada no setor."
    )

    assert result["id"]
    assert repo.email_updates[0]["status"] == "failed"
    assert "super-secret-value" not in (repo.email_updates[0]["error"] or "")


def test_graph_payload_never_includes_authenticated_user_fields() -> None:
    http_client = MagicMock()
    http_client.post.side_effect = [
        httpx.Response(
            200,
            json={"access_token": "tok"},
            request=httpx.Request("POST", "https://example/token"),
        ),
        httpx.Response(
            202,
            request=httpx.Request("POST", "https://graph.microsoft.com/sendMail"),
        ),
    ]
    repo = CanalDenunciaProbeRepo()
    CreateAnonymousDenunciaUseCase(repo, _configured_mail_client(http_client)).execute(
        description="Relato anônimo completo para a ouvidoria."
    )
    send_payload = http_client.post.call_args_list[1].kwargs["json"]
    message = send_payload["message"]
    assert set(message.keys()) == {"subject", "body", "toRecipients"}
    assert message["toRecipients"][0]["emailAddress"]["address"] == (
        "ouvidoria@delpi.com.br"
    )
    body = message["body"]["content"].lower()
    for forbidden in (
        "user_id",
        "keycloak",
        "permission",
        "preferred_username",
        "11111111-1111-1111-1111-111111111111",
    ):
        assert forbidden not in body



def test_sanitize_graph_error_redacts_secrets() -> None:
    assert "Bearer" not in sanitize_graph_error("Authorization Bearer abc.def")
    assert sanitize_graph_error("client_secret=xyz") == (
        "Erro ao enviar e-mail via Microsoft Graph."
    )


def test_graph_mail_error_on_unexpected_status() -> None:
    http_client = MagicMock()
    http_client.post.side_effect = [
        httpx.Response(
            200,
            json={"access_token": "tok"},
            request=httpx.Request("POST", "https://example/token"),
        ),
        httpx.Response(
            500,
            request=httpx.Request("POST", "https://graph.microsoft.com/sendMail"),
        ),
    ]
    with pytest.raises(GraphMailError, match="rejeitado"):
        _configured_mail_client(http_client).send_mail(
            subject=EMAIL_SUBJECT, html_body="<p>x</p>"
        )
