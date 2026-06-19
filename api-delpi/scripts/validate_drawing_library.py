#!/usr/bin/env python3
"""Valida catálogo e metadados de desenhos PDF (api-delpi + extração local)."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_API_PREFIX = os.environ.get("SMOKE_API_PREFIX", "/apps/api-delpi").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_DRAWINGS_DIR = Path(
    os.environ.get(
        "DRAWING_PDF_LIBRARY_DIR",
        "/home/analistaptd/projetos/delpi-central/minha-delpi-ai-api/desenhos",
    )
)

# Códigos visíveis na biblioteca corporativa (FILESERVER / screenshot do usuário).
TARGET_CODES = [
    "90260027",
    "90263954",
    "90261358",
    "90262019",
    "90261656",
    "90261757",
    "90263396",
    "90261647",
    "90262948",
    "90262008",
    "90263489",
    "90264227",
    "90261899",
    "90263702",
    "90264205",
    "90261743",
    "90264050",
    "90264206",
    "90262018",
    "90261876",
    "90263992",
]


def _request(method: str, url: str, *, token: str | None = None) -> tuple[int, dict | None, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            status = response.status
            body = json.loads(raw) if raw else None
            return status, body, raw[:500]
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = None
        return exc.code, body, raw[:500]


def _fetch_token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Token ausente: {payload}")
    return str(token)


def _local_extract(code: str, pdf_path: Path, *, token: str) -> dict:
    chat_root = Path(__file__).resolve().parents[2] / "minha-delpi-ai-api"
    if str(chat_root) not in sys.path:
        sys.path.insert(0, str(chat_root))

    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.domain.services.chat_drawing_pdf_extraction_service import (
        ChatDrawingPdfExtractionService,
    )
    from app.domain.services.chat_drawing_structure_validation_service import (
        ChatDrawingStructureValidationService,
    )

    configure_domain_infrastructure_ports()

    extracted = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(pdf_path),
        filename=pdf_path.name,
    )
    bom_codes = list(extracted.get("componentCodes") or [])
    scopes = extracted.get("validationScopes") if isinstance(extracted.get("validationScopes"), dict) else {}
    bom_scope = scopes.get("bom") if isinstance(scopes.get("bom"), dict) else {}

    result = {
        "productCode": extracted.get("productCode"),
        "legible": extracted.get("legible"),
        "componentCodes": bom_codes,
        "intermediateCodes": list(extracted.get("intermediateCodes") or []),
        "bomAvailable": bool(bom_scope.get("available")),
        "bomSourceKey": bom_scope.get("sourceKey"),
        "criticalBomItems": [],
        "apiStructureOk": False,
    }

    token = os.environ.get("_VALIDATION_TOKEN")
    if token:
        status, analyser, _ = _request(
            "GET",
            f"{_BASE_URL}{_API_PREFIX}/products/{code}/analyser",
            token=token,
        )
        if status == 200 and isinstance(analyser, dict) and analyser.get("success"):
            root = analyser.get("data") if isinstance(analyser.get("data"), dict) else {}
            if root.get("structure"):
                result["apiStructureOk"] = True
                items = ChatDrawingStructureValidationService.build_check_items(
                    root=root,
                    pdf_extract=extracted,
                    product_code=code,
                )
                result["criticalBomItems"] = [
                    {
                        "item": row.get("item"),
                        "status": row.get("status"),
                        "pdfEvidence": row.get("pdfEvidence"),
                    }
                    for row in items
                    if row.get("section") == "BOM" and row.get("status") == "critical_error"
                ]

    return result


def main() -> int:
    print(f"Base URL: {_BASE_URL}{_API_PREFIX}")
    print(f"Biblioteca local: {_DRAWINGS_DIR}\n")

    token = _fetch_token()

    status, catalog, raw = _request(
        "GET",
        f"{_BASE_URL}{_API_PREFIX}/products/drawings?page=1&page_size=500&sort=product_code",
        token=token,
    )

    if status != 200 or not isinstance(catalog, dict) or not catalog.get("success"):
        print(f"FALHA list_product_drawings HTTP={status}")
        print(raw)
        return 1

    meta = catalog.get("meta") if isinstance(catalog.get("meta"), dict) else {}
    data = catalog.get("data") if isinstance(catalog.get("data"), dict) else {}
    items = data.get("items") if isinstance(data.get("items"), list) else []
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}

    print(
        f"OK list_product_drawings — entity={meta.get('entity')} shape={meta.get('shape')} "
        f"total={data.get('total')} scanned={summary.get('scanned_files')}"
    )

    catalog_codes = {str(row.get("product_code") or "") for row in items if isinstance(row, dict)}

    os.environ["_VALIDATION_TOKEN"] = token

    rows: list[dict] = []
    failures = 0

    for code in TARGET_CODES:
        row: dict = {"code": code, "inCatalog": code in catalog_codes}

        status_meta, meta_body, _ = _request(
            "GET",
            f"{_BASE_URL}{_API_PREFIX}/products/{code}/drawing",
            token=token,
        )
        row["metadataHttp"] = status_meta
        if status_meta == 200 and isinstance(meta_body, dict) and meta_body.get("success"):
            md = meta_body.get("data") if isinstance(meta_body.get("data"), dict) else {}
            row["found"] = bool(md.get("found"))
            row["filename"] = md.get("filename")
            row["revision"] = md.get("revision")
        else:
            row["found"] = False
            row["metadataError"] = (
                meta_body.get("message") if isinstance(meta_body, dict) else None
            )

        local_pdf = _DRAWINGS_DIR / f"{code}.pdf"
        if local_pdf.is_file():
            try:
                local = _local_extract(code, local_pdf, token=token)
                row["localExtract"] = local
                row["localPdf"] = local_pdf.name
                if local.get("criticalBomItems"):
                    failures += 1
            except Exception as exc:
                row["localExtractError"] = exc.__class__.__name__
                failures += 1

        rows.append(row)

        status_icon = "✓" if row.get("found") else "✗"
        bom_crit = len((row.get("localExtract") or {}).get("criticalBomItems") or [])
        print(
            f"{status_icon} {code} catalog={row['inCatalog']} api_found={row.get('found')} "
            f"local={'sim' if row.get('localPdf') else '—'} bom_crit={bom_crit}"
        )

    print("\n--- Detalhes BOM crítico (extração local + analyser) ---")
    for row in rows:
        local = row.get("localExtract")
        if not isinstance(local, dict):
            continue
        crit = local.get("criticalBomItems") or []
        if not crit:
            continue
        print(f"\n{row['code']}:")
        for item in crit:
            print(f"  - {item.get('item')} | pdf={item.get('pdfEvidence')}")

    print("\n--- Ausentes na API (FILESERVER) ---")
    missing_api = [row["code"] for row in rows if not row.get("found")]
    if missing_api:
        print(", ".join(missing_api))
    else:
        print("(nenhum)")

    print("\n--- Presentes localmente sem match na API ---")
    local_only = [
        row["code"]
        for row in rows
        if row.get("localPdf") and not row.get("found")
    ]
    if local_only:
        print(", ".join(local_only))
    else:
        print("(nenhum — ou PDFs locais também estão na API)")

    out_path = Path(__file__).resolve().parent / "validate_drawing_library_report.json"
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRelatório JSON: {out_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
