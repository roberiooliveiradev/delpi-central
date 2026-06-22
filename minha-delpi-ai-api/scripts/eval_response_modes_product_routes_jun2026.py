#!/usr/bin/env python3
"""Avaliação E2E — rotas produto × modos fast/normal/thinker (jun/2026)."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
PAUSE = float(os.environ.get("SMOKE_PAUSE_SECONDS", "1.5"))

SCENARIOS = [
    {
        "id": "factory_broad",
        "group": "factory",
        "message": "Qual o status completo na fábrica do produto 90269002 hoje?",
        "expectedPath": "/factory-status",
    },
    {
        "id": "factory_colloquial",
        "group": "factory",
        "message": "Situação na fábrica / visão fabril integrada do PA 90269002",
        "expectedPath": "/factory-status",
    },
    {
        "id": "production_granular",
        "group": "factory",
        "message": "O produto 90269002 já começou a produzir? Tem apontamento na OP?",
        "expectedPath": "/production-status",
    },
    {
        "id": "shipping_granular",
        "group": "factory",
        "message": "Quanto do produto 90269002 já foi liberado para expedição hoje?",
        "expectedPath": "/shipping-status",
    },
    {
        "id": "exclusivity_granular",
        "group": "factory",
        "message": "Quais matérias-primas exclusivas existem na estrutura do produto 90269002?",
        "expectedPath": "/structure/exclusivity",
    },
    {
        "id": "mp_intelligence_broad",
        "group": "mp_price",
        "message": "Análise de preço da matéria-prima 10080001",
        "expectedPath": "/raw-material-price-intelligence",
    },
    {
        "id": "mp_intelligence_detail",
        "group": "mp_price",
        "message": "Último fornecedor, ICMS, histórico de orçamento e variação de preço da MP 10080001",
        "expectedPath": "/raw-material-price-intelligence",
    },
    {
        "id": "mp_last_purchase_granular",
        "group": "mp_price",
        "message": "Última compra e ICMS do produto 10080001",
        "expectedPath": ("/last-purchase", "/raw-material-price-intelligence"),
    },
    {
        "id": "cost_pareto",
        "group": "cost_sim",
        "message": "Quais materiais mais impactam o custo do PA 90261255?",
        "expectedPath": "/cost-impact-simulation",
    },
    {
        "id": "cost_adjust_10",
        "group": "cost_sim",
        "message": "Simule aumento de 10% nos materiais do produto 90261255",
        "expectedPath": "/cost-impact-simulation",
    },
]

MODES = ("fast", "normal", "thinker")


def req(method: str, url: str, *, token: str, body: dict | None = None, timeout: int = 600) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

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
            "client_id": os.environ.get("SMOKE_CLIENT_ID", "delpi-central"),
            "username": os.environ.get("SMOKE_USER", "rober"),
            "password": os.environ.get("SMOKE_PASSWORD", "1234"),
        }
    ).encode()
    request = urllib.request.Request(
        f"{BASE}/auth/realms/delpi/protocol/openid-connect/token",
        data=form,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read())

    return str(payload["access_token"])


def agent_id(tok: str) -> str:
    agents = req("GET", f"{BASE}{PREFIX}/agents?limit=20", token=tok)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    return str(next(a["id"] for a in items if a.get("enabled")))


def action_path(metadata: dict) -> str:
    for call in metadata.get("toolCalls") or []:
        if str(call.get("name") or "") != "execute_external_action":
            continue

        path = str((call.get("metadata") or {}).get("path") or "")

        if path:
            return path

    return ""


def path_ok(path: str, expected: str | tuple[str, ...]) -> bool:
    if isinstance(expected, tuple):
        return any(fragment in path for fragment in expected)

    return expected in path


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.domain.services.chat_response_mode_synthesis_quality_service import (
        ChatResponseModeSynthesisQualityService,
    )

    configure_domain_infrastructure_ports()
    validator = ChatResponseModeSynthesisQualityService

    tok = token()
    aid = agent_id(tok)
    results: list[dict] = []

    for scenario in SCENARIOS:
        for mode in MODES:
            time.sleep(PAUSE)
            session = req(
                "POST",
                f"{BASE}{PREFIX}/sessions",
                token=tok,
                body={"title": f"Eval {scenario['id']} {mode}", "agentId": aid},
            )
            sid = session["id"]
            started = time.perf_counter()
            req(
                "POST",
                f"{BASE}{PREFIX}/sessions/{sid}/messages",
                token=tok,
                body={
                    "message": scenario["message"],
                    "agentId": aid,
                    "responseMode": mode,
                },
            )
            elapsed = round(time.perf_counter() - started, 1)
            messages = req("GET", f"{BASE}{PREFIX}/sessions/{sid}/messages", token=tok)
            items = messages if isinstance(messages, list) else messages.get("items", [])
            assistant = next(m for m in reversed(items) if m.get("role") == "assistant")
            metadata = assistant.get("metadata") or {}
            content = str(assistant.get("content") or "")
            path = action_path(metadata)
            pipeline = (metadata.get("intelligence") or {}).get("pipeline") or {}
            tool_calls = metadata.get("toolCalls") if isinstance(metadata.get("toolCalls"), list) else []
            gaps = validator.evaluate_turn(
                mode=mode,
                question=scenario["message"],
                content=content,
                assistant_metadata=metadata,
                elapsed_sec=elapsed,
            )
            route_ok = path_ok(path, scenario["expectedPath"])
            results.append(
                {
                    "scenarioId": scenario["id"],
                    "group": scenario["group"],
                    "mode": mode,
                    "message": scenario["message"],
                    "expectedPath": scenario["expectedPath"],
                    "actualPath": path,
                    "routeOk": route_ok,
                    "elapsedSec": elapsed,
                    "chars": len(content),
                    "directResponse": pipeline.get("directResponse"),
                    "responseModeEffect": pipeline.get("responseModeEffect"),
                    "qualityGaps": gaps,
                    "contentPreview": content[:500],
                    "dataAnswer": (metadata.get("dataAnswer") or "")[:300],
                    "presentationDecision": metadata.get("presentationDecision"),
                }
            )
            status = "OK" if route_ok and not gaps else "GAP"
            print(
                f"{status} {scenario['id']} [{mode}] path={path or '?'} "
                f"route={'OK' if route_ok else 'FAIL'} gaps={len(gaps)} {elapsed}s",
                flush=True,
            )

    ladder = validator.evaluate_mode_ladder(results)
    payload = {
        "results": results,
        "ladderGaps": ladder,
        "summary": {
            "total": len(results),
            "routeFailures": sum(1 for r in results if not r["routeOk"]),
            "qualityGapCount": sum(len(r["qualityGaps"]) for r in results) + len(ladder),
        },
    }
    out = os.path.join(os.path.dirname(__file__), "eval_response_modes_product_routes_report.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(json.dumps(payload["summary"], ensure_ascii=False))
    print(f"Report: {out}")
    return 0 if payload["summary"]["routeFailures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
