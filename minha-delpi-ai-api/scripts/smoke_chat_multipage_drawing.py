#!/usr/bin/env python3
"""Smoke E2E — desenho multipágina pelo chat (upload PDF + análise DELPI)."""

from __future__ import annotations

import json
import os
import sys
import uuid
import urllib.parse
import urllib.request
from pathlib import Path

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://delpi-gateway").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "90263622").strip()
_PDF_PATH = Path(
    os.environ.get(
        "SMOKE_PDF_PATH",
        str(Path(__file__).resolve().parents[1] / "desenhos" / f"{_PRODUCT_CODE}.pdf"),
    )
)
_EXPECTED_PAGES = int(os.environ.get("SMOKE_EXPECTED_PAGE_COUNT", "10"))


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: int = 900,
) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _fetch_token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode()
    request = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        raise RuntimeError(f"Token ausente: {payload}")

    return str(token)


def _multipart_upload(
    url: str,
    *,
    token: str,
    filename: str,
    content: bytes,
) -> dict:
    boundary = f"----SmokeBoundary{uuid.uuid4().hex}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        (
            f'Content-Disposition: form-data; name="file"; '
            f'filename="{filename}"\r\n'
        ).encode()
    )
    body.extend(b"Content-Type: application/pdf\r\n\r\n")
    body.extend(content)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=300) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=30", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        agent_key = str(agent.get("agentKey") or agent.get("key") or "").strip().lower()

        if agent_key == "minha-delpi-chat" and agent.get("enabled"):
            return str(agent["id"])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente disponível")


def _assistant_metadata(session_id: str, *, token: str) -> dict:
    messages = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )
    items = messages if isinstance(messages, list) else messages.get("items", [])

    for item in reversed(items):
        if str(item.get("role") or "") != "assistant":
            continue

        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        intelligence = metadata.get("intelligence")

        if isinstance(intelligence, dict):
            merged = dict(metadata)
            for key in (
                "drawingAnalysis",
                "drawingAnalysisMode",
                "drawingPdfExtractSummary",
                "documentVision",
                "drawingAnalysisExport",
            ):
                if intelligence.get(key) is not None:
                    merged[key] = intelligence.get(key)

            return merged

        return metadata

    return {}


def main() -> int:
    errors: list[str] = []

    if not _PDF_PATH.is_file():
        print(f"FAIL PDF ausente: {_PDF_PATH}", file=sys.stderr)
        return 1

    print(f"PDF: {_PDF_PATH} ({_PDF_PATH.stat().st_size // 1024} KB)")
    print(f"Produto: {_PRODUCT_CODE} · páginas esperadas: {_EXPECTED_PAGES}")

    token = _fetch_token()
    print("OK login")

    agent_id = _first_agent(token)
    print(f"Agent: {agent_id}")

    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": f"Smoke multipágina {_PRODUCT_CODE}", "agentId": agent_id},
    )
    session_id = str(session["id"])
    print(f"Session: {session_id}")

    attachment = _multipart_upload(
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/attachments",
        token=token,
        filename=_PDF_PATH.name,
        content=_PDF_PATH.read_bytes(),
    )
    attachment_id = str(attachment["id"])
    print(f"Attachment: {attachment_id}")

    message = (
        f"Analise o desenho técnico {_PRODUCT_CODE} "
        "e gere o relatório de conformidade DELPI"
    )

    print("Enviando mensagem (OCR multipágina pode levar vários minutos)…")
    response = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": message,
            "agentId": agent_id,
            "attachmentIds": [attachment_id],
        },
    )

    answer = str(response.get("answer") or response.get("content") or "")
    print(f"Resposta ({len(answer)} chars): {answer[:280]}…")

    metadata = _assistant_metadata(session_id, token=token)
    drawing = metadata.get("drawingAnalysis") if isinstance(metadata.get("drawingAnalysis"), dict) else {}
    summary = (
        metadata.get("drawingPdfExtractSummary")
        if isinstance(metadata.get("drawingPdfExtractSummary"), dict)
        else {}
    )
    docvis = metadata.get("documentVision") if isinstance(metadata.get("documentVision"), dict) else {}
    multipage = drawing.get("multipageCoverage") if isinstance(drawing.get("multipageCoverage"), dict) else {}

    page_count = int(
        summary.get("pageCount")
        or multipage.get("pageCount")
        or docvis.get("pageCount")
        or 0
    )

    print("\n=== RESULTADO MULTIPÁGINA (chat) ===")
    print("drawingAnalysisMode:", metadata.get("drawingAnalysisMode"))
    print("status:", drawing.get("status"))
    print("pageCount:", page_count)
    print("legible:", summary.get("legible"))
    print("productCode:", summary.get("productCode"))
    print("multipageCoverage:", json.dumps(multipage, ensure_ascii=False))
    print("criticalErrors:", drawing.get("criticalErrors"))
    print("checklist items:", len(drawing.get("items") or []))
    print(f"URL: http://localhost/apps/minha-delpi-chat/conversas/{session_id}")

    if not metadata.get("drawingAnalysisMode"):
        errors.append("drawingAnalysisMode ausente")

    if not drawing.get("items"):
        errors.append("drawingAnalysis.items vazio")

    if page_count < _EXPECTED_PAGES:
        errors.append(f"pageCount={page_count} (esperado >= {_EXPECTED_PAGES})")

    if not multipage.get("applicable") and _EXPECTED_PAGES > 1:
        errors.append("multipageCoverage.applicable=false")

    if errors:
        for err in errors:
            print(f"FAIL {err}", file=sys.stderr)
        return 1

    print("\nOK chat multipágina — análise DELPI concluída.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
