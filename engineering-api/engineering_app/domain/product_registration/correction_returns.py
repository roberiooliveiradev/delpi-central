"""PRC-REF-022 — ciclos de devolução para correção da ficha.

Framework-free. Não altera MATCH oficial nem escreve no TOTVS.
"""

from __future__ import annotations

from typing import Any

from engineering_app.domain.product_registration import catalog
from engineering_app.domain.product_registration.errors import PrcValidationError

CORRECTION_TARGET_TYPES = frozenset({"FIELD", "SUPPLIER_LINK"})
SUPPLIER_ATTRIBUTES = frozenset({"partNumber", "catalogNumber"})


def target_key_for(
    *,
    target_type: str,
    target_path: str | None,
    supplier_key: dict[str, Any] | None,
    target_attribute: str | None,
) -> str:
    if target_type == "FIELD":
        return f"FIELD:{target_path}"
    code = str((supplier_key or {}).get("supplierCode") or "").strip()
    store = str((supplier_key or {}).get("store") or "").strip()
    attr = (target_attribute or "link").strip()
    return f"SUPPLIER_LINK:{code}/{store}:{attr}"


def target_label_for(
    *,
    target_type: str,
    target_path: str | None,
    supplier_key: dict[str, Any] | None,
    target_attribute: str | None,
) -> str:
    if target_type == "FIELD":
        path = target_path or ""
        # Labels canônicos ficam no MFE/content; domínio usa path estável.
        return path
    code = str((supplier_key or {}).get("supplierCode") or "").strip()
    store = str((supplier_key or {}).get("store") or "").strip()
    attr = target_attribute or "link"
    return f"Fornecedor {code}/{store} · {attr}"


def validate_return_targets(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not raw:
        raise PrcValidationError(
            "Informe ao menos um alvo para devolução.",
            fields={"targets": "required"},
        )
    if len(raw) > 40:
        raise PrcValidationError(
            "Limite de alvos excedido.",
            fields={"targets": "max"},
        )
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    editable = set(catalog.EDITABLE_DRAFT_PATHS)
    for idx, item in enumerate(raw):
        ttype = str(item.get("targetType") or "").strip().upper()
        if ttype not in CORRECTION_TARGET_TYPES:
            raise PrcValidationError(
                "targetType inválido.",
                fields={f"targets[{idx}].targetType": "enum"},
            )
        reason = str(item.get("reason") or "").strip()
        if len(reason) < 3:
            raise PrcValidationError(
                "Motivo obrigatório por alvo (mín. 3).",
                fields={f"targets[{idx}].reason": "required"},
            )
        path = str(item.get("targetPath") or "").strip() or None
        attr = str(item.get("targetAttribute") or "").strip() or None
        supplier = item.get("supplierKey")
        if ttype == "FIELD":
            if not path or path not in editable or path == "suppliers":
                raise PrcValidationError(
                    "targetPath não permitido.",
                    fields={f"targets[{idx}].targetPath": "allowlist"},
                )
            supplier = None
            attr = None
        else:
            if not isinstance(supplier, dict):
                raise PrcValidationError(
                    "supplierKey obrigatório.",
                    fields={f"targets[{idx}].supplierKey": "required"},
                )
            code = str(supplier.get("supplierCode") or "").strip()
            store = str(supplier.get("store") or "").strip()
            if not code or not store:
                raise PrcValidationError(
                    "supplierCode/store obrigatórios.",
                    fields={f"targets[{idx}].supplierKey": "required"},
                )
            supplier = {"supplierCode": code, "store": store}
            if attr and attr not in SUPPLIER_ATTRIBUTES:
                raise PrcValidationError(
                    "targetAttribute inválido.",
                    fields={f"targets[{idx}].targetAttribute": "enum"},
                )
            path = path or "suppliers"
        key = target_key_for(
            target_type=ttype,
            target_path=path,
            supplier_key=supplier,
            target_attribute=attr,
        )
        if key in seen:
            raise PrcValidationError(
                "Alvo duplicado na devolução.",
                fields={f"targets[{idx}]": "duplicate"},
            )
        seen.add(key)
        out.append(
            {
                "ordinal": len(out) + 1,
                "target_type": ttype,
                "target_path": path,
                "target_attribute": attr,
                "supplier_key": supplier,
                "target_key": key,
                "target_label": target_label_for(
                    target_type=ttype,
                    target_path=path,
                    supplier_key=supplier,
                    target_attribute=attr,
                ),
                "reason": reason[:1000],
            }
        )
    return out


def allowlist_paths(targets: list[dict[str, Any]]) -> set[str]:
    """Paths SB1 + 'suppliers' quando houver alvo SA5."""
    paths: set[str] = set()
    for t in targets:
        if t.get("target_type") == "FIELD" and t.get("target_path"):
            paths.add(str(t["target_path"]))
        elif t.get("target_type") == "SUPPLIER_LINK":
            paths.add("suppliers")
    return paths


def public_return_view(
    row: dict[str, Any],
    *,
    include_targets: bool = True,
) -> dict[str, Any]:
    targets = row.get("targets") or []
    return {
        "id": row.get("id"),
        "requestId": row.get("request_id"),
        "sequence": row.get("sequence"),
        "status": row.get("status"),
        "originCaseVersion": row.get("origin_case_version"),
        "returnedBy": {
            "subject": row.get("returned_by_subject"),
            "displayName": row.get("returned_by_display_name"),
        },
        "requesterSubject": row.get("requester_subject"),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
        "resubmittedAt": row.get("resubmitted_at"),
        "resubmittedBySubject": row.get("resubmitted_by_subject"),
        "targets": (
            [
                {
                    "id": t.get("id"),
                    "ordinal": t.get("ordinal"),
                    "targetType": t.get("target_type"),
                    "targetPath": t.get("target_path"),
                    "targetAttribute": t.get("target_attribute"),
                    "supplierKey": t.get("supplier_key"),
                    "targetKey": t.get("target_key"),
                    "targetLabel": t.get("target_label"),
                    "reason": t.get("reason"),
                    "baselineValue": t.get("baseline_value"),
                    "addressedAt": t.get("addressed_at"),
                    "addressedBySubject": t.get("addressed_by_subject"),
                    "addressedMode": t.get("addressed_mode"),
                    "addressedValue": t.get("addressed_value"),
                }
                for t in targets
            ]
            if include_targets
            else []
        ),
    }


def all_targets_addressed(targets: list[dict[str, Any]]) -> bool:
    if not targets:
        return False
    return all(t.get("addressed_at") for t in targets)


def validate_returned_changes(
    *,
    targets: list[dict[str, Any]],
    changes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Valida patch do solicitante contra allowlist da devolução aberta."""
    if not changes:
        raise PrcValidationError(
            "Informe ao menos uma alteração ou confirmação.",
            fields={"changes": "required"},
        )
    allowed = allowlist_paths(targets)
    out: list[dict[str, Any]] = []
    for idx, change in enumerate(changes):
        path = str(change.get("path") or "").strip()
        if path not in allowed:
            raise PrcValidationError(
                "Campo não devolvido para correção.",
                fields={f"changes[{idx}].path": "allowlist"},
            )
        if path == "officialProductCode":
            raise PrcValidationError(
                "Código oficial é imutável nesta correção.",
                fields={f"changes[{idx}].path": "immutable"},
            )
        reason = str(change.get("reason") or "").strip()
        if len(reason) < 3:
            raise PrcValidationError(
                "Justificativa obrigatória por alvo (mín. 3).",
                fields={f"changes[{idx}].reason": "required"},
            )
        mode = str(change.get("mode") or "changed").strip().lower()
        if mode not in ("changed", "confirmed"):
            raise PrcValidationError(
                "mode inválido.",
                fields={f"changes[{idx}].mode": "enum"},
            )
        out.append(
            {
                "path": path,
                "proposedValue": change.get("proposedValue"),
                "reason": reason[:500],
                "mode": mode,
            }
        )
    return out
