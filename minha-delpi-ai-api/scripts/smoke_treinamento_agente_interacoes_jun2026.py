#!/usr/bin/env python3
"""Smoke E2E — roteiro treinamento-agente-interacoes-jun2026.md (6 interações).

Simula usuário real via REST: sessões multi-turno, follow-up anafórico e fontes de projeto.

Uso:
  cd minha-delpi-ai-api
  SMOKE_BASE_URL=http://localhost PYTHONPATH=. python scripts/smoke_treinamento_agente_interacoes_jun2026.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_STOCK = os.environ.get("SMOKE_STOCK_CODE", "10080022").strip()
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "90269002").strip()
_MP = os.environ.get("SMOKE_MP_CODE", "10080001").strip()
_PA = os.environ.get("SMOKE_PA_CODE", "90261255").strip()
_MAX_LATENCY_S = float(os.environ.get("SMOKE_MAX_LATENCY_SECONDS", "60"))
_PAUSE_S = float(os.environ.get("SMOKE_PAUSE_SECONDS", "1"))

_CAPABILITY_MARKERS = (
    "posso executar",
    "consigo executar",
    "se eu consigo",
    "capacidades do assistente",
    "o que você consegue",
    "o que voce consegue",
)


def _request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=300) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _token() -> str:
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
        raise RuntimeError("Token ausente")

    return str(token)


def _agent_id(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        key = str(agent.get("agentKey") or agent.get("key") or "").strip().lower()
        if key == "minha-delpi-chat" and agent.get("enabled"):
            return str(agent["id"])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    return str(items[0]["id"])


def _session(
    token: str,
    agent_id: str,
    title: str,
    *,
    project_id: str | None = None,
) -> str:
    body: dict = {"title": title, "agentId": agent_id}

    if project_id:
        body["projectId"] = project_id

    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body=body,
    )

    return str(payload["id"])


def _send(token: str, session_id: str, agent_id: str, message: str) -> tuple[dict, float]:
    started = time.monotonic()
    response = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
    )

    return response, time.monotonic() - started


def _create_project(token: str, name: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/projects",
        token=token,
        body={"name": name, "description": "Smoke treinamento jun/2026"},
    )

    return str(payload["id"])


def _create_project_text_source(token: str, project_id: str, *, title: str, content: str) -> None:
    _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/projects/{project_id}/sources",
        token=token,
        body={"title": title, "content": content},
    )


def _delete_project(token: str, project_id: str) -> None:
    req = urllib.request.Request(
        f"{_BASE_URL}{_CHAT_PREFIX}/projects/{project_id}",
        headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
        method="DELETE",
    )

    try:
        with urllib.request.urlopen(req, timeout=30):
            pass
    except urllib.error.HTTPError:
        pass


def _content(response: dict) -> str:
    return str(response.get("content") or response.get("answer") or "")


def _stages(response: dict) -> list[str]:
    admin = response.get("adminDebug") or {}
    intelligence = admin.get("intelligence") or {}
    pipeline = intelligence.get("pipeline") or {}

    return list(pipeline.get("stages") or [])


def _skip_rag(response: dict) -> bool | None:
    admin = response.get("adminDebug") or {}
    intelligence = admin.get("intelligence") or {}
    pipeline = intelligence.get("pipeline") or {}

    if "skipRag" in pipeline:
        return bool(pipeline.get("skipRag"))

    return None


def _action_path(response: dict) -> str:
    for call in response.get("toolCalls") or []:
        if str(call.get("name") or "") != "execute_external_action":
            continue

        meta = call.get("metadata") or {}

        if meta.get("ok"):
            return str(meta.get("path") or "")

    for call in response.get("toolCalls") or []:
        if str(call.get("name") or "") != "execute_external_action":
            continue

        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "")

        if path:
            return path

    return ""


def _external_action_call(response: dict) -> dict:
    for call in response.get("toolCalls") or []:
        if str(call.get("name") or "") == "execute_external_action":
            return call

    return {}


def _tool_parameters(response: dict) -> dict:
    call = _external_action_call(response)
    args = call.get("arguments") or {}
    meta = call.get("metadata") or {}

    return dict(args.get("parameters") or meta.get("parameters") or {})


def _presentation_selected(response: dict) -> str:
    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        decision = meta.get("presentationDecision") or {}

        if decision.get("selected"):
            return str(decision["selected"])

    metadata = response.get("metadata") or {}
    decision = metadata.get("presentationDecision") or {}

    return str(decision.get("selected") or "")


def _is_capability_answer(response: dict) -> bool:
    content = _content(response).lower()
    stages = _stages(response)

    if "capability" in " ".join(stages).lower():
        return True

    return any(marker in content for marker in _CAPABILITY_MARKERS)


def _llm_improvised(response: dict) -> bool:
    stages = _stages(response)
    content = _content(response).lower()

    if any(stage in {"llm_synthesis", "agentic_loop", "llm_general"} for stage in stages):
        return True

    if "operational_parameter" in stages:
        return False

    if _action_path(response):
        return False

    markers = (
        "nao tenho acesso",
        "não tenho acesso",
        "infelizmente nao consigo",
        "infelizmente não consigo",
    )

    return any(marker in content for marker in markers)


def _check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"OK  {label}" + (f" — {detail}" if detail else ""))
        return

    print(f"FAIL {label}" + (f" — {detail}" if detail else ""), file=sys.stderr)
    raise AssertionError(label)


def _assert_operational(
    label: str,
    response: dict,
    elapsed: float,
    *,
    path_fragment: str,
    product_code: str | None = None,
) -> None:
    path = _action_path(response)
    stages = _stages(response)

    _check(label, elapsed <= _MAX_LATENCY_S, f"latência {elapsed:.1f}s")
    _check(label, not _llm_improvised(response), f"improvisação stages={stages[-4:]}")
    _check(label, path_fragment in path, f"path={path or '?'} stages={stages[-3:]}")

    if product_code:
        _check(label, product_code in path, f"path={path}")


def main() -> int:
    failed = 0
    token = _token()
    agent_id = _agent_id(token)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    print(f"Agente: {agent_id} · PA/produto: {_PRODUCT} · estoque: {_STOCK}")

    # Interação 1 — estoque + refinamento visual
    try:
        time.sleep(_PAUSE_S)
        session_id = _session(token, agent_id, "I1 estoque + gráfico")
        first, elapsed = _send(token, session_id, agent_id, f"estoque do produto {_STOCK}")
        _assert_operational("I1.1 estoque", first, elapsed, path_fragment="/stock")

        follow, elapsed = _send(token, session_id, agent_id, "mostre em gráfico")
        follow_path = _action_path(follow)
        selected = _presentation_selected(follow)
        stages = _stages(follow)

        _check(
            "I1.2 refinamento gráfico",
            "/stock" not in follow_path or selected in {"chart", "line_chart", "bar_chart", "graph"},
            f"path={follow_path or '(sem nova rota)'} selected={selected or '?'} stages={stages[-4:]}",
        )
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL I1 — {exc}", file=sys.stderr)
        failed += 1

    # Interação 2 — status fabril + exclusividade «desse produto»
    try:
        time.sleep(_PAUSE_S)
        session_id = _session(token, agent_id, "I2 fabril + exclusividade anafórica")
        first, elapsed = _send(
            token,
            session_id,
            agent_id,
            f"status fabril do produto {_PRODUCT} hoje",
        )
        _assert_operational(
            "I2.1 status fabril",
            first,
            elapsed,
            path_fragment="/factory-status",
            product_code=_PRODUCT,
        )

        follow, elapsed = _send(
            token,
            session_id,
            agent_id,
            "quais matérias-primas exclusivas existem na estrutura desse produto?",
        )
        path = _action_path(follow)
        stages = _stages(follow)

        _check("I2.2 exclusividade desse produto", not _is_capability_answer(follow), f"stages={stages[-4:]}")
        _assert_operational(
            "I2.2 exclusividade desse produto",
            follow,
            elapsed,
            path_fragment="/structure/exclusivity",
            product_code=_PRODUCT,
        )
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL I2 — {exc}", file=sys.stderr)
        failed += 1

    # Interação 3 — preço MP vs preço venda
    try:
        time.sleep(_PAUSE_S)
        session_id = _session(token, agent_id, "I3 MP vs pricing")
        first, elapsed = _send(token, session_id, agent_id, f"análise de preço da matéria-prima {_MP}")
        _assert_operational(
            "I3.1 análise MP",
            first,
            elapsed,
            path_fragment="/raw-material-price-intelligence",
        )

        follow, elapsed = _send(token, session_id, agent_id, f"qual o preço de venda do produto {_MP}?")
        _assert_operational("I3.2 preço venda", follow, elapsed, path_fragment="/pricing")
        _check(
            "I3.2 preço venda",
            "/raw-material-price-intelligence" not in _action_path(follow),
            f"path={_action_path(follow)}",
        )
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL I3 — {exc}", file=sys.stderr)
        failed += 1

    # Interação 4 — simulador + reajuste 10%
    try:
        time.sleep(_PAUSE_S)
        session_id = _session(token, agent_id, "I4 simulador PA")
        first, elapsed = _send(
            token,
            session_id,
            agent_id,
            f"quais materiais mais impactam o custo do PA {_PA}?",
        )
        _assert_operational(
            "I4.1 simulador",
            first,
            elapsed,
            path_fragment="/cost-impact-simulation",
        )

        follow, elapsed = _send(
            token,
            session_id,
            agent_id,
            "simule aumento de 10% nos materiais desse produto",
        )
        path = _action_path(follow)
        params = _tool_parameters(follow)
        adjustment = params.get("adjustment_percent")

        _assert_operational(
            "I4.2 reajuste 10%",
            follow,
            elapsed,
            path_fragment="/cost-impact-simulation",
        )
        _check(
            "I4.2 reajuste 10%",
            adjustment in {10, 10.0, "10"} or "10" in str(adjustment or ""),
            f"adjustment_percent={adjustment!r} params={params}",
        )
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL I4 — {exc}", file=sys.stderr)
        failed += 1

    # Interação 5 — produção → «e a expedição?»
    try:
        time.sleep(_PAUSE_S)
        session_id = _session(token, agent_id, "I5 produção → expedição")
        first, elapsed = _send(
            token,
            session_id,
            agent_id,
            f"situação de produção do {_PRODUCT} hoje",
        )
        _assert_operational(
            "I5.1 produção",
            first,
            elapsed,
            path_fragment="/production-status",
            product_code=_PRODUCT,
        )

        follow, elapsed = _send(token, session_id, agent_id, "e a expedição?")
        path = _action_path(follow)
        params = _tool_parameters(follow)
        meta = (_external_action_call(follow).get("metadata") or {})
        error_text = str(meta.get("error") or "")

        _check("I5.2 e a expedição?", "limit" not in error_text.lower(), f"error={error_text[:120]!r}")
        _assert_operational(
            "I5.2 e a expedição?",
            follow,
            elapsed,
            path_fragment="/shipping-status",
            product_code=_PRODUCT,
        )
        _check(
            "I5.2 e a expedição?",
            params.get("code") in {None, _PRODUCT} or _PRODUCT in path,
            f"params={params}",
        )
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL I5 — {exc}", file=sys.stderr)
        failed += 1

    # Interação 6 — fontes do projeto
    project_id: str | None = None

    try:
        time.sleep(_PAUSE_S)
        project_id = _create_project(token, f"Smoke treinamento {stamp}")
        _create_project_text_source(
            token,
            project_id,
            title="Manual homologação DELPI",
            content=(
                "Este documento descreve o processo de homologação do chat DELPI. "
                "O primeiro arquivo contém instruções sobre estoque, produção e expedição. "
                "A equipe deve validar follow-ups operacionais e fontes de projeto."
            ),
        )
        _create_project_text_source(
            token,
            project_id,
            title="Segundo arquivo auxiliar",
            content="Conteúdo secundário para testes de slot ordinal.",
        )

        session_id = _session(token, agent_id, "I6 fontes projeto", project_id=project_id)
        first, elapsed = _send(token, session_id, agent_id, "o que tem nas suas fontes?")
        stages = _stages(first)
        content = _content(first)
        skip_rag = _skip_rag(first)

        _check("I6.1 inventário fontes", elapsed <= _MAX_LATENCY_S, f"latência {elapsed:.1f}s")
        _check("I6.1 inventário fontes", not _llm_improvised(first), f"stages={stages[-4:]}")
        _check(
            "I6.1 inventário fontes",
            "project_sources_inventory" in stages or "Manual homologação" in content,
            f"stages={stages[-4:]} preview={content[:100]!r}",
        )
        _check(
            "I6.1 inventário fontes",
            skip_rag is not False,
            f"skipRag={skip_rag}",
        )
        _check(
            "I6.1 inventário fontes",
            "não tenho acesso" not in content.lower() and "nao tenho acesso" not in content.lower(),
            f"answer={content[:120]!r}",
        )

        follow, elapsed = _send(token, session_id, agent_id, "resuma o conteúdo do primeiro arquivo")
        follow_stages = _stages(follow)
        follow_content = _content(follow)

        _check("I6.2 resumo primeiro arquivo", elapsed <= _MAX_LATENCY_S, f"latência {elapsed:.1f}s")
        _check(
            "I6.2 resumo primeiro arquivo",
            "text_task" not in follow_stages and "operational_query" not in follow_stages[-1:],
            f"stages={follow_stages[-5:]}",
        )
        _check(
            "I6.2 resumo primeiro arquivo",
            "project_sources_content" in follow_stages
            or "homologação" in follow_content.lower()
            or "homologacao" in follow_content.lower()
            or "estoque" in follow_content.lower()
            or "produção" in follow_content.lower()
            or "producao" in follow_content.lower(),
            f"stages={follow_stages[-5:]} preview={follow_content[:120]!r}",
        )
        _check(
            "I6.2 resumo primeiro arquivo",
            "não tenho acesso" not in follow_content.lower()
            and "nao tenho acesso" not in follow_content.lower(),
            f"answer={follow_content[:120]!r}",
        )
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL I6 — {exc}", file=sys.stderr)
        failed += 1
    finally:
        if project_id:
            _delete_project(token, project_id)

    if failed:
        print(f"\n{failed} interação(ões) falharam", file=sys.stderr)
        return 1

    print("\nSmoke treinamento 6 interações: todas passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
