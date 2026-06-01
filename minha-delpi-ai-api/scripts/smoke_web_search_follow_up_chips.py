#!/usr/bin/env python3
"""Smoke — atalhos «Após pesquisa web» após uma busca bem-sucedida.

Requer PYTHONPATH=/app e pesquisa web ativa.
HTTP: SMOKE_BASE_URL=http://gateway SMOKE_USER=rober SMOKE_PASSWORD=1234
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_WEB_MESSAGE = os.environ.get(
    "SMOKE_WEB_MESSAGE",
    "pesquise na web sobre Delpi Conexões Elétricas",
).strip()
_TOPIC = os.environ.get("SMOKE_WEB_TOPIC", "Delpi Conexões Elétricas").strip()

_CHIP_QUERIES: dict[str, str] = {
    "Abrir fontes": "liste os links das fontes da pesquisa web acima",
    "Resumir pesquisa": f"resuma em tópicos os resultados da pesquisa web sobre {_TOPIC}",
    "Extrair parâmetros": (
        f"extraia parâmetros técnicos das fontes da pesquisa web sobre {_TOPIC} "
        "em tabela markdown"
    ),
    "Comparar fontes": (
        f"compare as fontes da pesquisa web sobre {_TOPIC} e destaque divergências"
    ),
    "Colocar na lousa": (
        f"coloque na lousa um resumo das fontes da pesquisa web sobre {_TOPIC} com links"
    ),
    "Salvar fontes": "salve as fontes da pesquisa web no projeto",
    "Só fontes oficiais": f"pesquisa profunda na web só em sites oficiais sobre {_TOPIC}",
    "Buscar em inglês": f"busque na internet em inglês sobre {_TOPIC}",
}


def _request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=180) as response:
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
    req = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        raise RuntimeError(f"Token ausente: {payload}")

    return str(token)


def _first_agent_id(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=10", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente disponível")


def _tool_paths(response: dict) -> list[str]:
    paths: list[str] = []

    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "").strip()

        if path:
            paths.append(path.lower())

    return paths


def _tool_names(response: dict) -> list[str]:
    return [str(call.get("name") or "") for call in (response.get("toolCalls") or [])]


def _assert_chip(
    label: str,
    response: dict,
    *,
    expect_web_search: bool | None = None,
    expect_no_erp: bool = True,
    content_markers: tuple[str, ...] = (),
) -> bool:
    paths = _tool_paths(response)
    names = _tool_names(response)
    content = str(response.get("answer") or response.get("content") or "").lower()
    admin_debug = response.get("adminDebug") or {}
    stages = response.get("pipelineStages") or admin_debug.get("pipelineStages") or []

    if expect_no_erp and any("/products/search" in path for path in paths):
        print(f"FAIL [{label}]: usou /products/search ({paths})", file=sys.stderr)
        return False

    if expect_web_search is True and "web_search" not in names:
        print(f"FAIL [{label}]: esperava web_search ({names})", file=sys.stderr)
        return False

    if expect_web_search is False and "web_search" in names:
        print(f"FAIL [{label}]: não deveria web_search ({names})", file=sys.stderr)
        return False

    if label == "Colocar na lousa" and response.get("canvasOpen"):
        print(f"OK [{label}] canvasOpen presente")
        return True

    if content_markers:
        haystack = f"{content} {stages}".lower()
        if not any(marker.lower() in haystack for marker in content_markers):
            print(
                f"FAIL [{label}]: resposta sem marcadores {content_markers}",
                file=sys.stderr,
            )
            return False

    print(f"OK [{label}] names={names or '—'} stages={stages[-3:] if stages else '—'}")
    return True


def main() -> int:
    from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService

    failed = 0

    for label, query in _CHIP_QUERIES.items():
        if label in {"Só fontes oficiais", "Buscar em inglês"}:
            if not ChatWebSearchIntentService.matches(query):
                print(f"FAIL unit [{label}]: não reconhece web ({query})", file=sys.stderr)
                failed += 1
            else:
                print(f"OK unit [{label}]: gatilho web")

    try:
        token = _fetch_token()
    except Exception as exc:
        print(f"SKIP API: {exc}", file=sys.stderr)
        return 1 if failed else 0

    agent_id = _first_agent_id(token)
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke web follow-up chips", "agentId": agent_id},
    )
    session_id = session["id"]

    initial = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": _WEB_MESSAGE, "agentId": agent_id},
    )

    if "web_search" not in _tool_names(initial):
        print(
            f"FAIL API: pesquisa inicial sem web_search ({_tool_names(initial)})",
            file=sys.stderr,
        )
        return 1

    print("OK API: pesquisa web inicial")

    expectations: dict[str, dict] = {
        "Abrir fontes": {
            "expect_web_search": False,
            "content_markers": ("http",),
        },
        "Resumir pesquisa": {
            "expect_web_search": False,
            "content_markers": ("resumo",),
        },
        "Extrair parâmetros": {
            "expect_web_search": False,
            "content_markers": ("|",),
        },
        "Comparar fontes": {
            "expect_web_search": False,
            "content_markers": ("compara",),
        },
        "Colocar na lousa": {
            "expect_web_search": False,
            "content_markers": (),
        },
        "Salvar fontes": {
            "expect_web_search": False,
            "content_markers": ("fonte", "projeto", "salv"),
        },
        "Só fontes oficiais": {"expect_web_search": True},
        "Buscar em inglês": {"expect_web_search": True},
    }

    for label, query in _CHIP_QUERIES.items():
        response = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
            token=token,
            body={"message": query, "agentId": agent_id},
        )
        opts = expectations.get(label, {})

        if not _assert_chip(label, response, **opts):
            failed += 1

    if failed:
        print(f"\n{failed} atalho(s) com falha.", file=sys.stderr)
        return 1

    print("\nSmoke atalhos pós-pesquisa web: todos OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
