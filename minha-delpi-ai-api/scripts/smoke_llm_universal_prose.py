#!/usr/bin/env python3
"""Smoke P5.6 — matriz Playbook 19 (inferência LLM universal).

Cenários: factory_status, playbook_top_items, kpi_cpv, sql, api_error.

Uso:
  SMOKE_SCENARIO=factory_status .venv/bin/python scripts/smoke_llm_universal_prose.py
  SMOKE_SCENARIO=all .venv/bin/python scripts/smoke_llm_universal_prose.py
  SMOKE_STRICT=1  # falha também em gaps de qualidade LLM (não só desacoplamento)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
SCENARIO = os.environ.get("SMOKE_SCENARIO", "factory_status").strip().lower()
STRICT = os.environ.get("SMOKE_STRICT", "").strip().lower() in {"1", "true", "yes"}
MAX_TEMPLATE_SIM = float(os.environ.get("SMOKE_MAX_TEMPLATE_SIMILARITY", "0.72"))

SCENARIOS: dict[str, dict[str, str | bool]] = {
    "factory_status": {
        "question": "qual o status do produto 90269002 na fabrica hoje?",
        "pathHint": "/factory-status",
        "requireOkTool": True,
    },
    "playbook_top_items": {
        "question": "Quais itens mais consumidos no mês passado filial 01 top 10?",
        "pathHint": "/production/consumption/top-items",
        "requireOkTool": True,
    },
    "kpi_cpv": {
        "question": "Qual o CPV da empresa?",
        "pathHint": "/supplies/cpv",
        "requireOkTool": True,
    },
    "sql": {
        "question": (
            "Execute SQL somente leitura: selecione top 5 produtos da SB1 "
            "com codigo e descricao"
        ),
        "pathHint": "/data/sql",
        "requireOkTool": True,
    },
    "api_error": {
        "question": "Qual o estoque do produto 99999999 inexistente?",
        "pathHint": "/products/",
        "requireOkTool": False,
    },
}


def req(method, url, token=None, body=None, timeout=600):
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


def _import_validator():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.domain.services.chat_response_mode_synthesis_quality_service import (
        ChatResponseModeSynthesisQualityService,
    )

    configure_domain_infrastructure_ports()
    return ChatResponseModeSynthesisQualityService


def _tool_metadata(assistant_metadata: dict) -> list[dict]:
    tool_calls = assistant_metadata.get("toolCalls")
    if not isinstance(tool_calls, list):
        return []
    return [tc for tc in tool_calls if isinstance(tc, dict)]


def _matching_tool(tool_calls: list[dict], path_hint: str, *, require_ok: bool) -> dict | None:
    hint = str(path_hint or "").lower()
    candidates: list[dict] = []

    for tool_call in tool_calls:
        if str(tool_call.get("name") or "") != "execute_external_action":
            continue

        metadata = tool_call.get("metadata")
        if not isinstance(metadata, dict):
            continue

        path = str(metadata.get("path") or "").lower()
        if hint and hint not in path:
            continue

        if require_ok and metadata.get("ok") is not True:
            continue

        candidates.append(metadata)

    if candidates:
        return candidates[0]

    for tool_call in tool_calls:
        if str(tool_call.get("name") or "") != "execute_external_action":
            continue

        metadata = tool_call.get("metadata")
        if not isinstance(metadata, dict):
            continue

        if require_ok and metadata.get("ok") is not True:
            continue

        return metadata

    return None


def _evaluate_structural(
    *,
    scenario: str,
    mode: str,
    tool_meta: dict | None,
    template_similarity: float,
    require_ok_tool: bool,
) -> list[str]:
    gaps: list[str] = []
    prefix = f"[{scenario}/{mode}]"

    if tool_meta is None:
        gaps.append(f"{prefix}: nenhuma tool execute_external_action compatível")
        return gaps

    if require_ok_tool and tool_meta.get("ok") is not True:
        gaps.append(f"{prefix}: tool ok=false inesperado para cenário operacional")

    if not (tool_meta.get("dataOnlyPresentation") or tool_meta.get("llmProseDecoupled")):
        gaps.append(f"{prefix}: falta dataOnlyPresentation/llmProseDecoupled")

    if str(tool_meta.get("proseDeliveryMode") or "") != "llm":
        gaps.append(f"{prefix}: proseDeliveryMode != llm")

    text_presentation = tool_meta.get("textPresentation")
    if isinstance(text_presentation, dict):
        markdown = str(text_presentation.get("markdown") or "").strip()
        if markdown:
            gaps.append(f"{prefix}: textPresentation.markdown preenchido em data-only")

    humanized = tool_meta.get("humanizedSummary")
    if isinstance(humanized, dict):
        if humanized.get("linhas") or humanized.get("linhas_detalhe"):
            gaps.append(f"{prefix}: humanizedSummary ainda contém linhas template")

    if template_similarity >= MAX_TEMPLATE_SIM:
        gaps.append(
            f"{prefix}: templateSimilarity {template_similarity} >= {MAX_TEMPLATE_SIM}"
        )

    return gaps


def _run_scenario(
    validator,
    *,
    token: str,
    agent_id: str,
    scenario_id: str,
    spec: dict,
) -> tuple[list[dict], list[str]]:
    question = str(spec.get("question") or "").strip()
    path_hint = str(spec.get("pathHint") or "")
    require_ok_tool = bool(spec.get("requireOkTool", True))
    results: list[dict] = []
    structural_gaps: list[str] = []

    for mode in ("fast", "normal", "thinker"):
        session = req(
            "POST",
            f"{BASE}{PREFIX}/sessions",
            token=token,
            body={"title": f"Smoke P19 {scenario_id} {mode}", "agentId": agent_id},
        )
        sid = session["id"]
        t0 = time.perf_counter()
        req(
            "POST",
            f"{BASE}{PREFIX}/sessions/{sid}/messages",
            token=token,
            body={"message": question, "agentId": agent_id, "responseMode": mode},
        )
        elapsed = round(time.perf_counter() - t0, 1)
        messages = req("GET", f"{BASE}{PREFIX}/sessions/{sid}/messages", token=token)
        msg_items = messages if isinstance(messages, list) else messages.get("items", [])
        assistant = next(m for m in reversed(msg_items) if m.get("role") == "assistant")
        metadata = assistant.get("metadata") or {}
        pipeline = (metadata.get("intelligence") or {}).get("pipeline", {})
        content = str(assistant.get("content") or "")
        tool_calls = _tool_metadata(metadata)
        template = validator.extract_template_markdown(tool_calls)
        similarity = round(validator.template_similarity(content, template), 3) if template else 0.0
        tool_meta = _matching_tool(tool_calls, path_hint, require_ok=require_ok_tool)

        structural_gaps.extend(
            _evaluate_structural(
                scenario=scenario_id,
                mode=mode,
                tool_meta=tool_meta,
                template_similarity=similarity,
                require_ok_tool=require_ok_tool,
            )
        )

        quality_gaps: list[str] = []
        if STRICT:
            quality_gaps = validator.evaluate_turn(
                mode=mode,
                question=question,
                content=content,
                assistant_metadata=metadata,
                elapsed_sec=elapsed,
            )

        results.append(
            {
                "scenario": scenario_id,
                "question": question,
                "mode": mode,
                "elapsedSec": elapsed,
                "chars": len(content),
                "path": (tool_meta or {}).get("path"),
                "toolOk": (tool_meta or {}).get("ok"),
                "effect": pipeline.get("responseModeEffect"),
                "templateSimilarity": similarity,
                "dataOnlyPresentation": (tool_meta or {}).get("dataOnlyPresentation"),
                "llmProseDecoupled": (tool_meta or {}).get("llmProseDecoupled"),
                "proseDeliveryMode": (tool_meta or {}).get("proseDeliveryMode"),
                "structuralGaps": [
                    gap
                    for gap in structural_gaps
                    if gap.startswith(f"[{scenario_id}/{mode}]")
                ],
                "qualityGaps": quality_gaps,
                "preview": content[:160].replace("\n", " "),
            }
        )

    ladder_gaps = validator.evaluate_mode_ladder(results) if STRICT else []
    return results, structural_gaps + ladder_gaps


def main() -> int:
    validator = _import_validator()

    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": "delpi-central",
            "username": os.environ.get("SMOKE_USER", "rober"),
            "password": os.environ.get("SMOKE_PASSWORD", "1234"),
        }
    ).encode()
    with urllib.request.urlopen(
        urllib.request.Request(
            f"{BASE}/auth/realms/delpi/protocol/openid-connect/token",
            data=form,
            method="POST",
        ),
        timeout=30,
    ) as response:
        token = json.loads(response.read())["access_token"]

    agents = req("GET", f"{BASE}{PREFIX}/agents?limit=5", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    agent_id = str(next(a["id"] for a in items if a.get("enabled")))

    if SCENARIO == "all":
        selected = list(SCENARIOS.items())
    else:
        spec = SCENARIOS.get(SCENARIO)
        if not spec:
            print(f"Cenário desconhecido: {SCENARIO}", file=sys.stderr)
            print(f"Válidos: {', '.join(SCENARIOS)} ou all", file=sys.stderr)
            return 2
        selected = [(SCENARIO, spec)]

    all_results: list[dict] = []
    all_gaps: list[str] = []

    for scenario_id, spec in selected:
        results, gaps = _run_scenario(
            validator,
            token=token,
            agent_id=agent_id,
            scenario_id=scenario_id,
            spec=spec,
        )
        all_results.extend(results)
        all_gaps.extend(gaps)

    payload = {
        "scenario": SCENARIO,
        "strictQuality": STRICT,
        "results": all_results,
        "passed": not all_gaps,
        "gapCount": len(all_gaps),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if all_gaps:
        print("\nFalhas estruturais/qualidade:", file=sys.stderr)
        for gap in all_gaps:
            print(f"- {gap}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
