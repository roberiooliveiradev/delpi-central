#!/usr/bin/env python3
"""Smoke live — thread follow-up assertivo (ROL revise / challenge / typo).

Uso:
  cd minha-delpi-ai-api
  PYTHONPATH=. .venv/bin/python -u scripts/smoke_follow_up_assertivo_live.py

Variáveis:
  SMOKE_BASE_URL (default http://localhost)
  SMOKE_USER / SMOKE_PASSWORD
  SMOKE_RESPONSE_MODE (default normal)
  SMOKE_OFFLINE=1 — só imprime o roteiro sem HTTP
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_RESPONSE_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip()
_OFFLINE = os.environ.get("SMOKE_OFFLINE", "").strip().lower() in {"1", "true", "yes"}

_MISSING_PERIOD_RE = re.compile(
    r"(preciso.*(per[ií]odo|data)|informe.*(per[ií]odo|data)|qual (o )?per[ií]odo)",
    re.I,
)
_NARRATE_RECAP_RE = re.compile(r"Com base no [uú]ltimo resultado", re.I)


@dataclass
class TurnResult:
    label: str
    message: str
    response: dict = field(default_factory=dict)
    stage: str = ""
    paths: list[str] = field(default_factory=list)
    branches: list[str] = field(default_factory=list)
    prose: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 360,
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


def _parse_sse(raw: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    current_event = "message"
    data_lines: list[str] = []

    for line in raw.splitlines():
        if line.startswith("event:"):
            current_event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())
        elif line == "" and data_lines:
            try:
                payload = json.loads("\n".join(data_lines))
            except json.JSONDecodeError:
                payload = {}
            if isinstance(payload, dict):
                events.append((current_event, payload))
            data_lines = []
            current_event = "message"

    if data_lines:
        try:
            payload = json.loads("\n".join(data_lines))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            events.append((current_event, payload))

    return events


def _assistant_from_stream_done(data: dict) -> dict:
    if isinstance(data.get("assistantMessage"), dict):
        return data["assistantMessage"]
    if isinstance(data.get("message"), dict):
        return data["message"]
    return {
        "content": data.get("answer") or data.get("content") or "",
        "toolCalls": data.get("toolCalls") or [],
        "adminDebug": data.get("adminDebug") or {},
        "metadata": data.get("metadata") or {},
    }


def _stream_send(token: str, session_id: str, message: str) -> dict:
    request = urllib.request.Request(
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages/stream",
        data=json.dumps(
            {
                "message": message,
                "responseMode": _RESPONSE_MODE,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=420) as response:
        raw = response.read().decode("utf-8", errors="replace")
    events = _parse_sse(raw)
    done = next((payload for name, payload in reversed(events) if name == "done"), {})
    assistant = _assistant_from_stream_done(done)
    if not assistant.get("adminDebug") and done.get("adminDebug"):
        assistant["adminDebug"] = done["adminDebug"]
    if not assistant.get("metadata") and done.get("metadata"):
        assistant["metadata"] = done["metadata"]
    return assistant


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
    explicit = os.environ.get("SMOKE_AGENT_ID", "").strip()
    if explicit:
        return explicit
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def _ensure_financial_actions(token: str, agent_id: str) -> None:
    for action_id in (
        "api_delpi.financial.get_financial_rol",
        "api_delpi.financial.get_rol",
    ):
        try:
            _request(
                "PUT",
                f"{_BASE_URL}{_CHAT_PREFIX}/agents/{agent_id}/actions",
                token=token,
                body={
                    "providerKey": "api-delpi",
                    "actionId": action_id,
                    "enabled": True,
                },
            )
        except Exception:
            pass


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={
            "title": "Smoke follow-up assertivo ROL",
            "agentId": agent_id,
        },
    )
    return str(payload["id"])


def _assistant_prose(response: dict) -> str:
    for key in ("content", "answer", "message"):
        value = response.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    assistant = response.get("assistant")
    if isinstance(assistant, dict):
        for key in ("content", "message"):
            value = assistant.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _extract_stage(response: dict) -> str:
    admin = response.get("adminDebug") or {}
    for source in (
        admin.get("turnGrounding"),
        admin.get("intelligence", {}).get("turnGrounding")
        if isinstance(admin.get("intelligence"), dict)
        else None,
        (response.get("metadata") or {}).get("turnGrounding")
        if isinstance(response.get("metadata"), dict)
        else None,
    ):
        if isinstance(source, dict):
            stage = str(source.get("stage") or "").strip()
            if stage:
                return stage
    return ""


def _extract_paths_and_branches(response: dict) -> tuple[list[str], list[str]]:
    paths: list[str] = []
    branches: list[str] = []
    for call in response.get("toolCalls") or []:
        if not isinstance(call, dict):
            continue
        if str(call.get("name") or "") != "execute_external_action":
            continue
        meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
        path = str(meta.get("path") or "").strip()
        if path:
            paths.append(path)
        args = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
        params = args.get("parameters") if isinstance(args.get("parameters"), dict) else {}
        branch = str(params.get("branch") or meta.get("branch") or "").strip()
        if branch:
            branches.append(branch)
    return paths, branches


def _send(
    token: str,
    session_id: str,
    message: str,
    *,
    stream: bool = False,
) -> dict:
    if stream:
        return _stream_send(token, session_id, message)
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": message,
            "responseMode": _RESPONSE_MODE,
        },
        timeout=420,
    )


def _run_turn(
    *,
    label: str,
    message: str,
    token: str,
    session_id: str,
    expect_stage: str | None = None,
    expect_path_substr: str | None = None,
    expect_branch: str | None = None,
    forbid_missing_period: bool = False,
    forbid_narrate_recap: bool = False,
    expect_no_tools: bool = False,
    stream: bool = False,
) -> TurnResult:
    response = _send(token, session_id, message, stream=stream)
    stage = _extract_stage(response)
    paths, branches = _extract_paths_and_branches(response)
    prose = _assistant_prose(response)
    result = TurnResult(
        label=label,
        message=message,
        response=response,
        stage=stage,
        paths=paths,
        branches=branches,
        prose=prose,
    )

    if expect_stage and stage != expect_stage:
        # Live pode omitir stage no payload; ainda validamos tools/prosa.
        if stage:
            result.errors.append(f"stage={stage!r} esperado={expect_stage!r}")

    if expect_path_substr:
        if not any(expect_path_substr in path for path in paths):
            result.errors.append(
                f"path com {expect_path_substr!r} ausente; paths={paths}"
            )

    if expect_branch:
        if expect_branch not in branches:
            result.errors.append(
                f"branch={expect_branch!r} ausente; branches={branches}"
            )

    if expect_no_tools and paths:
        result.errors.append(f"esperava sem tools; paths={paths}")

    if forbid_missing_period and _MISSING_PERIOD_RE.search(prose):
        result.errors.append("prosa pediu período indevidamente")

    if forbid_narrate_recap and _NARRATE_RECAP_RE.search(prose) and not paths:
        result.errors.append("caiu em narrate-recap sem reexecutar")

    return result


def _print_offline_plan() -> None:
    print("SMOKE_OFFLINE=1 — roteiro da thread (sem HTTP):\n")
    turns = [
        ("T0", "qual o rol desse mês?", "seed ROL"),
        ("T1", "somente da filial 01", "revise → /financial/rol + branch=01"),
        ("T2", "o rol de uma unidade não pode ser igual ao total", "challenge sem missing_date"),
        ("T3", "rol filail 01 deste mês", "typo → branch=01"),
        ("T4", "resuma o resultado", "narrate sem tool"),
    ]
    for label, message, expect in turns:
        print(f"  {label}: {message!r}")
        print(f"       → {expect}")
    print("\nOffline gates:")
    print("  .venv/bin/python scripts/smoke_follow_up_assertivo_gates.py")


def main() -> int:
    if _OFFLINE:
        _print_offline_plan()
        return 0

    print(f"Base={_BASE_URL} mode={_RESPONSE_MODE}")
    try:
        token = _fetch_token()
    except Exception as exc:
        print(f"Falha auth/HTTP ({exc}). Use SMOKE_OFFLINE=1 ou suba a stack.")
        _print_offline_plan()
        return 2

    agent_id = _first_agent(token)
    _ensure_financial_actions(token, agent_id)
    session_id = _create_session(token, agent_id)
    print(f"session={session_id} agent={agent_id}")

    results: list[TurnResult] = []

    # Seed
    seed = _run_turn(
        label="T0-seed",
        message="qual o rol desse mês?",
        token=token,
        session_id=session_id,
        expect_path_substr="/financial/rol",
    )
    results.append(seed)

    results.append(
        _run_turn(
            label="T1-revise",
            message="somente da filial 01",
            token=token,
            session_id=session_id,
            expect_stage="grounded_revise_query",
            expect_path_substr="/financial/rol",
            expect_branch="01",
            forbid_narrate_recap=True,
        )
    )
    results.append(
        _run_turn(
            label="T2-challenge",
            message="o rol de uma unidade não pode ser igual ao total",
            token=token,
            session_id=session_id,
            expect_stage="grounded_challenge_result",
            expect_no_tools=True,
            forbid_missing_period=True,
        )
    )
    results.append(
        _run_turn(
            label="T3-typo",
            message="rol filail 01 deste mês",
            token=token,
            session_id=session_id,
            expect_branch="01",
            expect_path_substr="/financial/rol",
        )
    )
    results.append(
        _run_turn(
            label="T4-narrate",
            message="resuma o resultado",
            token=token,
            session_id=session_id,
            expect_no_tools=True,
        )
    )

    # Stream spot-check no revise (nova sessão)
    session_stream = _create_session(token, agent_id)
    _run_turn(
        label="S0-seed",
        message="qual o rol desse mês?",
        token=token,
        session_id=session_stream,
    )
    results.append(
        _run_turn(
            label="S1-revise-stream",
            message="somente da filial 01",
            token=token,
            session_id=session_stream,
            expect_path_substr="/financial/rol",
            expect_branch="01",
            stream=True,
            forbid_narrate_recap=True,
        )
    )

    print("\n== Resultados ==")
    failed = 0
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        if not item.passed:
            failed += 1
        print(
            f"{status} {item.label}: stage={item.stage!r} "
            f"paths={item.paths} branches={item.branches}"
        )
        for err in item.errors:
            print(f"       ! {err}")
        if item.prose:
            preview = item.prose.replace("\n", " ")[:160]
            print(f"       prose: {preview}")

    if failed:
        print(f"\nFAIL — {failed} turno(s)")
        return 1

    print("\nOK — follow-up assertivo live")
    return 0


if __name__ == "__main__":
    sys.exit(main())
