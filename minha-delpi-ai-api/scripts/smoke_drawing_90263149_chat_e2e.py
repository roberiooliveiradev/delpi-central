#!/usr/bin/env python3
"""Smoke E2E — chat real com PDF 90263149 (caso âncora BOM colunar)."""

from __future__ import annotations

import json
import os
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "90263149").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_ADMIN_DEBUG = os.environ.get("SMOKE_ADMIN_DEBUG", "1").lower() in {"1", "true", "yes"}


def _pdf_path() -> Path:
    candidates = [
        Path(__file__).resolve().parents[1] / "desenhos" / f"{_PRODUCT_CODE}.pdf",
        Path(f"/app/desenhos/{_PRODUCT_CODE}.pdf"),
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(f"PDF {_PRODUCT_CODE}.pdf não encontrado")


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: int = 300,
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

    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        raise RuntimeError(f"Token ausente: {payload}")

    return str(token)


def _multipart_upload(url: str, *, token: str, filename: str, content: bytes) -> dict:
    boundary = f"----Smoke90263149{uuid.uuid4().hex}"
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

    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=30", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        agent_key = str(agent.get("agentKey") or agent.get("key") or "").strip().lower()

        if "drawing" in agent_key or agent_key == "minha-delpi-chat":
            if agent.get("enabled"):
                return str(agent["id"])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente disponível")


def _assistant_metadata(session_id: str, *, token: str) -> tuple[dict, dict]:
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
            merged.setdefault("drawingAnalysis", intelligence.get("drawingAnalysis"))
            return merged, metadata.get("adminDebug") if isinstance(metadata.get("adminDebug"), dict) else {}

        return metadata, metadata.get("adminDebug") if isinstance(metadata.get("adminDebug"), dict) else {}

    return {}, {}


def main() -> int:
    pdf_path = _pdf_path()
    print(f"PDF: {pdf_path}")
    print(f"Gateway: {_BASE_URL}{_CHAT_PREFIX}\n")

    try:
        token = _fetch_token()
        print("OK login")
    except Exception as exc:
        print(f"FAIL login: {exc}", file=sys.stderr)
        return 1

    agent_id = _first_agent(token)
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": f"Smoke {_PRODUCT_CODE} BOM colunar", "agentId": agent_id},
    )
    session_id = str(session["id"])
    print(f"OK session {session_id}")

    attachment = _multipart_upload(
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/attachments",
        token=token,
        filename=pdf_path.name,
        content=pdf_path.read_bytes(),
    )
    attachment_id = str(attachment["id"])
    print(f"OK attachment {attachment_id}")

    message = (
        f"Analise o desenho técnico {_PRODUCT_CODE} anexado e gere o relatório "
        "de conformidade DELPI comparando PDF × SG1010."
    )
    body = {
        "message": message,
        "agentId": agent_id,
        "attachmentIds": [attachment_id],
    }

    if _ADMIN_DEBUG:
        body["adminDebug"] = True

    print("Enviando mensagem (pode levar alguns minutos)...")

    try:
        response = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
            token=token,
            body=body,
            timeout=600,
        )
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        print(f"FAIL HTTP {exc.code}: {raw[:800]}", file=sys.stderr)
        return 1

    metadata, persisted_admin = _assistant_metadata(session_id, token=token)
    admin_debug = response.get("adminDebug") if isinstance(response.get("adminDebug"), dict) else persisted_admin
    drawing = metadata.get("drawingAnalysis") if isinstance(metadata.get("drawingAnalysis"), dict) else {}
    answer = str(response.get("answer") or response.get("content") or "")

    print("\n--- Resultado ---")
    print(f"status: {drawing.get('status')}")
    print(f"criticalErrors: {drawing.get('criticalErrors')}")
    print(f"visionRefinement: {json.dumps(drawing.get('visionRefinement'), ensure_ascii=False)}")
    print(f"answer preview: {answer[:400].replace(chr(10), ' ')}")

    critical = [
        item
        for item in drawing.get("items") or []
        if isinstance(item, dict) and item.get("status") == "critical_error"
    ]
    bom_qty_critical_keys = {"bom_quantity_mismatch"}
    qty_critical = [
        item
        for item in critical
        if item.get("templateKey") in bom_qty_critical_keys
    ]

    if qty_critical:
        print("\nCríticos BOM QTD:")
        for item in qty_critical[:6]:
            print(f"  - {item.get('item')} | {item.get('pdfEvidence')} vs {item.get('apiEvidence')}")

    trace = admin_debug.get("drawingAnalysisTrace") if isinstance(admin_debug, dict) else None

    if isinstance(trace, dict):
        print("\nFases adminDebug:")
        for phase in trace.get("phases") or []:
            if isinstance(phase, dict):
                print(f"  - {phase.get('id')}: {phase.get('status')} — {phase.get('detail')}")

    failed = False

    if qty_critical:
        print("FAIL: bom_quantity_mismatch crítico (falso positivo QTD)", file=sys.stderr)
        failed = True

    other_critical = [
        item for item in critical if item.get("templateKey") not in bom_qty_critical_keys
    ]
    if other_critical:
        print(
            f"\nWARN: {len(other_critical)} crítico(s) não-QTD "
            f"(ex.: bom_extra) — fora do gate 15.8 assertividade QTD"
        )
        for item in other_critical[:4]:
            print(f"  - {item.get('templateKey')}: {item.get('item')}")

    if not drawing.get("items"):
        print("FAIL: drawingAnalysis vazio", file=sys.stderr)
        failed = True

    if failed:
        return 1

    print("\nOK chat E2E 90263149 — 0 críticos BOM QTD (gate 15.8)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
