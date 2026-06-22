#!/usr/bin/env python3
"""Fluxo real: programação hoje → escolhe PA 9026 → perguntas fabril/MP/custo × 3 modos."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
API_PREFIX = os.environ.get("SMOKE_API_PREFIX", "/apps/api-delpi").strip()
PAUSE = float(os.environ.get("SMOKE_PAUSE_SECONDS", "1"))

FOLLOW_UPS = [
    {
        "id": "factory_broad",
        "template": "Qual o status completo na fábrica do produto {code} hoje?",
        "expectedPath": "/factory-status",
    },
    {
        "id": "production_granular",
        "template": "O produto {code} já começou a produzir? Tem apontamento na OP?",
        "expectedPath": "/production-status",
    },
    {
        "id": "shipping_granular",
        "template": "Quanto do produto {code} já foi liberado para expedição hoje?",
        "expectedPath": "/shipping-status",
    },
    {
        "id": "exclusivity",
        "template": "Quais matérias-primas exclusivas existem na estrutura do produto {code}?",
        "expectedPath": "/structure/exclusivity",
    },
    {
        "id": "mp_from_structure",
        "template": "Análise de preço da matéria-prima 10080001",
        "expectedPath": "/raw-material-price-intelligence",
        "fixed": True,
    },
    {
        "id": "cost_pareto",
        "template": "Quais materiais mais impactam o custo do PA {code}?",
        "expectedPath": "/cost-impact-simulation",
    },
    {
        "id": "cost_sim_10",
        "template": "Simule aumento de 10% nos materiais do produto {code}",
        "expectedPath": "/cost-impact-simulation",
    },
]

MODES = ("fast", "normal", "thinker")
_CODE_RE = re.compile(r"\b9026\d{4}\b")


def _token() -> str:
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


def _req(method: str, url: str, *, token: str, body: dict | None = None, timeout: int = 600) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode()
        return json.loads(raw) if raw else {}


def _agent_id(token: str) -> str:
    agents = _req("GET", f"{BASE}{PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    return str(next(a["id"] for a in items if a.get("enabled")))


def _session(token: str, agent_id: str, title: str) -> str:
    payload = _req(
        "POST",
        f"{BASE}{PREFIX}/sessions",
        token=token,
        body={"title": title, "agentId": agent_id},
    )
    return str(payload["id"])


def _send(
    token: str,
    session_id: str,
    agent_id: str,
    message: str,
    *,
    response_mode: str | None = None,
) -> tuple[dict, float, dict]:
    body: dict = {"message": message, "agentId": agent_id}

    if response_mode:
        body["responseMode"] = response_mode

    started = time.perf_counter()
    _req(
        "POST",
        f"{BASE}{PREFIX}/sessions/{session_id}/messages",
        token=token,
        body=body,
    )
    elapsed = round(time.perf_counter() - started, 1)
    messages = _req("GET", f"{BASE}{PREFIX}/sessions/{session_id}/messages", token=token)
    items = messages if isinstance(messages, list) else messages.get("items", [])
    assistant = next(m for m in reversed(items) if m.get("role") == "assistant")
    return assistant, elapsed, assistant.get("metadata") or {}


def _action_path(metadata: dict) -> str:
    for call in metadata.get("toolCalls") or []:
        if str(call.get("name") or "") != "execute_external_action":
            continue

        path = str((call.get("metadata") or {}).get("path") or "")

        if path:
            return path

    return ""


def _extract_codes(text: str) -> list[str]:
    return sorted(set(_CODE_RE.findall(text or "")))


def _schedule_today_from_api(token: str) -> list[str]:
    today = date.today().isoformat()
    url = f"{BASE}{API_PREFIX}/production/schedule/today?reference_date={today}"
    payload = _req("GET", url, token=token, timeout=120)
    root = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    items = root.get("items") if isinstance(root, dict) else []

    codes: list[str] = []

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue

            for key in ("productCode", "code", "product_code", "paCode"):
                value = str(item.get(key) or "").strip()

                if value.startswith("9026") and len(value) >= 8:
                    codes.append(value[:8])
                    break

    return sorted(set(codes))


def _pick_code(chat_codes: list[str], api_codes: list[str]) -> str | None:
    for pool in (chat_codes, api_codes):
        for code in pool:
            if code.startswith("9026"):
                return code

    return None


def main() -> int:
    token = _token()
    agent_id = _agent_id(token)
    report: dict = {
        "date": date.today().isoformat(),
        "steps": [],
        "followUps": [],
    }

    print("=== 1) Programação de hoje ===")
    session_id = _session(token, agent_id, "Eval programação hoje")
    assistant, elapsed, metadata = _send(
        token,
        session_id,
        agent_id,
        "Quais produtos estão programados para produzir hoje?",
        response_mode="normal",
    )
    content = str(assistant.get("content") or "")
    path = _action_path(metadata)
    chat_codes = _extract_codes(content)
    api_codes = _schedule_today_from_api(token)
    chosen = _pick_code(chat_codes, api_codes)

    report["steps"].append(
        {
            "question": "Quais produtos estão programados para produzir hoje?",
            "path": path,
            "elapsedSec": elapsed,
            "codesInChat": chat_codes[:20],
            "codesFromApi": api_codes[:20],
            "chosenCode": chosen,
            "contentPreview": content[:800],
        }
    )

    print(f"path={path or '?'} elapsed={elapsed}s")
    print(f"códigos no chat: {chat_codes[:10]}")
    print(f"códigos API: {api_codes[:10]}")
    print(f"escolhido: {chosen}")

    if not chosen:
        print("Nenhum PA 9026 encontrado — abortando.", file=sys.stderr)
        out = os.path.join(os.path.dirname(__file__), "eval_real_product_flow_report.json")
        with open(out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        return 1

    print(f"\n=== 2) Perguntas sobre PA {chosen} (3 modos) ===")

    for spec in FOLLOW_UPS:
        message = spec["template"] if spec.get("fixed") else spec["template"].format(code=chosen)

        for mode in MODES:
            time.sleep(PAUSE)
            sid = _session(token, agent_id, f"{spec['id']} {mode}")
            assistant, elapsed, metadata = _send(
                token,
                sid,
                agent_id,
                message,
                response_mode=mode,
            )
            content = str(assistant.get("content") or "")
            path = _action_path(metadata)
            pipeline = (metadata.get("intelligence") or {}).get("pipeline") or {}
            route_ok = spec["expectedPath"] in path
            entry = {
                "scenarioId": spec["id"],
                "mode": mode,
                "message": message,
                "expectedPath": spec["expectedPath"],
                "actualPath": path,
                "routeOk": route_ok,
                "elapsedSec": elapsed,
                "chars": len(content),
                "directResponse": pipeline.get("directResponse"),
                "responseModeEffect": pipeline.get("responseModeEffect"),
                "contentPreview": content[:600],
                "dataAnswerPreview": str(metadata.get("dataAnswer") or "")[:300],
            }
            report["followUps"].append(entry)
            status = "OK" if route_ok else "FAIL"
            print(
                f"{status} {spec['id']} [{mode}] path={path or '?'} "
                f"{elapsed}s chars={len(content)}",
                flush=True,
            )

    route_failures = sum(1 for item in report["followUps"] if not item["routeOk"])
    report["summary"] = {
        "chosenCode": chosen,
        "followUpTotal": len(report["followUps"]),
        "routeFailures": route_failures,
    }

    out = os.path.join(os.path.dirname(__file__), "eval_real_product_flow_report.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print(f"\nResumo: PA={chosen} falhas_rota={route_failures}/{len(report['followUps'])}")
    print(f"Report: {out}")
    return 0 if route_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
