#!/usr/bin/env python3
"""One-shot: avaliação rota × qualidade do texto (dev stack via docker network)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("SMOKE_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
KC = os.environ.get(
    "SMOKE_KEYCLOAK_TOKEN_URL",
    "http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/token",
).strip()
CLIENT = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
USER = os.environ.get("SMOKE_USER", "rober").strip()
PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/api/chat").strip()
CODE = os.environ.get("SMOKE_PRODUCT_CODE", "90260148").strip()

CASES = [
    f"ultimas notas fiscais do {CODE}",
    f"nfe do {CODE}",
    f"invoice items {CODE}",
    f"notas fiscais de entrada do {CODE}",
    f"notas fiscais de saída do {CODE}",
    f"movimentacao interna do {CODE}",
    f"directive list {CODE}",
    f"exclusividade de mp {CODE}",
    f"estoque do produto {CODE}",
    f"me fale do produto {CODE}",
    "estoque",
]


def req(method: str, url: str, token: str | None = None, body: dict | None = None, timeout: int = 300):
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode()
        return json.loads(raw) if raw else {}


def token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": CLIENT,
            "username": USER,
            "password": PASSWORD,
        }
    ).encode()
    request = urllib.request.Request(KC, data=form, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode())
    access = payload.get("access_token")
    if not access:
        raise RuntimeError(f"token ausente: {payload}")
    return str(access)


def agent_id(tok: str) -> str:
    agents = req("GET", f"{BASE}{CHAT}/agents?limit=40", token=tok)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and "minha" in str(agent.get("name") or "").lower():
            return str(agent["id"])
    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])
    raise RuntimeError(f"sem agente: {items[:2]}")


def paths_from(resp: dict) -> list[dict]:
    out: list[dict] = []
    for call in resp.get("toolCalls") or []:
        if str(call.get("name") or "") != "execute_external_action":
            continue
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "")
        if path:
            out.append(
                {
                    "path": path,
                    "ok": bool(meta.get("ok")),
                    "empty": bool(meta.get("emptyResult")),
                    "op": str(meta.get("operationId") or ""),
                    "error": str(meta.get("error") or meta.get("message") or "")[:160],
                }
            )
    return out


def text_quality(content: str, paths: list[dict], error: str | None) -> str:
    text = (content or "").strip()
    low = text.lower()
    if error:
        return f"ERRO: {error[:140]}"
    if "memory_snapshot" in low or "nameerror" in low:
        return "ERRO NameError memory_snapshot"
    if not text:
        return "Vazio"
    weak_empty = (
        "não encontrei",
        "nao encontrei",
        "nenhum registro",
        "sem dados",
        "não há",
        "nao ha",
        "lista vazia",
        "sem itens",
    )
    weak_clarify = (
        "preciso que",
        "pode reformular",
        "não ficou claro",
        "nao ficou claro",
        "qual informação",
        "me diga o código",
    )
    if any(marker in low for marker in weak_clarify) and len(text) < 320:
        return "Clarify / incompleto"
    if any(marker in low for marker in weak_empty) and len(text) < 320:
        return "Fraco no vazio"
    if any(marker in low for marker in ("atenção", "atencao", "próximos passos", "proximos passos")) and any(
        path.get("empty") for path in paths
    ):
        return "Fraco (atenção/nextSteps em vazio)"
    if len(text) > 140 and not any(marker in low for marker in weak_empty):
        return "Bom"
    if len(text) >= 80:
        return "Aceitável"
    return "Fraco (curto)"


def _first_str(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return ""


def content_of(resp: dict) -> str:
    meta = resp.get("metadata") if isinstance(resp.get("metadata"), dict) else {}
    presentation = meta.get("presentation") if isinstance(meta.get("presentation"), dict) else {}
    data_answer = meta.get("dataAnswer") if isinstance(meta.get("dataAnswer"), dict) else {}
    render_plan = meta.get("renderPlan") if isinstance(meta.get("renderPlan"), dict) else {}
    segments = render_plan.get("segments") if isinstance(render_plan.get("segments"), list) else []
    segment_texts = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        segment_texts.append(
            _first_str(segment.get("text"), segment.get("markdown"), segment.get("content"))
        )
    message = resp.get("message") if isinstance(resp.get("message"), dict) else {}
    direct = meta.get("directResponse") if isinstance(meta.get("directResponse"), dict) else {}
    tool_answers: list[str] = []
    for call in resp.get("toolCalls") or []:
        if not isinstance(call, dict):
            continue
        call_meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
        data_ans = call_meta.get("dataAnswer") if isinstance(call_meta.get("dataAnswer"), dict) else {}
        summary = data_ans.get("summary") if isinstance(data_ans.get("summary"), dict) else {}
        archive = call_meta.get("templateProseArchive") if isinstance(call_meta.get("templateProseArchive"), dict) else {}
        humanized = archive.get("humanizedSummary") if isinstance(archive.get("humanizedSummary"), dict) else {}
        lines = humanized.get("linhas") if isinstance(humanized.get("linhas"), list) else []
        tool_answers.append(
            _first_str(
                summary.get("answer"),
                data_ans.get("lead"),
                archive.get("textPresentationMarkdown"),
                "\n".join(str(line) for line in lines if str(line).strip()),
            )
        )
    return _first_str(
        resp.get("answer"),
        resp.get("content"),
        resp.get("humanizedSummary"),
        resp.get("directAnswer"),
        message.get("content"),
        message.get("answer"),
        message.get("humanizedSummary"),
        meta.get("humanizedSummary"),
        meta.get("directAnswer"),
        meta.get("assistantMessage"),
        direct.get("message"),
        direct.get("text"),
        direct.get("answer"),
        data_answer.get("lead"),
        data_answer.get("text"),
        presentation.get("humanizedSummary"),
        presentation.get("title"),
        "\n".join(text for text in segment_texts if text),
        "\n".join(text for text in tool_answers if text),
    )

def main() -> int:
    cases_env = os.environ.get("SMOKE_EVAL_CASES", "").strip()
    cases = [item.strip() for item in cases_env.split("||") if item.strip()] if cases_env else list(CASES)
    tok = token()
    aid = agent_id(tok)
    print(f"base={BASE} agent={aid} code={CODE} cases={len(cases)}\n")
    rows: list[dict] = []
    out_path = os.environ.get(
        "SMOKE_EVAL_OUT",
        "/app/scripts/_tmp_eval_routes_text_quality.json"
        if os.path.isdir("/app/scripts")
        else str(os.path.join(os.path.dirname(__file__), "_tmp_eval_routes_text_quality.json")),
    )

    for message in cases:
        error: str | None = None
        response: dict = {}
        paths: list[dict] = []
        content = ""
        intent_meta: dict = {}
        started = time.monotonic()
        try:
            tok = token()
            session = req(
                "POST",
                f"{BASE}{CHAT}/sessions",
                token=tok,
                body={"title": f"eval {message[:48]}", "agentId": aid},
            )
            session_id = str(session["id"])
            response = req(
                "POST",
                f"{BASE}{CHAT}/sessions/{session_id}/messages",
                token=tok,
                body={"message": message, "agentId": aid},
                timeout=180,
            )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")[:240]
            error = f"HTTP {exc.code}: {body}"
        except Exception as exc:  # noqa: BLE001 — smoke
            error = f"{type(exc).__name__}: {exc}"
        elapsed = time.monotonic() - started
        if response:
            content = content_of(response)
            meta = response.get("metadata") or {}
            paths = paths_from(response)
            if not paths and isinstance(meta, dict) and isinstance(meta.get("toolCalls"), list):
                paths = paths_from({"toolCalls": meta["toolCalls"]})
            if "memory_snapshot" in content.lower() or "memory_snapshot" in str(meta).lower():
                error = error or "memory_snapshot na resposta"
            intent_meta = meta.get("intentRoute") if isinstance(meta, dict) else None
            if not isinstance(intent_meta, dict):
                intent_meta = ((response.get("adminDebug") or {}).get("intentRoute") or {})
        path_str = ", ".join(path["path"] for path in paths) or "—"
        quality = text_quality(content, paths, error)
        row = {
            "msg": message,
            "path": path_str,
            "n_tools": len(paths),
            "ok_tools": sum(1 for path in paths if path.get("ok")),
            "empty_tools": sum(1 for path in paths if path.get("empty")),
            "intent": intent_meta.get("intent") or intent_meta.get("subIntent") or "?",
            "quality": quality,
            "sec": round(elapsed, 1),
            "preview": content.replace("\n", " ").strip()[:180],
            "err": error,
            "tool_errors": [path.get("error") for path in paths if path.get("error")],
        }
        rows.append(row)
        print(f"[{quality}] {message!r}")
        print(f"  path={path_str} tools={len(paths)} ok={row['ok_tools']} {elapsed:.1f}s")
        print(f"  text={row['preview']!r}")
        print()
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(rows, handle, ensure_ascii=False, indent=2)
        time.sleep(1.0)

    print(f"wrote {out_path}")
    print("===JSON===")
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
