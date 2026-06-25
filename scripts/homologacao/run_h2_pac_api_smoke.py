#!/usr/bin/env python3
"""Smoke automatizado do cenário H2 — agente GPT via api-pac-quality (produção).

Espelha o fluxo do H1 na API PAC (PAC_QUALITY_API_KEY), valida paridade no plugin
via api-delpi (mesmo Postgres) e cobre search_similar_cases antes da criação do plano.
"""
from __future__ import annotations

import argparse
import base64
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

_FALLBACK_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

_PAC_API_URL_DEFAULT = "https://pac-api.minhadelpi.com.br"
_DELPI_BASE_DEFAULT = "http://localhost"


def _resolve_pac_api_key(explicit: str) -> str:
    if explicit.strip():
        return explicit.strip()
    env_key = (os.environ.get("PAC_QUALITY_API_KEY") or "").strip()
    if env_key:
        return env_key
    sibling_env = Path(__file__).resolve().parents[2].parent / "api-pac-quality" / ".env"
    if sibling_env.is_file():
        for line in sibling_env.read_text(encoding="utf-8").splitlines():
            if line.startswith("PAC_QUALITY_API_KEY="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    return ""


def _resolve_delpi_token(explicit: str) -> str:
    if explicit.strip():
        return explicit.strip()
    token = (os.environ.get("DELPI_TOKEN") or os.environ.get("TOKEN") or "").strip()
    if token:
        return token
    infra_env = Path(__file__).resolve().parents[2] / "infra" / ".env"
    if infra_env.is_file():
        for line in infra_env.read_text(encoding="utf-8").splitlines():
            if line.startswith("API_DELPI_INTERNAL_SERVICE_TOKEN="):
                return line.split("=", 1)[1].strip()
    return ""


def _pac_request(
    method: str,
    url: str,
    *,
    api_key: str,
    data: dict | None = None,
) -> dict:
    body = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "Delpi-PAC-Homologation/1.0",
    }
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc
    if not raw:
        return {}
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("success") is False:
        raise RuntimeError(f"{method} {url} -> API error: {payload}")
    return payload


def _delpi_request(method: str, url: str, *, token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Delpi-Caller-App": "quality-action-plans",
        "Accept": "application/json",
    }
    request = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc


def _upload_png(url: str, *, api_key: str, png_bytes: bytes, fields: dict[str, str]) -> dict:
    boundary = "----delpi-pac-h2-smoke"
    parts: list[bytes] = []
    for key, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        b'Content-Disposition: form-data; name="file"; filename="h2-smoke.png"\r\n'
        b"Content-Type: image/png\r\n\r\n"
    )
    parts.append(png_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Delpi-PAC-Homologation/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST evidence -> HTTP {exc.code}: {detail}") from exc


def _download_export(url: str, *, api_key: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "User-Agent": "Delpi-PAC-Homologation/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GET export -> HTTP {exc.code}: {detail}") from exc


def _png_bytes() -> bytes:
    if Image is not None:
        buffer = io.BytesIO()
        Image.new("RGB", (16, 16), color=(80, 120, 200)).save(buffer, format="PNG")
        return buffer.getvalue()
    return _FALLBACK_PNG


def _unwrap_data(response: dict) -> dict:
    data = response.get("data")
    if isinstance(data, dict):
        return data
    if data is not None:
        return {"value": data}
    return response


def run_h2_smoke(
    pac_base: str,
    api_key: str,
    *,
    delpi_base: str,
    delpi_token: str,
) -> str:
    pac_api = f"{pac_base.rstrip('/')}/quality/action-plans"
    intel = f"{pac_base.rstrip('/')}/quality/action-plans/intelligence"

    print("[H2] search_similar_cases (inteligência histórica)…")
    similar = _pac_request(
        "POST",
        f"{intel}/similar-cases",
        api_key=api_key,
        data={
            "problem_description": "Trinca superficial em chicote elétrico — homologação H2",
            "product_code": "14297268",
            "customer_name": "Cliente Homologação Anon",
            "symptoms": ["trinca", "aparência"],
            "branch_code": "01",
            "failure_mode": "trinca",
        },
    )
    similar_data = _unwrap_data(similar)
    cases = similar_data.get("similar_cases") or []
    print(f"  OK {len(cases)} casos similares retornados")

    print("[H2] Criar plano via API PAC…")
    created = _pac_request(
        "POST",
        pac_api,
        api_key=api_key,
        data={
            "title": "[H2-SMOKE] NC externa — fluxo agente GPT",
            "customer_name": "Cliente Homologação Anon",
            "product_code": "14297268",
            "product_description": "CHICOTE TESTE HOMOLOG H2",
            "reported_problem": "Defeito visual (smoke agente GPT).",
            "severity": "critical",
            "status": "triage",
            "branch_code": "01",
            "nonconformity_scope": "external",
            "source_type": "manual_text",
            "customer_template": "rnc_8d",
            "client_nc_registry": "H2-SMOKE-001",
        },
    )
    plan = _unwrap_data(created)
    plan_id = str(plan["id"])
    code = plan.get("code", plan_id)
    print(f"  OK plano {code} ({plan_id})")

    print("[H2] Verificar plano visível no plugin (api-delpi)…")
    delpi_detail = _delpi_request(
        "GET",
        f"{delpi_base.rstrip('/')}/apps/api-delpi/quality/action-plans/{plan_id}",
        token=delpi_token,
    )
    if not delpi_detail.get("success"):
        raise RuntimeError(f"Plano não visível na api-delpi: {delpi_detail}")
    delpi_plan = (delpi_detail.get("data") or {}).get("plan") or {}
    assert delpi_plan.get("code") == code, delpi_plan
    print(f"  OK paridade plugin — {delpi_plan.get('code')}")

    print("[H2] Ishikawa + 5 Porquês…")
    _pac_request(
        "PUT",
        f"{pac_api}/{plan_id}/ishikawa",
        api_key=api_key,
        data={
            "machine": "Equipamento — hipótese H2",
            "material": "Matéria-prima — hipótese H2",
        },
    )
    _pac_request(
        "PUT",
        f"{pac_api}/{plan_id}/five-whys",
        api_key=api_key,
        data={
            "why_1": "Falha no processo (H2)",
            "why_2": "Parâmetro incorreto (H2)",
            "detection_why_1": "Inspeção incompleta (H2)",
            "root_cause": "Causa raiz fictícia H2",
            "confidence_level": "medium",
        },
    )
    print("  OK análises")

    print("[H2] Ações corretiva + contenção…")
    actions_resp = _pac_request(
        "POST",
        f"{pac_api}/{plan_id}/actions",
        api_key=api_key,
        data={
            "actions": [
                {
                    "action_type": "containment",
                    "description": "Segregar lote (H2 smoke)",
                    "responsible_name": "Analista Homolog",
                },
                {
                    "action_type": "corrective",
                    "description": "Ajustar parâmetro (H2 smoke)",
                    "responsible_name": "Analista Homolog",
                    "cause_track": "occurrence",
                },
            ]
        },
    )
    action_items = (_unwrap_data(actions_resp).get("items") or []) or (
        actions_resp.get("data") if isinstance(actions_resp.get("data"), list) else []
    )
    corrective_id = next(
        (a["id"] for a in action_items if a.get("action_type") == "corrective"),
        None,
    )
    print(f"  OK ações (corretiva={corrective_id})")

    print("[H2] Evidência via API PAC…")
    png = _png_bytes()
    evidence_fields = {
        "evidence_type": "image",
        "section": "corrective",
        "description": "Evidência H2 smoke",
        "knowledge_visible": "true",
    }
    if corrective_id:
        evidence_fields["action_id"] = corrective_id
    evidence_resp = _upload_png(
        f"{pac_api}/{plan_id}/evidences",
        api_key=api_key,
        png_bytes=png,
        fields=evidence_fields,
    )
    if evidence_resp.get("success") is False:
        raise RuntimeError(f"Falha ao anexar evidência: {evidence_resp}")

    delpi_evidences = _delpi_request(
        "GET",
        f"{delpi_base.rstrip('/')}/apps/api-delpi/quality/action-plans/{plan_id}/evidences",
        token=delpi_token,
    )
    ev_count = len((delpi_evidences.get("data") or []))
    assert ev_count >= 1, delpi_evidences
    print(f"  OK evidência no plugin ({ev_count} itens)")

    print("[H2] Relatório 8D + export Excel…")
    _pac_request(
        "PUT",
        f"{pac_api}/{plan_id}/rnc-8d",
        api_key=api_key,
        data={
            "client_nc_registry": "H2-SMOKE-001",
            "customer_name": "Cliente Homologação Anon",
            "product_code": "14297268",
            "reported_problem": "Defeito visual (H2)",
            "template_payload": {
                "nc_description": {
                    "characteristic": "Aparência",
                    "specified": "Sem trinca",
                    "verified": "Trinca superficial",
                }
            },
        },
    )
    xlsx = _download_export(f"{pac_api}/{plan_id}/export/rnc-8d", api_key=api_key)
    assert xlsx[:2] == b"PK", "export não é xlsx válido"
    assert len(xlsx) > 10_000, f"export pequeno ({len(xlsx)} bytes)"
    print(f"  OK export {len(xlsx)} bytes")

    print(f"\n[OK] H2 smoke concluído — plano {code}")
    print(f"     Plugin: {delpi_base}/apps/quality-action-plans/plans/{plan_id}")
    print(f"     PLAN_ID={plan_id}")
    return plan_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke H2 PAC (agente GPT) em produção")
    parser.add_argument("--pac-url", default=os.environ.get("PAC_API_URL", _PAC_API_URL_DEFAULT))
    parser.add_argument("--api-key", default="")
    parser.add_argument("--delpi-base-url", default=os.environ.get("DELPI_BASE_URL", _DELPI_BASE_DEFAULT))
    parser.add_argument("--delpi-token", default="")
    args = parser.parse_args()

    api_key = _resolve_pac_api_key(args.api_key)
    if not api_key:
        print(
            "Defina PAC_QUALITY_API_KEY (env ou api-pac-quality/.env).",
            file=sys.stderr,
        )
        return 1

    delpi_token = _resolve_delpi_token(args.delpi_token)
    if not delpi_token:
        print(
            "Defina DELPI_TOKEN / TOKEN para validar visibilidade no plugin (api-delpi).",
            file=sys.stderr,
        )
        return 1

    try:
        run_h2_smoke(
            args.pac_url,
            api_key,
            delpi_base=args.delpi_base_url,
            delpi_token=delpi_token,
        )
        return 0
    except Exception as exc:
        print(f"[FALHA] {exc}", file=sys.stderr)
        print(
            "\nDica: se HTTP 404 em rnc-8d/evidences, faça deploy da api-pac-quality "
            "(docker compose up -d --build no srv-api) e rode check-pac-api-server.sh.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
