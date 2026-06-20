#!/usr/bin/env python3
"""Smoke — modos de resposta com validação de qualidade (LLM vs template)."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
SCENARIO = os.environ.get("SMOKE_SCENARIO", "overview").strip().lower()

SCENARIOS = {
    "overview": "me fale do produto 10080045",
    "factory_status": "qual o status do produto 90269002 na fabrica hoje?",
    "stock_narrative": "como está o estoque do produto 10080045?",
}

QUESTION = os.environ.get("SMOKE_QUESTION", SCENARIOS.get(SCENARIO, SCENARIOS["overview"])).strip()


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

    results = []
    all_gaps: list[str] = []

    for mode in ("fast", "normal", "thinker"):
        session = req(
            "POST",
            f"{BASE}{PREFIX}/sessions",
            token=token,
            body={"title": f"Smoke {SCENARIO} {mode}", "agentId": agent_id},
        )
        sid = session["id"]
        t0 = time.perf_counter()
        req(
            "POST",
            f"{BASE}{PREFIX}/sessions/{sid}/messages",
            token=token,
            body={"message": QUESTION, "agentId": agent_id, "responseMode": mode},
        )
        elapsed = round(time.perf_counter() - t0, 1)
        messages = req("GET", f"{BASE}{PREFIX}/sessions/{sid}/messages", token=token)
        msg_items = messages if isinstance(messages, list) else messages.get("items", [])
        assistant = next(m for m in reversed(msg_items) if m.get("role") == "assistant")
        metadata = assistant.get("metadata") or {}
        pipeline = (metadata.get("intelligence") or {}).get("pipeline", {})
        content = str(assistant.get("content") or "")
        tool_calls = metadata.get("toolCalls") if isinstance(metadata.get("toolCalls"), list) else []
        template = validator.extract_template_markdown(tool_calls)
        similarity = round(validator.template_similarity(content, template), 3) if template else 0.0
        context_tokens = sorted(validator.extract_context_tokens(tool_calls))[:8]
        gaps = validator.evaluate_turn(
            mode=mode,
            question=QUESTION,
            content=content,
            assistant_metadata=metadata,
            elapsed_sec=elapsed,
        )

        for gap in gaps:
            all_gaps.append(f"[{mode}] {gap}")

        results.append(
            {
                "scenario": SCENARIO,
                "question": QUESTION,
                "mode": mode,
                "elapsedSec": elapsed,
                "chars": len(content),
                "content": content,
                "effect": pipeline.get("responseModeEffect"),
                "directResponse": pipeline.get("directResponse"),
                "templateChars": len(template),
                "templateSimilarity": similarity,
                "contextTokensSample": context_tokens,
                "qualityGaps": gaps,
                "preview": content[:160].replace("\n", " "),
            }
        )

    ladder_gaps = validator.evaluate_mode_ladder(results)
    all_gaps.extend(ladder_gaps)

    payload = {
        "results": results,
        "ladderGaps": ladder_gaps,
        "passed": not all_gaps,
        "gapCount": len(all_gaps),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if all_gaps:
        print("\nFalhas de qualidade:", file=sys.stderr)
        for gap in all_gaps:
            print(f"- {gap}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
