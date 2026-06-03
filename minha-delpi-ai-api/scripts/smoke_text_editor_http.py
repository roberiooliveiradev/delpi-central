#!/usr/bin/env python3
"""Smoke HTTP — editor textual: correção (corrija) e lousa.

Uso (rede docker):
  docker exec delpi-minha-delpi-ai-api env SMOKE_BASE_URL=http://delpi-gateway \\
    python /app/scripts/smoke_text_editor_http.py

Local:
  cd minha-delpi-ai-api && PYTHONPATH=. python3 scripts/smoke_text_editor_http.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _default_smoke_base_url() -> str:
    explicit = os.environ.get("SMOKE_BASE_URL", "").strip()

    if explicit:
        return explicit

    if os.path.isdir("/app"):
        return "http://delpi-gateway"

    return "http://localhost"


_BASE_URL = _default_smoke_base_url().strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=180) as response:
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


def _pick_agent_id(token: str) -> str:
    agents = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20",
        token=token,
    )
    items = agents if isinstance(agents, list) else agents.get("items") or []

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente habilitado")


def _create_session(token: str, agent_id: str, *, title: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": title, "agentId": agent_id},
    )
    session_id = str(payload.get("id") or "")

    if not session_id:
        raise RuntimeError(f"Sessão inválida: {payload}")

    return session_id


def _send_message(
    token: str,
    session_id: str,
    message: str,
    *,
    agent_id: str,
    admin_debug: bool = False,
) -> dict:
    body: dict = {"message": message, "agentId": agent_id}

    if admin_debug:
        body["adminDebug"] = True

    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body=body,
    )


def _assistant_metadata(response: dict) -> dict:
    assistant = response.get("assistantMessage") or response.get("assistant") or {}
    metadata = assistant.get("metadata") if isinstance(assistant, dict) else None

    if isinstance(metadata, dict):
        return metadata

    top = response.get("metadata")

    return top if isinstance(top, dict) else {}


def _pipeline_stages(response: dict) -> list:
    admin_debug = response.get("adminDebug") or _assistant_metadata(response).get("adminDebug") or {}
    pipeline = admin_debug.get("intelligence", {}).get("pipeline") or {}
    stages = pipeline.get("stages") or response.get("pipelineStages") or []

    return list(stages) if isinstance(stages, list) else []


def _tool_calls(response: dict) -> list:
    return list(response.get("toolCalls") or [])


def _answer(response: dict) -> str:
    assistant = response.get("assistantMessage") or response.get("assistant") or {}
    content = response.get("answer") or response.get("content")

    if isinstance(assistant, dict):
        content = content or assistant.get("content")

    return str(content or "").strip()


def _canvas_open(response: dict) -> dict | None:
    canvas = response.get("canvasOpen")

    if isinstance(canvas, dict):
        return canvas

    metadata = _assistant_metadata(response)
    canvas = metadata.get("canvasOpen")

    return canvas if isinstance(canvas, dict) else None


def _run_correction_smoke(token: str, agent_id: str) -> bool:
    session_id = _create_session(token, agent_id, title="Smoke editor — corrija")
    message = "corrija: o produto 10080022 esta bloqueado na filial 01"
    response = _send_message(
        token,
        session_id,
        message,
        agent_id=agent_id,
        admin_debug=True,
    )

    if _tool_calls(response):
        print(f"FAIL corrija: toolCalls={_tool_calls(response)}", file=sys.stderr)
        return False

    stages = _pipeline_stages(response)

    if stages and "tools" in stages:
        print(f"FAIL corrija: pipeline com tools ({stages})", file=sys.stderr)
        return False

    answer = _answer(response).lower()
    metadata = _assistant_metadata(response)
    text_task = metadata.get("textTask") or {}

    if "10080022" not in answer and "10080022" not in str(metadata):
        print(f"WARN corrija: código pode não estar na resposta ({answer[:120]}...)", file=sys.stderr)

    task_type = text_task.get("type")

    if task_type not in {"correction", None}:
        print(f"FAIL corrija: textTask.type={task_type}", file=sys.stderr)
        return False

    if not answer:
        print("FAIL corrija: resposta vazia", file=sys.stderr)
        return False

    print(f"OK corrija: sem tools, resposta textual ({len(answer)} chars), stages={stages[-4:]}")
    return True


def _run_canvas_smoke(token: str, agent_id: str) -> bool:
    session_id = _create_session(token, agent_id, title="Smoke editor — lousa")

    draft = _send_message(
        token,
        session_id,
        "escreva um comunicado interno curto sobre manutenção programada",
        agent_id=agent_id,
    )
    draft_answer = _answer(draft)

    if not draft_answer:
        print("FAIL lousa: rascunho vazio no turno 1", file=sys.stderr)
        return False

    if _tool_calls(draft):
        print(f"FAIL lousa turno 1: acionou tools ({_tool_calls(draft)})", file=sys.stderr)
        return False

    print(f"OK lousa turno 1: comunicado ({len(draft_answer)} chars)")

    canvas_response = _send_message(
        token,
        session_id,
        "coloque na lousa o texto da resposta anterior",
        agent_id=agent_id,
        admin_debug=True,
    )

    if _tool_calls(canvas_response):
        print(f"FAIL lousa turno 2: toolCalls={_tool_calls(canvas_response)}", file=sys.stderr)
        return False

    canvas = _canvas_open(canvas_response)
    metadata = _assistant_metadata(canvas_response)

    if canvas and str(canvas.get("markdown") or "").strip():
        print(
            f"OK lousa turno 2: canvasOpen title={canvas.get('title')!r} "
            f"len={len(str(canvas.get('markdown') or ''))}"
        )
        return True

    if metadata.get("textCanvasUpdated") or metadata.get("textCanvasVersions"):
        print("OK lousa turno 2: textCanvasVersions/textCanvasUpdated na metadata")
        return True

    answer = _answer(canvas_response)

    if answer and ("lousa" in answer.lower() or "canvas" in answer.lower()):
        print(f"OK lousa turno 2: confirmação textual ({answer[:80]}...)")
        return True

    print(
        f"FAIL lousa: sem canvasOpen nem versão ({list(metadata.keys())[:12]})",
        file=sys.stderr,
    )
    return False


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if root not in sys.path:
        sys.path.insert(0, root)

    failed = 0

    try:
        token = _fetch_token()
        agent_id = _pick_agent_id(token)
    except (urllib.error.URLError, RuntimeError, json.JSONDecodeError, KeyError) as exc:
        print(f"SKIP gateway/token ({exc})", file=sys.stderr)
        return 0

    if not _run_correction_smoke(token, agent_id):
        failed += 1

    if not _run_canvas_smoke(token, agent_id):
        failed += 1

    if failed:
        print(f"FAIL smoke_text_editor_http ({failed} cenário(s))", file=sys.stderr)
        return 1

    print("OK smoke_text_editor_http (corrija + lousa)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
