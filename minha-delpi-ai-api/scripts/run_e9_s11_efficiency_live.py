#!/usr/bin/env python3
"""E9.S11 — medir eficiência live no stack openai_compatible (Kimi/OpenRouter).

Uso:
  cd minha-delpi-ai-api
  set -a && source ../infra/.env && set +a
  PYTHONPATH=. .venv/bin/python -u scripts/run_e9_s11_efficiency_live.py

Não usa Ollama. Exige LLM_PROVIDER=openai_compatible + KIMI_* no runtime do API.
"""

from __future__ import annotations
from smoke_credentials import require_smoke_credentials

import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.domain.services.chat_r8_latency_threshold_service import (  # noqa: E402
    ChatR8LatencyThresholdService,
)
_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME, _PASSWORD = require_smoke_credentials()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_RESPONSE_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip()
_TRIALS = max(3, int(os.environ.get("E9_S11_TRIALS", "5")))

_PROBES = [
    {"id": "smalltalk", "message": "ola, tudo bem?"},
    {"id": "stock", "message": "qual o estoque do produto 10080022?"},
    {"id": "stock_sibling", "message": "e o saldo do 10080001?"},
]


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
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
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
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("token ausente")
    return str(token)


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items") or agents.get("data") or []
    if not items:
        raise RuntimeError("nenhum agente")
    return str(items[0].get("id") or items[0].get("agentId"))


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"agentId": agent_id, "title": "e9-s11-efficiency"},
    )
    sid = payload.get("id") or payload.get("sessionId")
    if not sid:
        raise RuntimeError(f"session sem id: {payload!r}")
    return str(sid)


def _send(token: str, session_id: str, message: str) -> dict:
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "responseMode": _RESPONSE_MODE},
        timeout=360,
    )


def _percentile(sorted_values: list[float], pct: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return float(sorted_values[f])
    return float(sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f))


def _extract_usage(response: dict) -> dict[str, Any]:
    assistant = response.get("assistantMessage") or response.get("message") or response
    admin = assistant.get("adminDebug") or response.get("adminDebug") or {}
    if not isinstance(admin, dict):
        admin = {}
    meta = assistant.get("metadata") or response.get("metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    llm = admin.get("llm") if isinstance(admin.get("llm"), dict) else {}
    usage = llm.get("usage") if isinstance(llm.get("usage"), dict) else {}
    metrics = admin.get("metrics") if isinstance(admin.get("metrics"), dict) else {}
    timings = {}
    intel = admin.get("intelligence") if isinstance(admin.get("intelligence"), dict) else {}
    if isinstance(intel.get("timings"), dict):
        timings = intel["timings"]
    elif isinstance(admin.get("timings"), dict):
        timings = admin["timings"]
    provider = (
        llm.get("provider")
        or admin.get("provider")
        or meta.get("llmProvider")
        or os.environ.get("LLM_PROVIDER")
        or "unknown"
    )

    def _token(*keys: str) -> int | float | None:
        for source in (usage, metrics, meta.get("metrics") if isinstance(meta.get("metrics"), dict) else {}):
            if not isinstance(source, dict):
                continue
            for key in keys:
                value = source.get(key)
                if isinstance(value, (int, float)):
                    return value
        return None

    return {
        "provider": provider,
        "promptTokens": _token("promptTokens", "promptTokensEstimated", "prompt_tokens"),
        "completionTokens": _token(
            "completionTokens", "completionTokensEstimated", "completion_tokens"
        ),
        "totalTokens": _token("totalTokens", "totalTokensEstimated", "total_tokens"),
        "tokenSource": usage.get("tokenSource") or metrics.get("tokenSource") or "unknown",
        "llmMs": timings.get("llmMs") or usage.get("latencyMs") or metrics.get("latencyMs"),
        "totalMs": timings.get("totalMs"),
        "toolCalls": len(assistant.get("toolCalls") or response.get("toolCalls") or []),
        "answerChars": len(str(assistant.get("content") or response.get("answer") or "")),
    }


def main() -> int:
    print("run_e9_s11_efficiency_live")
    print(f"base={_BASE_URL} trials={_TRIALS} mode={_RESPONSE_MODE}")
    print(f"LLM_PROVIDER(env)={os.environ.get('LLM_PROVIDER', '')!r}")

    token = _fetch_token()
    agent_id = _first_agent(token)
    session_id = _create_session(token, agent_id)
    print(f"agent={agent_id} session={session_id}")

    trials: list[dict[str, Any]] = []
    errors: list[str] = []

    # Round-robin probes up to _TRIALS
    for i in range(_TRIALS):
        probe = _PROBES[i % len(_PROBES)]
        label = f"{probe['id']}#{i+1}"
        started = time.perf_counter()
        try:
            response = _send(token, session_id, probe["message"])
            wall_ms = int((time.perf_counter() - started) * 1000)
            usage = _extract_usage(response)
            row = {
                "id": label,
                "probeId": probe["id"],
                "ok": True,
                "wallMs": wall_ms,
                **usage,
            }
            trials.append(row)
            print(
                f"PASS  {label} wall={wall_ms}ms tools={usage.get('toolCalls')} "
                f"tokens={usage.get('totalTokens')} provider={usage.get('provider')}"
            )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:300]
            wall_ms = int((time.perf_counter() - started) * 1000)
            errors.append(f"{label}: HTTP {exc.code} {body}")
            trials.append({"id": label, "probeId": probe["id"], "ok": False, "wallMs": wall_ms})
            print(f"FAIL  {label} HTTP {exc.code} wall={wall_ms}ms")
        except Exception as exc:  # noqa: BLE001
            wall_ms = int((time.perf_counter() - started) * 1000)
            errors.append(f"{label}: {type(exc).__name__}: {exc}")
            trials.append({"id": label, "probeId": probe["id"], "ok": False, "wallMs": wall_ms})
            print(f"FAIL  {label} {type(exc).__name__} wall={wall_ms}ms")

    ok_walls = sorted(float(t["wallMs"]) for t in trials if t.get("ok") and t.get("wallMs") is not None)
    token_totals = [
        float(t["totalTokens"])
        for t in trials
        if t.get("ok") and isinstance(t.get("totalTokens"), (int, float))
    ]
    llm_ms = [
        float(t["llmMs"])
        for t in trials
        if t.get("ok") and isinstance(t.get("llmMs"), (int, float))
    ]
    providers = sorted(
        {str(t.get("provider") or "") for t in trials if t.get("ok") and t.get("provider")}
    )

    summary = {
        "schemaVersion": 1,
        "step": "E9.S11",
        "evaluatedAt": datetime.now(timezone.utc).isoformat(),
        "stack": {
            "expectedProvider": "openai_compatible",
            "observedProviders": providers,
            "modelEnv": os.environ.get("KIMI_MODEL") or os.environ.get("LLM_TEXT_MODEL") or "",
            "baseUrl": _BASE_URL,
            "responseMode": _RESPONSE_MODE,
            "trialsRequested": _TRIALS,
            "trialsOk": sum(1 for t in trials if t.get("ok")),
        },
        "latency": {
            "wallsMs": [int(v) for v in ok_walls],
            "p50Ms": _percentile(ok_walls, 50),
            "p95Ms": _percentile(ok_walls, 95),
            "avgMs": statistics.mean(ok_walls) if ok_walls else None,
            "minMs": min(ok_walls) if ok_walls else None,
            "maxMs": max(ok_walls) if ok_walls else None,
            "llmMsSample": llm_ms,
        },
        "tokens": {
            "totals": [int(v) for v in token_totals],
            "avgTotal": statistics.mean(token_totals) if token_totals else None,
            "p50Total": _percentile(sorted(token_totals), 50) if token_totals else None,
            "trialsWithTokens": len(token_totals),
            "status": "PASS" if token_totals else "PENDING",
            "sourceSample": sorted(
                {
                    str(t.get("tokenSource") or "")
                    for t in trials
                    if t.get("ok") and t.get("tokenSource")
                }
            ),
        },
        "errors": errors,
        "trials": trials,
        "decision": None,
    }

    # Gate R8 canônico (chat-ai-flow-families.md §12): P50/P95 ≤ alvo do modo.
    provider_for_gate = providers[0] if len(providers) == 1 else (",".join(providers) if providers else None)
    if any("ollama" in p.lower() for p in providers):
        provider_for_gate = next(p for p in providers if "ollama" in p.lower())
    llm_call_count = sum(
        1
        for t in trials
        if t.get("ok") and isinstance(t.get("llmMs"), (int, float))
    )
    tool_call_count = sum(int(t.get("toolCalls") or 0) for t in trials if t.get("ok"))
    token_avg = statistics.mean(token_totals) if token_totals else None

    gate = ChatR8LatencyThresholdService.evaluate(
        response_mode=_RESPONSE_MODE,
        p50_ms=summary["latency"]["p50Ms"],
        p95_ms=summary["latency"]["p95Ms"],
        provider=provider_for_gate,
        total_tokens=token_avg,
        llm_calls=llm_call_count,
        tool_calls=tool_call_count,
        trials_ok=int(summary["stack"]["trialsOk"]),
        min_trials_ok=3,
        require_tokens=True,
    )
    decision = gate.decision
    reason = gate.reason
    summary["decision"] = decision
    summary["decisionReason"] = reason
    summary["r8Gate"] = gate.as_dict()
    summary["efficiency"] = {
        "llmCalls": llm_call_count,
        "toolCalls": tool_call_count,
        "tokensAvgTotal": token_avg,
        "observedProviders": providers,
    }

    out_dir = (
        _ROOT
        / "docs/roadmap/llm-json-decoupling/evidence/e9-s11-efficiency-live-v1"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\n=== RESUMO ===")
    print(
        f"ok={summary['stack']['trialsOk']}/{_TRIALS} "
        f"mode={_RESPONSE_MODE} thresholdMs={gate.threshold_ms} "
        f"p50={summary['latency']['p50Ms']} p95={summary['latency']['p95Ms']} "
        f"providers={providers} llmCalls={llm_call_count} toolCalls={tool_call_count} "
        f"decision={decision}"
    )
    print(f"reason={reason}")
    print(f"evidence={out_dir / 'results.json'}")
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
