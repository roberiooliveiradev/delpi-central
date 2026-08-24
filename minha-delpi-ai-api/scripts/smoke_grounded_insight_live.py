#!/usr/bin/env python3
"""Smoke live E15 — checkpoints CP1/CP2 (grounded insight + fan-out MP).

Uso:
  cd minha-delpi-ai-api
  PYTHONPATH=. .venv/bin/python scripts/smoke_grounded_insight_live.py

Variáveis:
  SMOKE_BASE_URL (default http://localhost)
  SMOKE_USER / SMOKE_PASSWORD
  SMOKE_PRODUCT_CODE (default 90260149)
  SMOKE_RESPONSE_MODE (default normal)
  SMOKE_SKIP_THINKER=1 — pula repetição T2 em modo thinker
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "90260149").strip()
_RESPONSE_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip()
_SKIP_THINKER = os.environ.get("SMOKE_SKIP_THINKER", "").strip().lower() in {
    "1",
    "true",
    "yes",
}

_REFORMULE_RE = re.compile(r"\b(reformule|reformular)\b", re.I)
_TECH_DUMP_RE = re.compile(r"\b(Código|Tipo)\s*:", re.I)


@dataclass
class TurnResult:
    label: str
    message: str
    response: dict
    stage: str = ""
    operation_ids: list[str] = field(default_factory=list)
    stock_paths: list[str] = field(default_factory=list)
    prose: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=360) as response:
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


def _ensure_product_actions(token: str, agent_id: str) -> None:
    for action_id in (
        "api_delpi.products.get_product_stock",
        "api_delpi.products.get_product_structure",
        "api_delpi.products.get_product_summary",
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

    try:
        _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/agents/{agent_id}/providers/api-delpi/import",
            token=token,
        )
    except Exception:
        pass


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={
            "title": f"Smoke grounded insight {_PRODUCT}",
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
        admin.get("intelligence", {}).get("turnGrounding") if isinstance(admin.get("intelligence"), dict) else None,
    ):
        if isinstance(source, dict):
            stage = str(source.get("stage") or "").strip()

            if stage:
                return stage

    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        grounding = meta.get("turnGrounding")

        if isinstance(grounding, dict):
            stage = str(grounding.get("stage") or "").strip()

            if stage:
                return stage

    return ""


def _tool_meta(response: dict) -> list[dict]:
    return [
        call.get("metadata") or {}
        for call in (response.get("toolCalls") or [])
        if isinstance(call, dict)
    ]


def _operation_ids(response: dict) -> list[str]:
    ids: list[str] = []

    for meta in _tool_meta(response):
        operation_id = str(
            meta.get("operationId")
            or (meta.get("apiDelpiResponseMeta") or {}).get("operationId")
            or ""
        ).strip()

        if operation_id and operation_id not in ids:
            ids.append(operation_id)

    return ids


def _stock_paths(response: dict) -> list[str]:
    paths: list[str] = []

    for meta in _tool_meta(response):
        path = str(meta.get("path") or "").strip()

        if "/stock" in path.lower() and path not in paths:
            paths.append(path)

    return paths


def _has_tree_or_table(response: dict) -> bool:
    for meta in _tool_meta(response):
        presentation = meta.get("presentation") or {}
        ptype = str(presentation.get("type") or "").strip().lower()

        if ptype in {"tree", "table"}:
            return True

        if isinstance(meta.get("treePresentation"), dict):
            return True

        render_plan = meta.get("renderPlan")

        if isinstance(render_plan, dict) and render_plan.get("segments"):
            return True

    return False


def _send(
    token: str,
    session_id: str,
    agent_id: str,
    message: str,
    *,
    response_mode: str | None = None,
) -> dict:
    body = {
        "message": message,
        "agentId": agent_id,
        "adminDebug": True,
        "responseMode": response_mode or _RESPONSE_MODE,
    }

    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body=body,
    )


def _validate_cp1(result: TurnResult) -> None:
    if not _has_tree_or_table(result.response):
        result.errors.append("sem apresentação tree/table na tool de estrutura")

    if _REFORMULE_RE.search(result.prose):
        result.errors.append("prosa contém «reformule/reformular»")

    structure_paths = [
        meta.get("path")
        for meta in _tool_meta(result.response)
        if "/structure" in str(meta.get("path") or "").lower()
    ]

    if not structure_paths:
        result.errors.append("sem toolCall /structure")

    if _PRODUCT not in json.dumps(result.response, ensure_ascii=False):
        result.warnings.append(f"código {_PRODUCT} não encontrado no payload bruto")


def _validate_cp2_t2(result: TurnResult) -> None:
    if result.stage and result.stage != "grounded_enrich_insight":
        result.errors.append(f"stage esperado grounded_enrich_insight, obteve {result.stage!r}")

    if _TECH_DUMP_RE.search(result.prose):
        result.errors.append("prosa com dump técnico Código:/Tipo:")

    if _REFORMULE_RE.search(result.prose):
        result.errors.append("prosa contém «reformule/reformular»")

    if not result.operation_ids and not result.stock_paths:
        result.warnings.append("sem operationId/stock visível — agente sem actions?")


def _validate_cp2_t3(result: TurnResult, parent_product: str) -> None:
    if not result.stock_paths:
        result.errors.append("T3 sem toolCalls /stock")

    for path in result.stock_paths:
        if parent_product in path:
            result.errors.append(f"T3 consultou PA {parent_product} em vez de MPs: {path}")

    mp_hits = [path for path in result.stock_paths if parent_product not in path]

    if result.stock_paths and not mp_hits:
        result.errors.append("nenhum path stock de MP distinto do PA")


def _print_turn(result: TurnResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"\n[{status}] {result.label}")
    print(f"  message: {result.message}")
    print(f"  stage: {result.stage or '(n/a)'}")
    print(f"  operationIds: {result.operation_ids or '(n/a)'}")
    print(f"  stockPaths: {result.stock_paths or '(n/a)'}")

    if result.prose:
        preview = result.prose[:240].replace("\n", " ")
        print(f"  prose: {preview}…")

    for warning in result.warnings:
        print(f"  WARN: {warning}")

    for error in result.errors:
        print(f"  FAIL: {error}", file=sys.stderr)


def _run_turn(
    token: str,
    session_id: str,
    agent_id: str,
    *,
    label: str,
    message: str,
    response_mode: str | None = None,
) -> TurnResult:
    response = _send(
        token,
        session_id,
        agent_id,
        message,
        response_mode=response_mode,
    )

    return TurnResult(
        label=label,
        message=message,
        response=response,
        stage=_extract_stage(response),
        operation_ids=_operation_ids(response),
        stock_paths=_stock_paths(response),
        prose=_assistant_prose(response),
    )


def _render_markdown_report(
    session_id: str,
    turns: list[TurnResult],
    *,
    thinker_turn: TurnResult | None,
) -> str:
    today = date.today().isoformat()
    lines = [
        f"# Grounded insight — validação live",
        "",
        f"Produto canônico: `{_PRODUCT}` · modo default: `{_RESPONSE_MODE}` · data: {today}",
        "",
        "## CP1 — estrutura T1 (E10)",
        "",
        "| Turno | Mensagem | stage | operationIds | Pass? |",
        "|-------|----------|-------|--------------|-------|",
    ]

    t1 = turns[0]
    lines.append(
        f"| T1 | {t1.message} | {t1.stage or '—'} | {', '.join(t1.operation_ids) or '—'} | "
        f"{'✅' if t1.passed else '❌'} |"
    )

    lines.extend(
        [
            "",
            "### Prosa T1 (trecho)",
            "",
            t1.prose[:800] or "_(vazio)_",
            "",
            "## CP2 — três turnos (E11+E13)",
            "",
            "| Turno | Mensagem | stage | stock paths / operationIds | Pass? |",
            "|-------|----------|-------|----------------------------|-------|",
        ]
    )

    for turn in turns[1:]:
        ops = ", ".join(turn.stock_paths or turn.operation_ids) or "—"
        lines.append(
            f"| {turn.label} | {turn.message} | {turn.stage or '—'} | {ops} | "
            f"{'✅' if turn.passed else '❌'} |"
        )

    if thinker_turn:
        lines.extend(
            [
                "",
                "### T2 modo Pensador",
                "",
                f"- stage: `{thinker_turn.stage or '—'}`",
                f"- Pass: {'✅' if thinker_turn.passed else '❌'}",
            ]
        )

    lines.extend(
        [
            "",
            "## CP3 — composição LLM (E18)",
            "",
            "_Pendente — executar após E18 (marcadores `[[table]]` / `renderPlan` intercalado)._",
            "",
            "## Problemas / regressões",
            "",
        ]
    )

    problems = [f"- **{turn.label}**: {err}" for turn in turns for err in turn.errors]

    if thinker_turn:
        problems.extend(f"- **T2 thinker**: {err}" for err in thinker_turn.errors)

    lines.append("\n".join(problems) if problems else "- Nenhum na execução automatizada.")

    lines.extend(
        [
            "",
            "## Metadata",
            "",
            f"- sessionId: `{session_id}`",
            f"- script: `scripts/smoke_grounded_insight_live.py`",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    failed = 0
    turns: list[TurnResult] = []
    thinker_turn: TurnResult | None = None

    try:
        token = _fetch_token()
        print("OK login")
    except Exception as exc:
        print(f"FAIL login: {exc}", file=sys.stderr)
        print(
            "Dica: suba a stack com ./infra/scripts/up-dev-sequential.sh --fase core "
            "e ./infra/scripts/up-dev-sequential.sh --fase chat --build minha-delpi-ai-api",
            file=sys.stderr,
        )
        return 1

    try:
        agent_id = _first_agent(token)
        _ensure_product_actions(token, agent_id)
        session_id = _create_session(token, agent_id)
        print(f"OK sessão {session_id} agent={agent_id}")
    except Exception as exc:
        print(f"FAIL setup: {exc}", file=sys.stderr)
        return 1

    t1 = _run_turn(
        token,
        session_id,
        agent_id,
        label="T1",
        message=f"qual a estrutura do produto {_PRODUCT}",
    )
    _validate_cp1(t1)
    turns.append(t1)
    _print_turn(t1)
    failed += 0 if t1.passed else 1

    t2 = _run_turn(
        token,
        session_id,
        agent_id,
        label="T2",
        message="o que me diz sobre os itens?",
    )
    _validate_cp2_t2(t2)
    turns.append(t2)
    _print_turn(t2)
    failed += 0 if t2.passed else 1

    t3 = _run_turn(
        token,
        session_id,
        agent_id,
        label="T3",
        message="qual o estoque das matérias-primas?",
    )
    _validate_cp2_t3(t3, _PRODUCT)
    turns.append(t3)
    _print_turn(t3)
    failed += 0 if t3.passed else 1

    if not _SKIP_THINKER:
        thinker_turn = _run_turn(
            token,
            session_id,
            agent_id,
            label="T2-thinker",
            message="o que me diz sobre os itens?",
            response_mode="thinker",
        )
        _validate_cp2_t2(thinker_turn)
        _print_turn(thinker_turn)
        failed += 0 if thinker_turn.passed else 1

    report_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "docs",
        "operations",
        "grounded-insight-live-validation.md",
    )
    report = _render_markdown_report(session_id, turns, thinker_turn=thinker_turn)

    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write(report)

        print(f"\nOK relatório: {os.path.abspath(report_path)}")
    except Exception as exc:
        print(f"WARN não gravou relatório: {exc}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
