from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
    MicrosoftGraphMailClient,
)


def _client(http_client: Any, *, recipient: str | None = "ouvidoria@delpi.com.br") -> MicrosoftGraphMailClient:
    return MicrosoftGraphMailClient(
        tenant_id="tenant-id",
        client_id="client-id",
        client_secret="client-secret",
        sender="minhadelpi@delpi.com.br",
        recipient=recipient,
        http_client=http_client,
    )


def _token_then_accepted(http_client: MagicMock) -> None:
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


def test_send_mail_to_multiple_recipients_and_attachment() -> None:
    http_client = MagicMock()
    _token_then_accepted(http_client)
    client = _client(http_client, recipient=None)

    client.send_mail_to(
        subject="Rupturas 30d",
        html_body="<p>lista</p>",
        to_addresses=["a@delpi.com.br", "b@delpi.com.br", "a@delpi.com.br"],
        attachments=[
            {
                "name": "rupturas.csv",
                "content_type": "text/csv",
                "content_base64": "YTtiCg==",
            }
        ],
    )

    send_call = http_client.post.call_args_list[1]
    assert "users/minhadelpi@delpi.com.br/sendMail" in send_call.args[0]
    message = send_call.kwargs["json"]["message"]
    addresses = [r["emailAddress"]["address"] for r in message["toRecipients"]]
    assert addresses == ["a@delpi.com.br", "b@delpi.com.br"]
    assert message["attachments"][0]["@odata.type"] == "#microsoft.graph.fileAttachment"
    assert message["attachments"][0]["name"] == "rupturas.csv"
    assert message["attachments"][0]["contentBytes"] == "YTtiCg=="
    assert "isInline" not in message["attachments"][0]


def test_send_mail_to_retries_on_transient_http_status() -> None:
    http_client = MagicMock()
    http_client.post.side_effect = [
        httpx.Response(
            200,
            json={"access_token": "tok-abc"},
            request=httpx.Request("POST", "https://example/token"),
        ),
        httpx.Response(
            503,
            request=httpx.Request("POST", "https://graph.microsoft.com/v1.0/users/x/sendMail"),
        ),
        httpx.Response(
            202,
            request=httpx.Request("POST", "https://graph.microsoft.com/v1.0/users/x/sendMail"),
        ),
    ]
    client = _client(http_client, recipient=None)
    sleeps: list[float] = []

    client.send_mail_to(
        subject="Rupturas 30d",
        html_body="<p>lista</p>",
        to_addresses=["a@delpi.com.br"],
        sleep_fn=sleeps.append,
    )

    assert sleeps == [1.0]
    assert http_client.post.call_count == 3


def test_send_mail_to_inline_cid_attachment() -> None:
    http_client = MagicMock()
    _token_then_accepted(http_client)
    client = _client(http_client, recipient=None)

    client.send_mail_to(
        subject="Rupturas 30d",
        html_body='<img src="cid:delpi-logo" alt="DELPI" />',
        to_addresses=["a@delpi.com.br"],
        attachments=[
            {
                "name": "logo_delpi.png",
                "content_type": "image/png",
                "content_base64": "iVBOR",
                "is_inline": True,
                "content_id": "delpi-logo",
            }
        ],
    )

    attachment = http_client.post.call_args_list[1].kwargs["json"]["message"][
        "attachments"
    ][0]
    assert attachment["isInline"] is True
    assert attachment["contentId"] == "delpi-logo"
    assert attachment["contentType"] == "image/png"


def test_send_mail_legacy_uses_fixed_recipient() -> None:
    http_client = MagicMock()
    _token_then_accepted(http_client)
    client = _client(http_client)

    client.send_mail(subject="Denúncia", html_body="<p>x</p>")

    message = http_client.post.call_args_list[1].kwargs["json"]["message"]
    assert message["toRecipients"][0]["emailAddress"]["address"] == "ouvidoria@delpi.com.br"


def test_send_mail_to_rejects_empty_recipients() -> None:
    client = _client(MagicMock(), recipient=None)
    with pytest.raises(GraphMailError, match="vazia"):
        client.send_mail_to(subject="s", html_body="<p>x</p>", to_addresses=["  ", ""])


def test_send_mail_requires_recipient() -> None:
    client = _client(MagicMock(), recipient=None)
    with pytest.raises(GraphMailError, match="GRAPH_MAIL_RECIPIENT"):
        client.send_mail(subject="s", html_body="<p>x</p>")
