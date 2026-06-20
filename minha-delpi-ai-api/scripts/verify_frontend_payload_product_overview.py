#!/usr/bin/env python3
"""Verifica contrato API→MFE para overview de produto (prosa LLM + renderPlan)."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
QUESTION = os.environ.get("SMOKE_QUESTION", "me fale do produto 10080045").strip()
MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip()


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


def _first_external_tool_call(metadata: dict) -> dict | None:
    for tool_call in metadata.get("toolCalls") or []:
        if not isinstance(tool_call, dict):
            continue
        if str(tool_call.get("name") or "") == "execute_external_action":
            return tool_call
    return None


def _validate_frontend_contract(assistant: dict) -> list[str]:
    gaps: list[str] = []
    metadata = assistant.get("metadata") or {}
    content = str(assistant.get("content") or "").strip()
    tool_call = _first_external_tool_call(metadata)
    tc_meta = (tool_call or {}).get("metadata") or {}

    if not content:
        gaps.append("message.content vazio — MFE não terá prosa no lead")

    if not tool_call:
        gaps.append("metadata.toolCalls sem execute_external_action")
        return gaps

    if tc_meta.get("ok") is not True:
        gaps.append(f"tool metadata ok=false (status={tc_meta.get('statusCode')})")

    if not tc_meta.get("llmProseDecoupled"):
        gaps.append("llmProseDecoupled ausente/false — MFE pode repetir template no markdown")

    if not tc_meta.get("dataOnlyPresentation"):
        gaps.append("dataOnlyPresentation ausente/false — prosa template pode vazar")

    if str(tc_meta.get("proseDeliveryMode") or "") != "llm":
        gaps.append(
            f"proseDeliveryMode esperado 'llm', veio {tc_meta.get('proseDeliveryMode')!r}",
        )

    text_presentation = tc_meta.get("textPresentation") or {}
    if isinstance(text_presentation, dict):
        markdown = str(text_presentation.get("markdown") or "").strip()
        if markdown:
            gaps.append("textPresentation.markdown preenchido em turno data-only/decoupled")

    humanized = tc_meta.get("humanizedSummary") or {}
    if isinstance(humanized, dict):
        if humanized.get("linhas") or humanized.get("linhas_detalhe"):
            gaps.append("humanizedSummary.linhas ainda presentes — risco de duplicar prosa template")

    render_plan = tc_meta.get("renderPlan")
    if not isinstance(render_plan, dict):
        gaps.append("renderPlan ausente em toolCalls[].metadata")
    else:
        if render_plan.get("version") != 1:
            gaps.append(f"renderPlan.version esperado 1, veio {render_plan.get('version')!r}")

        segments = render_plan.get("segments") or []
        if not isinstance(segments, list) or not segments:
            gaps.append("renderPlan.segments vazio")
        else:
            kinds = [
                str(item.get("kind") or "").strip().lower()
                for item in segments
                if isinstance(item, dict)
            ]
            if "markdown" not in kinds:
                gaps.append(f"renderPlan sem segmento markdown (kinds={kinds})")

            visual_kinds = {"table", "tree", "chart", "kpi", "dashboard"}
            if not any(kind in visual_kinds for kind in kinds):
                gaps.append(f"renderPlan sem evidência visual (kinds={kinds})")

            if kinds[0] != "markdown":
                gaps.append(f"primeiro segmento deveria ser markdown/lead, veio {kinds[0]!r}")

    tables = tc_meta.get("tablePresentations") or []
    if not isinstance(tables, list) or not tables:
        gaps.append("tablePresentations vazio — MFE não renderiza tabela nativa")

    error_handling = metadata.get("errorHandling")
    if isinstance(error_handling, dict):
        err_type = str(error_handling.get("type") or "").strip()
        if err_type == "empty_result" and tables:
            gaps.append("errorHandling.empty_result com tabela presente — banner falso no MFE")

    if "10080045" not in content.replace(" ", "").replace("*", ""):
        gaps.append("código 10080045 ausente em message.content (prosa visível ao usuário)")

    decision = tc_meta.get("presentationDecision") or {}
    if isinstance(decision, dict):
        selected = str(decision.get("selected") or "").strip().lower()
        layout = str(decision.get("layoutMode") or "").strip().lower()
        if selected not in {"table", "text", "auto"}:
            gaps.append(f"presentationDecision.selected inesperado: {selected!r}")
        if layout not in {"stack", "single", ""}:
            gaps.append(f"presentationDecision.layoutMode inesperado: {layout!r}")

    return gaps


def main() -> int:
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

    session = req(
        "POST",
        f"{BASE}{PREFIX}/sessions",
        token=token,
        body={"title": "Verify frontend payload", "agentId": agent_id},
    )
    sid = session["id"]

    req(
        "POST",
        f"{BASE}{PREFIX}/sessions/{sid}/messages",
        token=token,
        body={"message": QUESTION, "agentId": agent_id, "responseMode": MODE},
    )

    messages = req("GET", f"{BASE}{PREFIX}/sessions/{sid}/messages", token=token)
    msg_items = messages if isinstance(messages, list) else messages.get("items", [])
    assistant = next(m for m in reversed(msg_items) if m.get("role") == "assistant")

    gaps = _validate_frontend_contract(assistant)
    tool_call = _first_external_tool_call(assistant.get("metadata") or {})
    tc_meta = (tool_call or {}).get("metadata") or {}
    render_plan = tc_meta.get("renderPlan") or {}

    report = {
        "question": QUESTION,
        "mode": MODE,
        "contentChars": len(str(assistant.get("content") or "")),
        "contentPreview": str(assistant.get("content") or "")[:240],
        "renderPlanSegments": [
            {
                "kind": segment.get("kind"),
                "slot": segment.get("slot"),
                "source": segment.get("source"),
            }
            for segment in (render_plan.get("segments") or [])
            if isinstance(segment, dict)
        ],
        "llmProseDecoupled": tc_meta.get("llmProseDecoupled"),
        "dataOnlyPresentation": tc_meta.get("dataOnlyPresentation"),
        "proseDeliveryMode": tc_meta.get("proseDeliveryMode"),
        "tableCount": len(tc_meta.get("tablePresentations") or []),
        "errorHandlingType": (assistant.get("metadata") or {}).get("errorHandling", {}).get("type")
        if isinstance((assistant.get("metadata") or {}).get("errorHandling"), dict)
        else None,
        "presentationSelected": (tc_meta.get("presentationDecision") or {}).get("selected"),
        "presentationLayout": (tc_meta.get("presentationDecision") or {}).get("layoutMode"),
        "gaps": gaps,
        "passed": not gaps,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if gaps:
        print("\nFalhas contrato API→MFE:", file=sys.stderr)
        for gap in gaps:
            print(f"- {gap}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
