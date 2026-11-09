"""D15 — baseline oficial persistido e pré-condições SA5.

O baseline é capturado pela Engineering API via leitura oficial
(api-delpi → TOTVS). Payload do browser nunca é prova de estado
oficial. Identidade do vínculo: (supplierCode, store) com zeros
preservados. Filial é implícita na fonte oficial contratada.

Política de conclusão REMOVE: ``PENDING_OWNER`` até aprovação
formal da Engenharia — propostas reversíveis e verificação técnica
são permitidas; publicação de revisão com op ``remove`` permanece
bloqueada.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from engineering_app.domain.product_registration import catalog

# Contrato de fonte / versão do snapshot D15.
SOURCE_CONTRACT_VERSION = "prc-sa5-baseline.v1"
OFFICIAL_SOURCE = catalog.OFFICIAL_SOURCE

# Gate de conclusão REMOVE — owner Engenharia ainda não aprovou a
# política final de ausência oficial publicada.
SA5_REMOVE_COMPLETION_POLICY = "PENDING_OWNER"
SA5_REMOVE_COMPLETION_ALLOWED = False


def _norm_code(value: Any) -> str:
    return str(value or "").strip()


def _norm_attr(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def link_key_from_official(item: dict[str, Any]) -> tuple[str, str]:
    return (
        _norm_code(item.get("supplier_code")),
        _norm_code(item.get("supplier_store")),
    )


def link_key_from_op(op: dict[str, Any]) -> tuple[str, str]:
    key = op.get("key") or {}
    return (_norm_code(key.get("supplierCode")), _norm_code(key.get("store")))


def _links_from_observed(suppliers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in suppliers or []:
        if not isinstance(item, dict):
            continue
        code, store = link_key_from_official(item)
        if not code or not store:
            continue
        out.append(
            {
                "supplierCode": code,
                "store": store,
                "supplierName": _norm_attr(item.get("supplier_name")),
                "supplierShortName": _norm_attr(
                    item.get("supplier_short_name")
                ),
                "partNumber": _norm_attr(item.get("supplier_part_number")),
                "catalogNumber": _norm_attr(item.get("catalog_code")),
                "partNumberPresent": "supplier_part_number" in item,
                "catalogNumberPresent": "catalog_code" in item,
            }
        )
    return out


def _product_fields_from_observed(product: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for spec in catalog.FIELD_SPECS:
        if not spec.official_field or spec.kind == "suppliers":
            continue
        fields[spec.path] = {
            "value": product.get(spec.official_field),
            "officialField": spec.official_field,
            "present": spec.official_field in product,
        }
    return fields


def fingerprint_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()


def relevant_state_for_fingerprint(
    *,
    official_code: str,
    fields: dict[str, Any],
    links: list[dict[str, Any]],
    links_complete: bool,
) -> dict[str, Any]:
    """Estado relevante para concorrência — não usa timestamp isolado."""
    return {
        "officialProductCode": official_code,
        "linksComplete": bool(links_complete),
        "fields": {
            path: {
                "value": meta.get("value"),
                "present": meta.get("present"),
            }
            for path, meta in sorted(fields.items())
        },
        "links": sorted(
            [
                {
                    "supplierCode": link["supplierCode"],
                    "store": link["store"],
                    "partNumber": link.get("partNumber"),
                    "catalogNumber": link.get("catalogNumber"),
                    "partNumberPresent": link.get("partNumberPresent"),
                    "catalogNumberPresent": link.get("catalogNumberPresent"),
                }
                for link in links
            ],
            key=lambda x: (x["supplierCode"], x["store"]),
        ),
    }


def build_official_baseline(
    observed: dict[str, Any],
    *,
    official_code: str,
    captured_by: str,
    correlation_id: str,
    captured_at: str,
    baseline_version: int = 1,
) -> dict[str, Any]:
    """Monta o snapshot canônico a partir da leitura oficial."""
    product = observed.get("product") or {}
    links = _links_from_observed(list(observed.get("suppliers") or []))
    links_complete = bool(observed.get("suppliers_complete", True))
    fields = _product_fields_from_observed(product)
    state = relevant_state_for_fingerprint(
        official_code=official_code,
        fields=fields,
        links=links,
        links_complete=links_complete,
    )
    return {
        "baselineVersion": baseline_version,
        "sourceContractVersion": SOURCE_CONTRACT_VERSION,
        "officialProductCode": official_code,
        "officialSource": OFFICIAL_SOURCE,
        "readAt": captured_at,
        "capturedAt": captured_at,
        "capturedBy": captured_by,
        "correlationId": correlation_id,
        "linksComplete": links_complete,
        "status": observed.get("status"),
        "fields": fields,
        "links": links,
        "fingerprint": fingerprint_payload(state),
    }


def index_baseline_links(
    baseline: dict[str, Any],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    indexed: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for link in baseline.get("links") or []:
        if not isinstance(link, dict):
            continue
        key = (
            _norm_code(link.get("supplierCode")),
            _norm_code(link.get("store")),
        )
        if not key[0] or not key[1]:
            continue
        indexed.setdefault(key, []).append(link)
    return indexed


def validate_link_ops_against_baseline(
    ops: list[dict[str, Any]],
    baseline: dict[str, Any],
) -> str | None:
    """Pré-condições ADD/UPDATE/REMOVE contra baseline server-side.

    Retorna mensagem de erro ou ``None`` quando válido.
    """
    if not baseline.get("linksComplete", False):
        return (
            "Baseline SA5 incompleto — formalização bloqueada "
            "(consulta parcial não prova ausência/presença)."
        )
    indexed = index_baseline_links(baseline)
    for i, op in enumerate(ops or []):
        key = link_key_from_op(op)
        label = f"{key[0]}/{key[1]}"
        found = indexed.get(key, [])
        operation = op.get("operation")
        if len(found) > 1:
            return (
                f"supplierLinkChanges[{i}] chave oficial ambígua "
                f"{label} no baseline (integridade SA5)."
            )
        if operation == "add":
            if found:
                return (
                    f"supplierLinkChanges[{i}] ADD rejeitado — vínculo "
                    f"{label} já existe no baseline oficial."
                )
            continue
        if operation in ("update", "remove"):
            if not found:
                return (
                    f"supplierLinkChanges[{i}] {operation.upper()} "
                    f"rejeitado — vínculo {label} ausente no baseline."
                )
            if operation == "update":
                before = found[0]
                fields = op.get("fields") or {}
                changed = False
                for field, proposed in fields.items():
                    current = _norm_attr(before.get(field))
                    if _norm_attr(proposed) != current:
                        changed = True
                        break
                if not changed:
                    return (
                        f"supplierLinkChanges[{i}] UPDATE sem alteração "
                        f"efetiva em {label}."
                    )
            continue
        return f"supplierLinkChanges[{i}] operation inválida."
    return None


def remove_ops_present(ops: list[dict[str, Any]] | None) -> bool:
    return any(
        isinstance(op, dict) and op.get("operation") == "remove"
        for op in (ops or [])
    )


def public_baseline_view(baseline: dict[str, Any] | None) -> dict[str, Any] | None:
    """Projeção read-only segura para detalhe REST/EVA."""
    if not baseline:
        return None
    return {
        "baselineVersion": baseline.get("baselineVersion"),
        "sourceContractVersion": baseline.get("sourceContractVersion"),
        "officialProductCode": baseline.get("officialProductCode"),
        "officialSource": baseline.get("officialSource"),
        "readAt": baseline.get("readAt"),
        "capturedAt": baseline.get("capturedAt"),
        "capturedBy": baseline.get("capturedBy"),
        "linksComplete": baseline.get("linksComplete"),
        "fingerprint": baseline.get("fingerprint"),
        "fields": baseline.get("fields"),
        "links": baseline.get("links"),
        "removeCompletionPolicy": SA5_REMOVE_COMPLETION_POLICY,
    }
