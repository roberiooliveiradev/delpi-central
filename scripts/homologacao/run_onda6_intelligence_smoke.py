#!/usr/bin/env python3
"""Smoke Onda 6 local — api-delpi (grafo, recorrência na abertura, tags de evidência)."""
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

INTEL = f"{BASE}/apps/api-delpi/quality/action-plans/intelligence"
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


def main() -> int:
    graph = _call("GET", f"{INTEL}/knowledge-graph?limit=10")
    assert graph.get("success"), graph
    data = graph.get("data") or {}
    assert "nodes" in data and "edges" in data and "summary" in data, data
    print(f"OK knowledge-graph nodes={data['summary'].get('node_count')} edges={data['summary'].get('edge_count')}")

    recurrence = _call(
        "POST",
        f"{INTEL}/recurrence-opening-assessment",
        {
            "problem_description": "Oxidação superficial em cabo após banho químico",
            "product_code": "90110001",
            "failure_mode": "oxidação",
            "branch_code": "01",
        },
    )
    assert recurrence.get("success"), recurrence
    rec_data = recurrence.get("data") or {}
    assert "recurrence_score" in rec_data and "alert_level" in rec_data, rec_data
    print(f"OK recurrence-opening alert_level={rec_data.get('alert_level')}")

    tags = _call(
        "POST",
        f"{INTEL}/suggest-evidence-tags",
        {
            "ocr_text": "NC 14297 trinca solda MIG cabo 90110001",
            "file_name": "foto_nc.jpg",
        },
    )
    assert tags.get("success"), tags
    tag_data = tags.get("data") or {}
    assert "suggested_tags" in tag_data, tag_data
    print(f"OK suggest-evidence-tags count={len(tag_data.get('suggested_tags') or [])}")

    print("Onda 6 intelligence smoke OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FALHA: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
