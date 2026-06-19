#!/usr/bin/env python3
"""E2E — análise de desenho só pelo código (sem anexo na pergunta)."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://delpi-gateway").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "90263396").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: int = 600,
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
    ).encode("utf-8")
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


def main() -> int:
    failed: list[str] = []

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
        body={"title": f"E2E desenho {_PRODUCT_CODE}", "agentId": agent_id},
    )
    session_id = str(session["id"])
    message = f"Analise o desenho {_PRODUCT_CODE}"

    print(f"POST session={session_id} agent={agent_id}")
    print(f"Mensagem: {message!r} (sem anexo)")

    try:
        response = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
            token=token,
            body={"message": message, "agentId": agent_id},
            timeout=600,
        )
    except Exception as exc:
        print(f"FAIL chat POST: {exc}", file=sys.stderr)
        return 1

    answer = str(response.get("answer") or response.get("content") or "")
    metadata = response.get("metadata") if isinstance(response.get("metadata"), dict) else {}
    intelligence = metadata.get("intelligence") if isinstance(metadata.get("intelligence"), dict) else {}
    drawing = intelligence.get("drawingAnalysis") or metadata.get("drawingAnalysis")
    attachments = metadata.get("attachments") or []

    messages = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )
    items = messages if isinstance(messages, list) else messages.get("items", [])
    user_meta: dict = {}
    assistant_meta: dict = {}

    for item in reversed(items):
        role = str(item.get("role") or "")
        item_meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}

        if role == "assistant" and not assistant_meta:
            assistant_meta = item_meta

        if role == "user" and not user_meta:
            user_meta = item_meta

    print("\n=== RESUMO ===")
    print(f"Resposta ({len(answer)} chars): {answer[:500]}")
    print(f"drawingAnalysis presente: {isinstance(drawing, dict)}")

    length_errors: list[dict] = []
    missing_intermediates: list[dict] = []

    if isinstance(drawing, dict):
        print(f"  status: {drawing.get('overallStatus')}")
        print(f"  criticalErrors: {drawing.get('criticalErrors')}")
        print(f"  errors: {drawing.get('errors')}")

        for row in drawing.get("items") or []:
            if not isinstance(row, dict):
                continue

            item_label = str(row.get("item") or "")

            if "Comprimento" in item_label and row.get("status") == "critical_error":
                length_errors.append(row)

            if "Intermediário" in item_label and row.get("status") in {"error", "critical_error"}:
                missing_intermediates.append(row)

        print(f"  erros comprimento 50xx: {len(length_errors)}")

        for row in length_errors[:8]:
            print(
                f"    - {row.get('item')} | pdf={row.get('pdfEvidence')} | api={row.get('apiEvidence')}"
            )

        print(f"  intermediários ausentes: {len(missing_intermediates)}")

        for row in missing_intermediates[:8]:
            print(f"    - {row.get('item')} | api={row.get('apiEvidence')}")
    else:
        failed.append("drawingAnalysis ausente ou vazio")

    assistant_attachments = assistant_meta.get("attachments") or attachments
    user_attachments = user_meta.get("attachments") or []

    print(f"anexos assistant: {len(assistant_attachments)}")

    for attachment in assistant_attachments[:4]:
        if not isinstance(attachment, dict):
            continue

        meta = attachment.get("metadata") if isinstance(attachment.get("metadata"), dict) else {}
        print(
            f"  - {attachment.get('original_filename')} "
            f"source={meta.get('source')} product={meta.get('productCode')}"
        )

    print(f"anexos user message: {len(user_attachments)}")

    for attachment in user_attachments[:4]:
        if not isinstance(attachment, dict):
            continue

        meta = attachment.get("metadata") if isinstance(attachment.get("metadata"), dict) else {}
        print(
            f"  - {attachment.get('original_filename')} "
            f"source={meta.get('source')} product={meta.get('productCode')}"
        )

    if length_errors:
        failed.append(f"{len(length_errors)} erro(s) de comprimento 50xx")

    if missing_intermediates:
        failed.append(f"{len(missing_intermediates)} intermediário(s) ausente(s)")

    if not assistant_attachments:
        failed.append("PDF não apareceu nos anexos da resposta")

    if user_attachments:
        failed.append("PDF foi parar na mensagem do usuário (deveria só na resposta)")

    if failed:
        print("\nFALHOU:", "; ".join(failed), file=sys.stderr)
        return 1

    print(f"\nOK — teste real {_PRODUCT_CODE} passou")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
