#!/usr/bin/env python3
"""Homologação Onda 1.10 — três casos anonimizados via api-delpi."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_h1_api_smoke import (  # noqa: E402
    _download_export,
    _png_bytes,
    _request,
    _upload_png,
    resolve_delpi_homologation_token,
)


def case_anon_01_rnc_8d(api: str, token: str) -> str:
    print("[ONDA1-ANON-01] NC externa crítica com relatório 8D…")
    created = _request(
        "POST",
        api,
        token=token,
        data={
            "title": "[ONDA1-ANON-01] NC cliente — 8D completo",
            "customer_name": "Cliente Alfa (fictício)",
            "product_code": "90000001",
            "reported_problem": "Dimensional fora de especificação.",
            "severity": "critical",
            "status": "triage",
            "branch_code": "01",
            "nonconformity_scope": "external",
            "source_type": "pdf",
            "source_reference": "rnc-anon-01.pdf",
            "customer_template": "rnc_8d",
            "client_nc_registry": "ANON-01-2026",
        },
    )
    assert created.get("success"), created
    plan_id = created["data"]["id"]

    _request(
        "PUT",
        f"{api}/{plan_id}/rnc-8d",
        token=token,
        data={
            "client_nc_registry": "ANON-01-2026",
            "reported_problem": "Dimensional fora de especificação.",
            "template_payload": {
                "containment": [{"area": "supplier", "action_plan": "Segregar lote"}],
            },
            "team_members": [{"member_name": "Coord. Qualidade", "is_leader": True}],
        },
    )
    xlsx = _download_export(f"{api}/{plan_id}/export/rnc-8d", token=token)
    assert len(xlsx) > 5_000, "export 8D muito pequeno"
    print(f"  OK plano {plan_id} + export {len(xlsx)} bytes")
    return plan_id


def case_anon_02_generic_external(api: str, token: str) -> str:
    print("[ONDA1-ANON-02] NC externa média — template genérico…")
    created = _request(
        "POST",
        api,
        token=token,
        data={
            "title": "[ONDA1-ANON-02] Reclamação cliente — genérico",
            "customer_name": "Cliente Beta (fictício)",
            "severity": "medium",
            "status": "triage",
            "branch_code": "02",
            "nonconformity_scope": "external",
            "source_type": "email",
            "source_reference": "msg-anon-02@cliente.fake",
            "customer_template": "generic",
            "reported_problem": "Atraso na resposta de NC anterior.",
        },
    )
    assert created.get("success"), created
    plan_id = created["data"]["id"]
    detail = _request("GET", f"{api}/{plan_id}", token=token)
    plan = detail["data"]["plan"]
    assert plan.get("source_type") == "email"
    assert plan.get("customer_template") in ("generic", None)
    print(f"  OK plano {plan_id}")
    return plan_id


def case_anon_03_internal(api: str, token: str) -> str:
    print("[ONDA1-ANON-03] NC interna — sem 8D…")
    created = _request(
        "POST",
        api,
        token=token,
        data={
            "title": "[ONDA1-ANON-03] Desvio interno de processo",
            "severity": "medium",
            "status": "triage",
            "branch_code": "01",
            "nonconformity_scope": "internal",
            "source_type": "manual_text",
            "department": "Montagem",
            "failure_mode": "falta_treinamento",
        },
    )
    assert created.get("success"), created
    plan_id = created["data"]["id"]
    actions = _request(
        "POST",
        f"{api}/{plan_id}/actions",
        token=token,
        data={
            "actions": [
                {
                    "action_type": "corrective",
                    "description": "Reciclar operadores (anon)",
                    "evidence_required": True,
                }
            ]
        },
    )
    action_id = actions["data"]["items"][0]["id"]
    _upload_png(
        f"{api}/{plan_id}/evidences",
        token=token,
        png_bytes=_png_bytes(),
        fields={
            "evidence_type": "image",
            "section": "general",
            "action_id": action_id,
            "description": "Lista de presença treinamento",
        },
    )
    print(f"  OK plano {plan_id} com evidência vinculada")
    return plan_id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost"))
    parser.add_argument("--token", default="")
    args = parser.parse_args()

    token = resolve_delpi_homologation_token(args.token)
    if not token:
        print("Defina TOKEN ou API_DELPI_INTERNAL_SERVICE_TOKEN", file=sys.stderr)
        return 1

    api = f"{args.base_url.rstrip('/')}/apps/api-delpi/quality/action-plans"
    ids = [
        case_anon_01_rnc_8d(api, token),
        case_anon_02_generic_external(api, token),
        case_anon_03_internal(api, token),
    ]
    print(f"\n[OK] Onda 1.10 — 3 casos anonimizados: {', '.join(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
