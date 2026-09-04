#!/usr/bin/env python3
"""Harness offline — baseline de inteligência conversacional (E0.S1).

Avalia, sem HTTP, decisões pré-LLM para um dataset de mensagens:
  - looks_like_product_search
  - missing_product_code (guard)
  - intent router decision/subIntent
  - expected vs actual (clarify_wrong / tool_path)

Uso:
  cd minha-delpi-ai-api && PYTHONPATH=. .venv/bin/python \\
    scripts/chat_intelligence_baseline_harness.py

Saída: docs/testing/evidence/chat-intelligence-baseline.json
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_operational_parameter.chat_operational_parameter_product_code_service import (
    ChatOperationalParameterProductCodeService,
)
from app.domain.services.chat_product_search_intent_service import (
    ChatProductSearchIntentService,
)

_FIXTURE = ROOT / "tests" / "fixtures" / "intelligence_baseline" / "routing_cases.json"
_OUT = ROOT / "docs" / "testing" / "evidence" / "chat-intelligence-baseline.json"


def _load_cases() -> list[dict]:
    raw = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return list(raw.get("cases") or [])


def _eval_case(case: dict) -> dict:
    message = str(case.get("message") or "")
    expected = case.get("expect") or {}

    looks_search = ChatProductSearchIntentService.looks_like_product_search(message)
    missing_code = ChatOperationalParameterProductCodeService.resolve_missing_product_code_answer(
        message
    )
    route = ChatIntentRouterService.classify(message)
    decision = str(getattr(route, "decision", None) or (route.get("decision") if isinstance(route, dict) else "") or "")
    sub = str(getattr(route, "sub_intent", None) or getattr(route, "subIntent", None) or "")
    if isinstance(route, dict):
        decision = str(route.get("decision") or route.get("intent") or decision)
        sub = str(route.get("subIntent") or route.get("sub_intent") or sub)

    actual = {
        "looksLikeProductSearch": looks_search,
        "missingProductCode": bool(missing_code),
        "missingProductCodePreview": (missing_code or "")[:120] or None,
        "intentDecision": decision,
        "intentSubIntent": sub,
    }

    errors: list[str] = []
    if "looksLikeProductSearch" in expected:
        if bool(expected["looksLikeProductSearch"]) != looks_search:
            errors.append("looksLikeProductSearch mismatch")
    if "missingProductCode" in expected:
        if bool(expected["missingProductCode"]) != bool(missing_code):
            errors.append("missingProductCode mismatch")
    if expected.get("forbidClarifyViaMissingCode") and missing_code:
        errors.append("unexpected missingProductCode clarify")
    if expected.get("requireProductSearchLook") and not looks_search:
        errors.append("expected product search look")
    if "intentSubIntent" in expected:
        if str(expected["intentSubIntent"]) != sub:
            errors.append(
                f"intentSubIntent mismatch expected={expected['intentSubIntent']!r} actual={sub!r}"
            )
    if "intentDecision" in expected:
        if str(expected["intentDecision"]) != decision:
            errors.append(
                f"intentDecision mismatch expected={expected['intentDecision']!r} actual={decision!r}"
            )

    return {
        "caseId": case.get("id"),
        "family": case.get("family"),
        "message": message,
        "expect": expected,
        "actual": actual,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def main() -> int:
    cases = _load_cases()
    results = [_eval_case(c) for c in cases]
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    # Métricas baseline (sem targets inventados)
    n = max(len(results), 1)
    unexpected_clarify = sum(
        1
        for r in results
        if r["actual"]["missingProductCode"]
        and (r["expect"] or {}).get("forbidClarifyViaMissingCode")
    )
    search_look_ok = sum(
        1
        for r in results
        if (r["expect"] or {}).get("requireProductSearchLook")
        and r["actual"]["looksLikeProductSearch"]
    )
    search_look_total = sum(
        1 for r in results if (r["expect"] or {}).get("requireProductSearchLook")
    )

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "harness": "chat_intelligence_baseline_harness",
        "fixture": str(_FIXTURE.relative_to(ROOT)),
        "summary": {
            "total": len(results),
            "pass": passed,
            "fail": failed,
            "metrics": {
                "unexpectedClarificationCount": unexpected_clarify,
                "productSearchLookHitRate": (
                    round(search_look_ok / search_look_total, 4) if search_look_total else None
                ),
                "offlinePassRate": round(passed / n, 4),
            },
            "notes": (
                "Baseline pré-cutover. Targets só após E0; fails esperados "
                "documentam o gap (search vs missing-code / clarify)."
            ),
        },
        "cases": results,
    }

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {_OUT} PASS={passed} FAIL={failed}")
    # Exit 0 sempre em E0 — baseline registra o estado, não bloqueia.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
