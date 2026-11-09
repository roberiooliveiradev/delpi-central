"""D16 / D16-REF-01 — bandeiras de acompanhamento PRC.

Anotações operacionais governadas por alvo técnico (FIELD path ou
SUPPLIER_LINK+atributo). Não alteram SB1/SA5/baseline/revisões nem
escrevem no TOTVS. Soft-delete auditável. GENERAL é somente legado.
"""

from __future__ import annotations

from typing import Any

from engineering_app.domain.product_registration import catalog
from engineering_app.domain.product_registration.errors import (
    PrcValidationError,
)

FLAG_STATUSES = ("OPEN", "RESOLVED")
FLAG_SUBJECTS = ("GENERAL", "FIELD", "SUPPLIER_LINK")
SUPPLIER_FLAG_ATTRIBUTES = ("partNumber", "catalogNumber")

TITLE_MAX = 120
DESCRIPTION_MAX = 1000

# Política explícita: bandeiras permanecem mutáveis após conclusão/
# rejeição do caso — sem reabrir cadastro oficial.
FLAG_MUTATION_AFTER_TERMINAL = True

# Novos fluxos contextuais (UI/EVA) não criam GENERAL.
ALLOW_NEW_GENERAL = False

_FIELD_PATHS = frozenset(
    spec.path
    for spec in catalog.FIELD_SPECS
    if spec.path != "officialProductCode" and spec.kind != "suppliers"
)


def flaggable_field_paths() -> tuple[str, ...]:
    """Paths SB1 sinalizáveis na Ficha técnica (ordem do catálogo)."""
    return tuple(
        spec.path
        for spec in catalog.FIELD_SPECS
        if spec.path in _FIELD_PATHS
    )


def normalize_target_key(
    *,
    subject: str,
    target_path: str | None = None,
    supplier_key: dict | None = None,
    target_attribute: str | None = None,
    flag_id: str | None = None,
) -> str:
    """Chave determinística para unicidade OPEN por solicitação."""
    subj = str(subject or "").strip().upper()
    if subj == "FIELD":
        path = str(target_path or "").strip()
        if not path:
            raise PrcValidationError(
                "targetPath é obrigatório para subject=FIELD.",
                fields={"targetPath": "required"},
            )
        return f"FIELD:{path}"
    if subj == "SUPPLIER_LINK":
        if not isinstance(supplier_key, dict):
            raise PrcValidationError(
                "supplierKey é obrigatório para subject=SUPPLIER_LINK.",
                fields={"supplierKey": "required"},
            )
        code = str(supplier_key.get("supplierCode") or "").strip()
        store = str(supplier_key.get("store") or "").strip()
        attr = str(target_attribute or "").strip()
        if not code or not store:
            raise PrcValidationError(
                "supplierKey exige supplierCode e store.",
                fields={"supplierKey": "required"},
            )
        if attr not in SUPPLIER_FLAG_ATTRIBUTES:
            raise PrcValidationError(
                "targetAttribute inválido para SUPPLIER_LINK.",
                fields={"targetAttribute": "enum"},
            )
        return f"SUPPLIER:{code}|{store}|{attr}"
    if subj == "GENERAL":
        # Legado: cada registro mantém chave própria (não collapsa).
        fid = str(flag_id or "").strip() or "legacy"
        return f"GENERAL:{fid}"
    raise PrcValidationError(
        "subject inválido.", fields={"subject": "enum"}
    )


def validate_flag_payload(
    *,
    title: Any,
    description: Any,
    subject: Any = "FIELD",
    target_path: Any = None,
    supplier_key: Any = None,
    target_attribute: Any = None,
    partial: bool = False,
    allow_general: bool = False,
    flag_id: str | None = None,
) -> dict[str, Any]:
    """Normaliza e valida payload de create/update.

    ``partial=True`` permite omitir campos no PATCH (só valida os
    presentes). ``allow_general`` só para leitura/legado — criações
    novas contextuais devem passar ``allow_general=False``.
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

    if not partial or subject is not None:
        subj = str(subject or "FIELD").strip().upper() or "FIELD"
    else:
        subj = "FIELD"
    if subj not in FLAG_SUBJECTS:
        raise PrcValidationError(
            "subject inválido.",
            fields={"subject": "enum"},
        )
    if subj == "GENERAL" and not allow_general and not ALLOW_NEW_GENERAL:
        raise PrcValidationError(
            "Novas bandeiras GENERAL não são permitidas — use FIELD "
            "ou SUPPLIER_LINK com alvo técnico.",
            fields={"subject": "deprecated"},
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
    attr = target_attribute
    if attr is not None and str(attr).strip() == "":
        attr = None
    if attr is not None:
        attr = str(attr).strip()

    key = supplier_key
    if key == {}:
        key = None

    if subj == "FIELD":
        if path is None and not partial:
            raise PrcValidationError(
                "subject=FIELD exige targetPath.",
                fields={"targetPath": "required"},
            )
        if key is not None or attr is not None:
            raise PrcValidationError(
                "supplierKey/targetAttribute não se aplicam a FIELD.",
                fields={"targetPath": "invalid"},
            )
        out["targetPath"] = path
        out["supplierKey"] = None
        out["targetAttribute"] = None
    elif subj == "SUPPLIER_LINK":
        if path is not None:
            raise PrcValidationError(
                "targetPath não se aplica a SUPPLIER_LINK.",
                fields={"targetPath": "invalid"},
            )
        if not isinstance(key, dict) and not partial:
            raise PrcValidationError(
                "supplierKey é obrigatório.",
                fields={"supplierKey": "required"},
            )
        if isinstance(key, dict):
            code = str(key.get("supplierCode") or "").strip()
            store = str(key.get("store") or "").strip()
            if not code or not store:
                raise PrcValidationError(
                    "supplierKey exige supplierCode e store.",
                    fields={"supplierKey": "required"},
                )
            out["supplierKey"] = {"supplierCode": code, "store": store}
        elif partial:
            out["supplierKey"] = None
        else:
            out["supplierKey"] = None
        if attr is None and not partial:
            raise PrcValidationError(
                "subject=SUPPLIER_LINK exige targetAttribute "
                "(partNumber|catalogNumber).",
                fields={"targetAttribute": "required"},
            )
        if attr is not None and attr not in SUPPLIER_FLAG_ATTRIBUTES:
            raise PrcValidationError(
                "targetAttribute inválido.",
                fields={"targetAttribute": "enum"},
            )
        out["targetPath"] = None
        out["targetAttribute"] = attr
    else:  # GENERAL legado
        out["targetPath"] = None
        out["supplierKey"] = None
        out["targetAttribute"] = None

    if not partial or "subject" in out:
        out["targetKey"] = normalize_target_key(
            subject=out["subject"],
            target_path=out.get("targetPath"),
            supplier_key=out.get("supplierKey"),
            target_attribute=out.get("targetAttribute"),
            flag_id=flag_id,
        )
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
        "targetAttribute": row.get("target_attribute"),
        "supplierKey": row.get("supplier_key"),
        "targetKey": row.get("target_key"),
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
        "legacyGeneral": row.get("subject") == "GENERAL",
    }
