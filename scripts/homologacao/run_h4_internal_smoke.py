#!/usr/bin/env python3
"""Smoke H4 — plano interno sem template 8D (api-delpi, Onda 1 recomendado)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Importa helpers do smoke H1 (mesmo diretório)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_h1_api_smoke import _request, resolve_delpi_homologation_token


def run_h4(base_url: str, token: str) -> str:
    api = f"{base_url.rstrip('/')}/apps/api-delpi/quality/action-plans"

    print("[H4] Criar plano interno (sem 8D)…")
    created = _request(
        "POST",
        api,
        token=token,
        data={
            "title": "[H4-SMOKE] NC interna — processo",
            "reported_problem": "Desvio de procedimento interno (fictício).",
            "severity": "medium",
            "status": "triage",
            "branch_code": "01",
            "nonconformity_scope": "internal",
            "department": "Produção",
            "failure_mode": "desvio_procedimento",
            "source_type": "manual_text",
        },
    )
    assert created.get("success"), created
    plan = created["data"]
    plan_id = plan["id"]
    code = plan.get("code", plan_id)
    template = plan.get("customer_template")
    assert template in (None, "generic"), f"esperado sem rnc_8d, obteve {template!r}"
    print(f"  OK plano {code} — template={template or 'generic'}")

    print("[H4] Ishikawa mínimo + ação corretiva…")
    _request(
        "PUT",
        f"{api}/{plan_id}/ishikawa",
        token=token,
        data={"method_process": "Procedimento não seguido (smoke H4)"},
    )
    _request(
        "POST",
        f"{api}/{plan_id}/actions",
        token=token,
        data={
            "actions": [
                {
                    "action_type": "corrective",
                    "description": "Revisar procedimento com equipe (H4)",
                    "responsible_name": "Analista Homolog",
                }
            ]
        },
    )
    print("  OK análises e ação")

    detail = _request("GET", f"{api}/{plan_id}", token=token)
    assert detail.get("success"), detail
    plan_row = detail["data"].get("plan") or {}
    assert plan_row.get("nonconformity_scope") == "internal"
    print("  OK detalhe confirma escopo internal")

    print(f"\n[OK] H4 smoke concluído — plano {code}")
    print(f"     PLAN_ID={plan_id}")
    return plan_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke H4 — plano interno api-delpi")
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost"))
    parser.add_argument("--token", default="")
    args = parser.parse_args()
    token = resolve_delpi_homologation_token(args.token)
    if not token:
        print("Defina TOKEN ou API_DELPI_INTERNAL_SERVICE_TOKEN.", file=sys.stderr)
        return 1
    try:
        run_h4(args.base_url, token)
        return 0
    except Exception as exc:
        print(f"[FALHA] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
