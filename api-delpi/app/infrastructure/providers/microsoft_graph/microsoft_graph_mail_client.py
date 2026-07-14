"""Cliente Microsoft Graph — envio de e-mail via client credentials."""

from __future__ import annotations

import logging
from typing import Any, Protocol

import httpx

logger = logging.getLogger(__name__)

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
GRAPH_SEND_MAIL_URL = (
    "https://graph.microsoft.com/v1.0/users/{sender}/sendMail"
)
TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

DEFAULT_TIMEOUT_SECONDS = 15.0
_MAX_ERROR_LEN = 480


class GraphMailError(RuntimeError):
    """Falha controlada de configuração, token ou envio Graph."""


class HttpClientProtocol(Protocol):
    def post(self, url: str, **kwargs: Any) -> httpx.Response: ...


def sanitize_graph_error(message: str, *, max_length: int = _MAX_ERROR_LEN) -> str:
    text = " ".join(str(message or "").split())
    if not text:
        return "Erro ao enviar e-mail via Microsoft Graph."
    lowered = text.lower()
    for needle in ("client_secret", "access_token", "bearer ", "refresh_token"):
        if needle in lowered:
            return "Erro ao enviar e-mail via Microsoft Graph."
    if len(text) > max_length:
        return text[: max_length - 1] + "…"
    return text


class MicrosoftGraphMailClient:
    """Obtém token (client credentials) e envia e-mail com sendMail."""

    def __init__(
        self,
        *,
        tenant_id: str | None,
        client_id: str | None,
        client_secret: str | None,
        sender: str | None,
        recipient: str | None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        http_client: HttpClientProtocol | None = None,
    ) -> None:
        self._tenant_id = (tenant_id or "").strip()
        self._client_id = (client_id or "").strip()
        self._client_secret = (client_secret or "").strip()
        self._sender = (sender or "").strip()
        self._recipient = (recipient or "").strip()
        self._timeout = timeout_seconds
        self._http_client = http_client

    @property
    def sender(self) -> str:
        return self._sender

    @property
    def recipient(self) -> str:
        return self._recipient

    def ensure_configured(self) -> None:
        missing = [
            name
            for name, value in (
                ("GRAPH_TENANT_ID", self._tenant_id),
                ("GRAPH_CLIENT_ID", self._client_id),
                ("GRAPH_CLIENT_SECRET", self._client_secret),
                ("GRAPH_MAIL_SENDER", self._sender),
                ("GRAPH_MAIL_RECIPIENT", self._recipient),
            )
            if not value
        ]
        if missing:
            raise GraphMailError(
                "Configuração Microsoft Graph incompleta "
                f"({', '.join(missing)})."
            )

    def get_access_token(self) -> str:
        self.ensure_configured()
        url = TOKEN_URL.format(tenant_id=self._tenant_id)
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": GRAPH_SCOPE,
            "grant_type": "client_credentials",
        }
        try:
            response = self._post(url, data=data)
        except httpx.TimeoutException as exc:
            raise GraphMailError("Timeout ao obter token Microsoft Graph.") from exc
        except httpx.HTTPError as exc:
            raise GraphMailError("Falha de conexão ao obter token Microsoft Graph.") from exc

        if response.status_code != 200:
            raise GraphMailError(
                sanitize_graph_error(
                    f"Falha ao obter token Microsoft Graph (HTTP {response.status_code})."
                )
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise GraphMailError("Resposta inválida ao obter token Microsoft Graph.") from exc
        token = payload.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise GraphMailError("Token Microsoft Graph ausente na resposta.")
        return token.strip()

    def send_mail(self, *, subject: str, html_body: str) -> None:
        token = self.get_access_token()
        url = GRAPH_SEND_MAIL_URL.format(sender=self._sender)
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_body,
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": self._recipient,
                        }
                    }
                ],
            },
            "saveToSentItems": True,
        }
        try:
            response = self._post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise GraphMailError("Timeout ao enviar e-mail via Microsoft Graph.") from exc
        except httpx.HTTPError as exc:
            raise GraphMailError(
                "Falha de conexão ao enviar e-mail via Microsoft Graph."
            ) from exc

        if response.status_code != 202:
            raise GraphMailError(
                sanitize_graph_error(
                    f"Envio Microsoft Graph rejeitado (HTTP {response.status_code})."
                )
            )
        logger.info(
            "microsoft_graph_mail_sent sender=%s recipient=%s",
            self._sender,
            self._recipient,
        )

    def _post(self, url: str, **kwargs: Any) -> httpx.Response:
        if self._http_client is not None:
            return self._http_client.post(url, **kwargs)
        with httpx.Client(timeout=self._timeout) as client:
            return client.post(url, **kwargs)
