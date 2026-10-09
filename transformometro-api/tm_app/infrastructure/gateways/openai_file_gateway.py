"""Platform-authorized file fetch for ChatGPT ``openai/fileParams``.

When a user uploads a file in ChatGPT, the host may bind it to a tool
argument declared in ``_meta["openai/fileParams"]`` — the argument carries
``{download_url, file_id, mime_type?, file_name?}`` where ``download_url``
is a short-lived URL pre-authorized by the host for this plugin.

This adapter is the only place that resolves such URLs into bytes. It is
deliberately narrow:

- HTTPS only;
- host allowlist (``OPENAI_FILE_DOWNLOAD_HOSTS``, default
  ``files.oaiusercontent.com``) — a model-supplied URL to any other host
  fails closed (SSRF guard);
- no redirects;
- bounded byte size (default 20 MiB, aligned with the Helpdesk BFF upload
  cap) enforced while streaming;
- short timeout.

It never authenticates to the URL (the host pre-authorized it), never
follows redirects, never reads the local filesystem, and never logs file
content.
"""

from __future__ import annotations

import logging
import os
from urllib.parse import unquote, urlparse

import httpx

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.helpdesk.helpdesk_write_port import (
    HelpdeskFileSourcePort,
)

logger = logging.getLogger(__name__)

_DEFAULT_HOSTS = "files.oaiusercontent.com"
MAX_FILE_BYTES = int(os.getenv("OPENAI_FILE_MAX_BYTES", str(20 * 1024 * 1024)))
_TIMEOUT_SECONDS = 20.0


def _allowed_hosts() -> tuple[str, ...]:
    raw = os.getenv("OPENAI_FILE_DOWNLOAD_HOSTS", _DEFAULT_HOSTS)
    return tuple(
        host.strip().lower() for host in raw.split(",") if host.strip()
    )


def _host_allowed(hostname: str) -> bool:
    host = hostname.lower()
    return any(
        host == allowed or host.endswith(f".{allowed}")
        for allowed in _allowed_hosts()
    )


def _filename_from_disposition(header: str) -> str:
    for part in str(header or "").split(";"):
        part = part.strip()
        if part.lower().startswith("filename*="):
            value = part.split("=", 1)[1].strip().strip('"')
            if "''" in value:
                _, value = value.split("''", 1)
            return unquote(value)
    for part in str(header or "").split(";"):
        part = part.strip()
        if part.lower().startswith("filename="):
            return part.split("=", 1)[1].strip().strip('"')
    return ""


def _sanitize_filename(value: str) -> str:
    name = str(value or "").replace("\\", "/").split("/")[-1]
    cleaned = "".join(
        char for char in name if char not in "\r\n\"" and char.isprintable()
    ).strip().lstrip(".")
    return (cleaned or "arquivo")[:180]


def _validation(message: str, code: str) -> GptActionsError:
    return GptActionsError(
        message, 400, {"error_kind": "validation", "error_code": code}
    )


class OpenAIFileGateway(HelpdeskFileSourcePort):
    """Fetches bytes from a ChatGPT fileParam ``download_url``."""

    def fetch(self, download_url: str) -> dict[str, Any]:
        url = str(download_url or "").strip()
        if not url:
            raise _validation(
                "download_url ausente na referência de arquivo.",
                "FILE_URL_REQUIRED",
            )
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise _validation(
                "download_url deve ser HTTPS.",
                "FILE_URL_NOT_ALLOWED",
            )
        if not parsed.hostname or not _host_allowed(parsed.hostname):
            raise _validation(
                "download_url fora do allowlist de arquivos da plataforma.",
                "FILE_URL_NOT_ALLOWED",
            )
        timeout = httpx.Timeout(_TIMEOUT_SECONDS, connect=10.0)
        try:
            # No redirects: a redirect could escape the allowlist; the host
            # URL is already the final signed location.
            with httpx.Client(
                timeout=timeout, follow_redirects=False
            ) as client:
                with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        raise GptActionsError(
                            "Arquivo da plataforma indisponível.",
                            502,
                            {
                                "error_kind": "upstream_unavailable",
                                "status": response.status_code,
                            },
                        )
                    chunks: list[bytes] = []
                    total = 0
                    for chunk in response.iter_bytes():
                        total += len(chunk)
                        if total > MAX_FILE_BYTES:
                            raise _validation(
                                "Arquivo excede o limite de tamanho.",
                                "FILE_TOO_LARGE",
                            )
                        chunks.append(chunk)
        except GptActionsError:
            raise
        except httpx.RequestError as exc:
            logger.warning(
                "openai_file_fetch_failed host=%s err=%s",
                parsed.hostname,
                exc,
            )
            raise GptActionsError(
                "Arquivo da plataforma indisponível.",
                502,
                {"error_kind": "upstream_unavailable"},
            ) from exc
        content = b"".join(chunks)
        if not content:
            raise _validation("Arquivo vazio.", "FILE_EMPTY")
        mime = (
            response.headers.get("content-type", "")
            .split(";")[0]
            .strip()
            or "application/octet-stream"
        )
        filename = _filename_from_disposition(
            response.headers.get("content-disposition", "")
        )
        return {
            "content": content,
            "mime": mime,
            "filename": filename,
        }


def sanitize_upload_filename(value: str) -> str:
    """Public filename normalizer shared with the upload capability."""
    return _sanitize_filename(value)
