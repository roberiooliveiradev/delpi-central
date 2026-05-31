#!/usr/bin/env python3
"""Smoke — upload CSV, indexação e welcome automático (Playbook 07).

Uso:
  PYTHONPATH=. .venv/bin/python scripts/smoke_attachment_index_welcome.py
  SMOKE_BASE_URL=http://localhost SMOKE_USER=rober SMOKE_PASSWORD=1234 ...
"""

from __future__ import annotations

import json
import os
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request

from app.application.services.chat_attachment_preview_service import (
    ChatAttachmentPreviewService,
)
from app.application.services.chat_attachment_welcome_service import (
    ChatAttachmentWelcomeService,
)

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_CSV_BODY = (
    "Produto;Descricao;Quantidade\n"
    "10080001;Parafuso;120\n"
    "10080002;Porca;80\n"
).encode("utf-8")


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc


def _multipart_upload(
    url: str,
    *,
    token: str,
    fields: dict[str, str],
    file_field: str,
    filename: str,
    content: bytes,
    content_type: str,
) -> dict:
    boundary = f"----SmokeBoundary{uuid.uuid4().hex}"
    body = bytearray()

    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        body.extend(f"{value}\r\n".encode())

    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        (
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{filename}"\r\n'
        ).encode()
    )
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
    body.extend(content)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    request = urllib.request.Request(
        url,
        data=bytes(body),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST {url} -> HTTP {exc.code}: {detail}") from exc


def _fetch_token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    return str(payload["access_token"])


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents", token=token)

    if not agents:
        raise RuntimeError("Nenhum agente disponível para smoke")

    return str(agents[0]["id"])


def _run_unit_checks() -> int:
    failed = 0

    preview = ChatAttachmentPreviewService.build_from_extracted(
        {
            "supported": True,
            "content": "Col1 | Col2 | Col3\n1 | 2 | 3",
            "metadata": {"extractor": "csv", "extension": ".csv"},
        },
        filename="planilha.csv",
    )

    if preview.get("columns") != ["Col1", "Col2", "Col3"]:
        print(f"FAIL unit: columns={preview}", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: preview de colunas CSV")

    if not ChatAttachmentWelcomeService.should_welcome("segue anexo", attachment_ids=["x"]):
        print("FAIL unit: should_welcome handoff", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: should_welcome handoff")

    return failed


def main() -> int:
    failed = _run_unit_checks()

    try:
        token = _fetch_token()
        print("OK login Keycloak")
    except Exception as exc:
        print(f"SKIP API: login falhou: {exc}", file=sys.stderr)
        return 1 if failed else 0

    try:
        agent_id = _first_agent(token)
        session = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
            token=token,
            body={"title": "Smoke anexo 07", "agentId": agent_id},
        )
        session_id = str(session["id"])

        attachment = _multipart_upload(
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/attachments",
            token=token,
            fields={},
            file_field="file",
            filename="smoke-vendas.csv",
            content=_CSV_BODY,
            content_type="text/csv",
        )

        attachment_id = str(attachment["id"])
        status = str(attachment.get("status") or "")
        meta = attachment.get("metadata") or {}

        preview = meta.get("preview") if isinstance(meta.get("preview"), dict) else {}

        if status != "indexed" and not meta.get("indexed"):
            print(
                f"WARN API: anexo status={status} metadata={meta}",
                file=sys.stderr,
            )
        else:
            print(f"OK API: upload indexado status={status}")

        reading_status = meta.get("readingStatus")

        if preview.get("columns"):
            print(f"OK API: preview no upload cols={preview['columns'][:3]}")
        elif reading_status == "Indexado":
            print("OK API: preview ausente mas readingStatus=Indexado")
        else:
            print(
                "WARN API: metadata.preview ausente no upload (rebuild/restart da API?)",
                file=sys.stderr,
            )

        if reading_status:
            print(f"OK API: readingStatus={reading_status}")
        else:
            print("WARN API: readingStatus ausente no upload", file=sys.stderr)

        response = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
            token=token,
            body={
                "message": "segue anexo",
                "agentId": agent_id,
                "attachmentIds": [attachment_id],
            },
        )
    except Exception as exc:
        print(f"SKIP API: {exc}", file=sys.stderr)
        return 1 if failed else 0

    answer = str(response.get("content") or response.get("answer") or "")

    messages = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )
    assistant_meta: dict = {}

    for message in reversed(messages if isinstance(messages, list) else []):
        if str(message.get("role") or "") == "assistant":
            assistant_meta = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
            break

    metadata = assistant_meta

    if "Arquivo recebido" not in answer:
        print(f"FAIL API: welcome ausente -> {answer[:200]}", file=sys.stderr)
        failed += 1
    else:
        print("OK API: resposta de welcome")

    suggestions = metadata.get("attachmentFollowUpSuggestions") or []

    if not suggestions:
        print("FAIL API: attachmentFollowUpSuggestions ausente", file=sys.stderr)
        failed += 1
    else:
        print(f"OK API: {len(suggestions)} chips de anexo")

    summaries = metadata.get("attachmentSummaries") or []

    if summaries and summaries[0].get("preview", {}).get("columns"):
        print("OK API: attachmentSummaries com colunas")
    elif "Colunas:" in answer:
        print("OK API: colunas na resposta de welcome")
    else:
        print(
            "WARN API: preview de colunas não visível (indexação pode ter falhado)",
            file=sys.stderr,
        )

    admin_debug = response.get("adminDebug") or {}
    intent_route = admin_debug.get("intentRoute") or {}

    if intent_route.get("intent") == "attachment_task":
        print("OK API: intent attachment_task")
    else:
        print(f"WARN API: intentRoute={intent_route}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
