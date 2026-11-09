"""D16 — bandeiras de acompanhamento do atendimento PRC.

Anotações operacionais governadas. Não alteram SB1/SA5/baseline/
revisões técnicas nem escrevem no TOTVS. Soft-delete auditável.
"""

from __future__ import annotations

from typing import Any

from engineering_app.domain.product_registration import catalog
from engineering_app.domain.product_registration.errors import (
    PrcValidationError,
)

FLAG_STATUSES = ("OPEN", "RESOLVED")
FLAG_SUBJECTS = ("GENERAL", "FIELD", "SUPPLIER_LINK")

TITLE_MAX = 120
DESCRIPTION_MAX = 1000

# Política explícita: bandeiras permanecem mutáveis após conclusão/
# rejeição do caso — sem reabrir cadastro oficial.
FLAG_MUTATION_AFTER_TERMINAL = True

_FIELD_PATHS = frozenset(
    spec.path
    for spec in catalog.FIELD_SPECS
    if spec.path != "officialProductCode" and spec.kind != "suppliers"
)


def validate_flag_payload(
    *,
    title: Any,
    description: Any,
    subject: Any = "GENERAL",
    target_path: Any = None,
    supplier_key: Any = None,
    partial: bool = False,
) -> dict[str, Any]:
    """Normaliza e valida payload de create/update.

    ``partial=True`` permite omitir campos no PATCH (só valida os
    presentes).
    """
    out: dict[str, Any] = {}

    if not partial or title is not None:
        text = str(title or "").strip()
        if not text:
            raise PrcValidationError(
                "title é obrigatório.",
                fields={"title": "required"},
            )
        if len(text) > TITLE_MAX:
            raise PrcValidationError(
                f"title excede {TITLE_MAX} caracteres.",
                fields={"title": "max_length"},
            )
        out["title"] = text

    if not partial or description is not None:
        text = str(description or "").strip()
        if not text:
            raise PrcValidationError(
                "description é obrigatória.",
                fields={"description": "required"},
            )
        if len(text) > DESCRIPTION_MAX:
            raise PrcValidationError(
                f"description excede {DESCRIPTION_MAX} caracteres.",
                fields={"description": "max_length"},
            )
        out["description"] = text

    subj = str(subject or "GENERAL").strip().upper() or "GENERAL"
    if subj not in FLAG_SUBJECTS:
        raise PrcValidationError(
            "subject inválido.",
            fields={"subject": "enum"},
        )
    out["subject"] = subj

    path = target_path
    if path is not None and str(path).strip() == "":
        path = None
    if path is not None:
        path = str(path).strip()
        if path not in _FIELD_PATHS:
            raise PrcValidationError(
                "targetPath não está no catálogo técnico.",
                fields={"targetPath": "invalid"},
            )
        if subj != "FIELD":
            raise PrcValidationError(
                "targetPath só se aplica a subject=FIELD.",
                fields={"targetPath": "invalid"},
            )
    out["targetPath"] = path

    key = supplier_key
    if key is None or key == {}:
        out["supplierKey"] = None
    else:
        if not isinstance(key, dict):
            raise PrcValidationError(
                "supplierKey inválido.",
                fields={"supplierKey": "invalid"},
            )
        code = str(key.get("supplierCode") or "").strip()
        store = str(key.get("store") or "").strip()
        if not code or not store:
            raise PrcValidationError(
                "supplierKey exige supplierCode e store.",
                fields={"supplierKey": "required"},
            )
        if subj != "SUPPLIER_LINK":
            raise PrcValidationError(
                "supplierKey só se aplica a subject=SUPPLIER_LINK.",
                fields={"supplierKey": "invalid"},
            )
        out["supplierKey"] = {"supplierCode": code, "store": store}

    if subj == "FIELD" and out.get("targetPath") is None and not partial:
        # FIELD sem path é permitido (contexto textual); path opcional.
        pass
    if subj == "SUPPLIER_LINK" and out.get("supplierKey") is None and not partial:
        raise PrcValidationError(
            "subject=SUPPLIER_LINK exige supplierKey.",
            fields={"supplierKey": "required"},
        )
    if subj == "GENERAL":
        out["targetPath"] = None
        out["supplierKey"] = None

    return out


def public_flag(row: dict[str, Any]) -> dict[str, Any]:
    """Projeção REST/EVA (sem internals de soft-delete brutos)."""
    return {
        "id": row["id"],
        "requestId": row["request_id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "subject": row["subject"],
        "targetPath": row.get("target_path"),
        "supplierKey": row.get("supplier_key"),
        "version": int(row["row_version"]),
        "createdAt": row["created_at"],
        "createdBy": {
            "subject": row["created_by_subject"],
            "displayName": row.get("created_by_display_name"),
        },
        "updatedAt": row["updated_at"],
        "updatedBy": {
            "subject": row.get("updated_by_subject"),
            "displayName": row.get("updated_by_display_name"),
        },
        "resolvedAt": row.get("resolved_at"),
        "resolvedBy": (
            {
                "subject": row["resolved_by_subject"],
                "displayName": row.get("resolved_by_display_name"),
            }
            if row.get("resolved_by_subject")
            else None
        ),
        "deleted": bool(row.get("deleted_at")),
    }
