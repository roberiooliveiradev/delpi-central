#!/usr/bin/env python3
"""Smoke Onda 2 local — api-delpi (recorrência + padrões de solução)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost").rstrip("/")
TOKEN = os.environ.get("TOKEN") or os.environ.get("DELPI_TOKEN")
if not TOKEN:
    env_path = os.path.join(os.path.dirname(__file__), "../../infra/.env")
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("API_DELPI_INTERNAL_SERVICE_TOKEN="):
                    TOKEN = line.strip().split("=", 1)[1]
                    break

if not TOKEN:
    print("Defina TOKEN ou API_DELPI_INTERNAL_SERVICE_TOKEN em infra/.env", file=sys.stderr)
    sys.exit(1)

API = f"{BASE}/apps/api-delpi/quality/action-plans"
SOLUTIONS = f"{BASE}/apps/api-delpi/quality/solution-patterns"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "X-Delpi-Caller-App": "quality-action-plans",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def _call(method: str, url: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> {exc.code}: {detail}") from exc


def _create_plan(title: str, *, product: str, failure: str) -> str:
    body = _call(
        "POST",
        API,
        {
            "title": title,
            "branch_code": "01",
            "nonconformity_scope": "external",
            "severity": "medium",
            "status": "triage",
            "product_code": product,
            "failure_mode": failure,
            "problem_category": "material",
        },
    )
    assert body.get("success"), body
    plan_id = body["data"]["id"]
    print(f"OK plano {body['data'].get('code')} ({plan_id})")
    return plan_id


def main() -> int:
    product = "H5-SMOKE-PROD"
    failure = "oxidacao superficial"

    _create_plan("[H5-SMOKE-A] Recorrência teste", product=product, failure=failure)
    _create_plan("[H5-SMOKE-B] Recorrência teste", product=product, failure=failure)

    recurrence = _call("GET", f"{API}/recurrence?min_plans=2&page_size=50")
    assert recurrence.get("success"), recurrence
    items = recurrence.get("data", {}).get("items") or []
    match = next(
        (
            item
            for item in items
            if item.get("product_code") == product and item.get("failure_mode") == failure
        ),
        None,
    )
    assert match and match.get("total_plans", 0) >= 2, recurrence
    print(f"OK H5 recorrência total={match['total_plans']}")

    solutions = _call("GET", f"{SOLUTIONS}?page_size=10")
    assert solutions.get("success"), solutions
    assert "items" in solutions.get("data", {}), solutions
    print(f"OK listagem padrões ({solutions['data']['pagination'].get('total', 0)} itens)")

    print("[OK] run_onda2_local_smoke.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
