"""Cliente Microsoft Graph — envio de e-mail via client credentials."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Mapping, Protocol, Sequence

import httpx


logger = logging.getLogger(__name__)

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
GRAPH_SEND_MAIL_URL = (
    "https://graph.microsoft.com/v1.0/users/{sender}/sendMail"
)
TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

DEFAULT_TIMEOUT_SECONDS = 15.0
_MAX_ERROR_LEN = 480


def _is_transient_graph_failure(
    *, status_code: int | None = None, exc: BaseException | None = None
) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.TransportError):
        return True
    if status_code is None:
        return False
    return status_code in {401, 429, 500, 502, 503, 504}


_GRAPH_RETRY_BACKOFF_SECONDS = (1.0, 2.0, 4.0)
_GRAPH_MAX_ATTEMPTS = 3


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


def _normalize_addresses(addresses: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for raw in addresses:
        email = str(raw or "").strip()
        if not email:
            continue
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(email)
    return result


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _build_attachments_payload(
    attachments: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not attachments:
        return []
    payload: list[dict[str, Any]] = []
    for item in attachments:
        name = str(item.get("name") or "").strip()
        content_type = str(item.get("content_type") or item.get("contentType") or "").strip()
        content_base64 = str(
            item.get("content_base64") or item.get("contentBytes") or ""
        ).strip()
        if not name or not content_type or not content_base64:
            raise GraphMailError(
                "Anexo Graph inválido: name, content_type e content_base64 são obrigatórios."
            )
        entry: dict[str, Any] = {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": name,
            "contentType": content_type,
            "contentBytes": content_base64,
        }
        is_inline = _truthy(item.get("is_inline") or item.get("isInline"))
        content_id = str(
            item.get("content_id") or item.get("contentId") or ""
        ).strip()
        if is_inline:
            entry["isInline"] = True
            if content_id:
                entry["contentId"] = content_id
        payload.append(entry)
    return payload


class MicrosoftGraphMailClient:
    """Obtém token (client credentials) e envia e-mail com sendMail."""

    def __init__(
        self,
        *,
        tenant_id: str | None,
        client_id: str | None,
        client_secret: str | None,
        sender: str | None,
        recipient: str | None = None,
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

    def ensure_auth_configured(self) -> None:
        missing = [
            name
            for name, value in (
                ("tenant_id", self._tenant_id),
                ("client_id", self._client_id),
                ("client_secret", self._client_secret),
                ("sender", self._sender),
            )
            if not value
        ]
        if missing:
            raise GraphMailError(
                "Configuração Microsoft Graph incompleta "
                f"({', '.join(missing)})."
            )

    def ensure_configured(self) -> None:
        self.ensure_auth_configured()
        if not self._recipient:
            raise GraphMailError(
                "Configuração Microsoft Graph incompleta (GRAPH_MAIL_RECIPIENT)."
            )

    def get_access_token(self) -> str:
        self.ensure_auth_configured()
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
        """Envio legado (canal-denúncia): destinatário fixo ``GRAPH_MAIL_RECIPIENT``."""
        self.ensure_configured()
        self.send_mail_to(
            subject=subject,
            html_body=html_body,
            to_addresses=[self._recipient],
        )

    def send_mail_to(
        self,
        *,
        subject: str,
        html_body: str,
        to_addresses: Sequence[str],
        attachments: Sequence[Mapping[str, Any]] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        """Envio com N destinatários, anexos opcionais e retry em falha transitória."""
        recipients = _normalize_addresses(to_addresses)
        if not recipients:
            raise GraphMailError("Lista de destinatários Microsoft Graph vazia.")

        url = GRAPH_SEND_MAIL_URL.format(sender=self._sender)
        message: dict[str, Any] = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_body,
            },
            "toRecipients": [
                {"emailAddress": {"address": address}} for address in recipients
            ],
        }
        attachment_payload = _build_attachments_payload(attachments)
        if attachment_payload:
            message["attachments"] = attachment_payload

        payload = {
            "message": message,
            "saveToSentItems": True,
        }
        sleeper = sleep_fn or time.sleep
        token = self.get_access_token()
        last_error: GraphMailError | None = None

        for attempt in range(_GRAPH_MAX_ATTEMPTS):
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
                last_error = GraphMailError(
                    "Timeout ao enviar e-mail via Microsoft Graph."
                )
                if attempt + 1 >= _GRAPH_MAX_ATTEMPTS or not _is_transient_graph_failure(
                    exc=exc
                ):
                    raise last_error from exc
                sleeper(_GRAPH_RETRY_BACKOFF_SECONDS[attempt])
                continue
            except httpx.HTTPError as exc:
                last_error = GraphMailError(
                    "Falha de conexão ao enviar e-mail via Microsoft Graph."
                )
                if attempt + 1 >= _GRAPH_MAX_ATTEMPTS or not _is_transient_graph_failure(
                    exc=exc
                ):
                    raise last_error from exc
                sleeper(_GRAPH_RETRY_BACKOFF_SECONDS[attempt])
                continue

            if response.status_code == 202:
                logger.info(
                    "microsoft_graph_mail_sent sender=%s recipients=%s "
                    "attachment_count=%s attempt=%s",
                    self._sender,
                    ",".join(recipients),
                    len(attachment_payload),
                    attempt + 1,
                )
                return

            if response.status_code == 401 and attempt == 0:
                token = self.get_access_token()
                sleeper(_GRAPH_RETRY_BACKOFF_SECONDS[0])
                continue

            last_error = GraphMailError(
                sanitize_graph_error(
                    f"Envio Microsoft Graph rejeitado (HTTP {response.status_code})."
                )
            )
            if attempt + 1 >= _GRAPH_MAX_ATTEMPTS or not _is_transient_graph_failure(
                status_code=response.status_code
            ):
                raise last_error
            sleeper(_GRAPH_RETRY_BACKOFF_SECONDS[attempt])

        raise last_error or GraphMailError(
            "Erro ao enviar e-mail via Microsoft Graph."
        )

    def _post(self, url: str, **kwargs: Any) -> httpx.Response:
        if self._http_client is not None:
            return self._http_client.post(url, **kwargs)
        with httpx.Client(timeout=self._timeout) as client:
            return client.post(url, **kwargs)
