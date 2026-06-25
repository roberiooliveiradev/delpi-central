#!/usr/bin/env python3
"""Smoke automatizado do cenário H1 (API api-delpi) — Onda 1 PAC Qualidade."""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[misc, assignment]


def _request(
    method: str,
    url: str,
    *,
    token: str,
    data: dict | None = None,
    headers: dict[str, str] | None = None,
) -> dict:
    body = None
    req_headers = {
        "Authorization": f"Bearer {token}",
        "X-Delpi-Caller-App": "quality-action-plans",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _upload_png(url: str, *, token: str, png_bytes: bytes, fields: dict[str, str]) -> dict:
    boundary = "----delpi-pac-h1-smoke"
    parts: list[bytes] = []
    for key, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        b'Content-Disposition: form-data; name="file"; filename="h1-smoke.png"\r\n'
        b"Content-Type: image/png\r\n\r\n"
    )
    parts.append(png_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Delpi-Caller-App": "quality-action-plans",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST evidence -> HTTP {exc.code}: {detail}") from exc


def _download_export(url: str, *, token: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Delpi-Caller-App": "quality-action-plans",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GET export -> HTTP {exc.code}: {detail}") from exc


def _png_bytes() -> bytes:
    if Image is None:
        raise RuntimeError("Instale Pillow: pip install Pillow")
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16), color=(180, 50, 50)).save(buffer, format="PNG")
    return buffer.getvalue()


def run_smoke(base_url: str, token: str) -> str:
    api = f"{base_url.rstrip('/')}/apps/api-delpi/quality/action-plans"
    print("[H1] Criar plano NC externa crítica…")
    created = _request(
        "POST",
        api,
        token=token,
        data={
            "title": "[H1-SMOKE] NC externa — homologação automatizada",
            "customer_name": "Cliente Homologação Anon",
            "product_code": "14297268",
            "product_description": "CHICOTE TESTE HOMOLOG",
            "reported_problem": "Defeito visual em amostra de homologação (dado fictício).",
            "severity": "critical",
            "status": "triage",
            "branch_code": "01",
            "nonconformity_scope": "external",
            "source_type": "manual_text",
        },
    )
    assert created.get("success"), created
    plan = created["data"]
    plan_id = plan["id"]
    code = plan.get("code", plan_id)
    print(f"  OK plano {code} ({plan_id})")

    print("[H1] Ativar template 8D e registro cliente…")
    updated = _request(
        "PATCH",
        f"{api}/{plan_id}",
        token=token,
        data={
            "customer_template": "rnc_8d",
            "client_nc_registry": "H1-SMOKE-001",
            "customer_contact": "homolog@delpi.local",
        },
    )
    assert updated.get("success"), updated
    plan_data = updated["data"]
    template = plan_data.get("customer_template") or (plan_data.get("plan") or {}).get(
        "customer_template"
    )
    assert template == "rnc_8d", plan_data
    print("  OK rnc_8d + registro")

    print("[H1] Ishikawa + 5 Porquês…")
    _request(
        "PUT",
        f"{api}/{plan_id}/ishikawa",
        token=token,
        data={
            "machine": "Equipamento de corte — hipótese teste",
            "material": "Matéria-prima — hipótese teste",
            "method_process": "Sequência operacional — hipótese teste",
        },
    )
    _request(
        "PUT",
        f"{api}/{plan_id}/five-whys",
        token=token,
        data={
            "why_1": "Falha no processo (smoke)",
            "why_2": "Parâmetro incorreto (smoke)",
            "detection_why_1": "Inspeção não cobriu ponto (smoke)",
            "detection_why_2": "Plano de controle desatualizado (smoke)",
            "root_cause": "Causa raiz fictícia para homologação",
            "confidence_level": "medium",
        },
    )
    print("  OK análises")

    print("[H1] Ações (contenção + corretiva)…")
    actions_resp = _request(
        "POST",
        f"{api}/{plan_id}/actions",
        token=token,
        data={
            "actions": [
                {
                    "action_type": "containment",
                    "description": "Isolar lote afetado (smoke)",
                    "responsible_name": "Analista Homolog",
                    "department": "Qualidade",
                },
                {
                    "action_type": "corrective",
                    "description": "Ajustar parâmetro de processo (smoke)",
                    "responsible_name": "Analista Homolog",
                    "cause_track": "occurrence",
                },
            ]
        },
    )
    assert actions_resp.get("success"), actions_resp
    action_items = actions_resp["data"].get("items") or []
    corrective_id = next(
        (a["id"] for a in action_items if a.get("action_type") == "corrective"),
        None,
    )
    print(f"  OK ações (corretiva={corrective_id})")

    print("[H1] Relatório 8D (payload mínimo)…")
    _request(
        "PUT",
        f"{api}/{plan_id}/rnc-8d",
        token=token,
        data={
            "client_nc_registry": "H1-SMOKE-001",
            "customer_name": "Cliente Homologação Anon",
            "product_code": "14297268",
            "product_description": "CHICOTE TESTE HOMOLOG",
            "reported_problem": "Defeito visual (smoke)",
            "template_payload": {
                "purchase_order": "5500000000",
                "disposition": "Rejeitado",
                "nc_description": {
                    "characteristic": "Aparência",
                    "specified": "Sem trinca",
                    "verified": "Trinca superficial",
                },
                "containment": [
                    {
                        "area": "supplier",
                        "quantity": "10",
                        "action_plan": "Segregar lote",
                        "responsible": "Qualidade",
                    }
                ],
            },
            "team_members": [
                {"member_name": "Líder Homolog", "department": "Qualidade", "is_leader": True},
            ],
        },
    )
    print("  OK 8D")

    png = _png_bytes()
    print("[H1] Evidências (imagem geral + imagem vinculada à ação)…")
    _upload_png(
        f"{api}/{plan_id}/evidences",
        token=token,
        png_bytes=png,
        fields={
            "evidence_type": "image",
            "section": "attachments",
            "description": "Evidência smoke geral",
            "knowledge_visible": "true",
        },
    )
    evidence_fields = {
        "evidence_type": "image",
        "section": "corrective",
        "description": "Evidência smoke vinculada à corretiva",
        "knowledge_visible": "true",
    }
    if corrective_id:
        evidence_fields["action_id"] = corrective_id
    _upload_png(
        f"{api}/{plan_id}/evidences",
        token=token,
        png_bytes=png,
        fields=evidence_fields,
    )
    listed = _request("GET", f"{api}/{plan_id}/evidences", token=token)
    assert listed.get("success"), listed
    assert len(listed["data"]) >= 2, listed
    print(f"  OK {len(listed['data'])} evidências")

    print("[H1] Export Excel 8D…")
    xlsx = _download_export(f"{api}/{plan_id}/export/rnc-8d", token=token)
    assert xlsx[:2] == b"PK", "export não é xlsx válido"
    assert len(xlsx) > 10_000, f"export pequeno demais ({len(xlsx)} bytes)"
    print(f"  OK export {len(xlsx)} bytes")

    print("[H1] Status → waiting_validation…")
    _request(
        "PATCH",
        f"{api}/{plan_id}/status",
        token=token,
        data={"status": "waiting_validation", "comment": "H1 smoke automatizado"},
    )
    print("  OK status")

    print(f"\n[OK] H1 smoke concluído — plano {code}")
    print(f"     Detalhe: {base_url}/apps/quality-action-plans/plans/{plan_id}")
    print(f"     PLAN_ID={plan_id}")
    return plan_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke H1 PAC via api-delpi")
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost"))
    parser.add_argument("--token", default=os.environ.get("TOKEN", ""))
    args = parser.parse_args()
    if not args.token:
        print("Defina TOKEN (JWT com quality-action-plans.read/write).", file=sys.stderr)
        return 1
    try:
        run_smoke(args.base_url, args.token)
        return 0
    except Exception as exc:
        print(f"[FALHA] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
