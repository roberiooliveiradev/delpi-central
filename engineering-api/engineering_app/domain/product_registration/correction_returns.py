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


def supplier_link_targets_index(
    targets: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    """Mapa ``(supplierCode, store) -> {attrs permitidos, target_key}``
    dos alvos SUPPLIER_LINK da devolução aberta.

    Alvo sem ``target_attribute`` (link integral) autoriza os dois
    atributos editáveis do vínculo — nunca a identidade (código, loja,
    razão social) nem a lista.
    """
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for t in targets or []:
        if t.get("target_type") != "SUPPLIER_LINK":
            continue
        key = t.get("supplier_key") or {}
        code = str(key.get("supplierCode") or "").strip()
        store = str(key.get("store") or "").strip()
        if not code or not store:
            continue
        attr = str(t.get("target_attribute") or "").strip()
        allowed = (
            set(catalog.SUPPLIER_LINK_EDITABLE_FIELDS)
            if not attr
            else {attr}
        )
        entry = out.setdefault(
            (code, store), {"attrs": set(), "target_keys": set()}
        )
        entry["attrs"].update(allowed)
        entry["target_keys"].add(str(t.get("target_key") or ""))
    return out


def _supplier_identity(item: dict[str, Any]) -> tuple[str, str]:
    return (
        str(item.get("supplierCode") or "").strip(),
        str(item.get("store") or "").strip(),
    )


def validate_supplier_correction(
    *,
    targets: list[dict[str, Any]],
    current_suppliers: list[dict[str, Any]],
    proposed: Any,
    change_index: int = 0,
) -> tuple[list[dict[str, Any]], set[str]]:
    """Valida o valor proposto do path agregado ``suppliers`` contra a
    allowlist granular da devolução (vínculo + atributo devolvidos).

    Regras:
    - a lista proposta deve ter exatamente o mesmo conjunto de
      identidades ``(supplierCode, store)`` — sem adição nem remoção;
    - ``supplierName`` e a identidade nunca são editáveis;
    - cada atributo divergente deve pertencer a um alvo SUPPLIER_LINK
      devolvido para aquele vínculo;
    - vínculos alterados são revalidados integralmente
      (``partNumber`` obrigatório — PRC-REF-022-FIX-01);
    - vínculos intocados preservam o valor vigente (legado não é
      reescrito nem revalidado).

    Retorna ``(lista_mesclada, target_keys_endereçados)``.
    """
    field = f"changes[{change_index}].proposedValue"
    if not isinstance(proposed, list):
        raise PrcValidationError(
            "suppliers deve ser lista.",
            fields={field: "type"},
        )
    allowed = supplier_link_targets_index(targets)
    current_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    current_order: list[tuple[str, str]] = []
    for item in current_suppliers or []:
        if not isinstance(item, dict):
            continue
        key = _supplier_identity(item)
        if not key[0] or not key[1]:
            continue
        current_by_key.setdefault(key, item)
        if key not in current_order:
            current_order.append(key)
    proposed_keys: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in proposed:
        if not isinstance(item, dict):
            raise PrcValidationError(
                "suppliers[] deve conter objetos.",
                fields={field: "type"},
            )
        key = _supplier_identity(item)
        if key in seen:
            raise PrcValidationError(
                f"Vínculo {key[0]}/{key[1]} duplicado na proposta.",
                fields={field: "duplicate"},
            )
        seen.add(key)
        proposed_keys.append(key)
    if set(proposed_keys) != set(current_by_key):
        raise PrcValidationError(
            "A correção não pode adicionar nem remover vínculos de "
            "fornecedor — apenas os atributos devolvidos.",
            fields={field: "link_set"},
        )
    merged: list[dict[str, Any]] = []
    addressed: set[str] = set()
    changed_keys: set[tuple[str, str]] = set()
    for key in current_order:
        current = current_by_key[key]
        proposal = next(
            p for p in proposed if _supplier_identity(p) == key
        )
        entry = allowed.get(key, {"attrs": set(), "target_keys": set()})
        name = str(proposal.get("supplierName") or "").strip()
        if name != str(current.get("supplierName") or "").strip():
            raise PrcValidationError(
                f"Razão social do vínculo {key[0]}/{key[1]} não é "
                "editável nesta correção.",
                fields={field: "immutable"},
            )
        candidate = dict(current)
        link_changed = False
        for attr in catalog.SUPPLIER_LINK_EDITABLE_FIELDS:
            new_value = proposal.get(attr)
            new_text = (
                ""
                if new_value is None
                else str(new_value).strip()
            )
            cur_text = str(current.get(attr) or "").strip()
            if new_text == cur_text:
                continue
            if attr not in entry["attrs"]:
                raise PrcValidationError(
                    f"Atributo '{attr}' do vínculo {key[0]}/{key[1]} "
                    "não foi devolvido para correção.",
                    fields={field: "allowlist"},
                )
            candidate[attr] = new_text
            link_changed = True
        if link_changed:
            changed_keys.add(key)
            # Vínculo alterado → revalidação integral (PN obrigatório).
            validated = catalog.validate_supplier(candidate)
            addressed.update(entry["target_keys"])
            merged.append(validated)
        else:
            merged.append(dict(current))
    if not changed_keys:
        raise PrcValidationError(
            "Nenhum atributo devolvido foi alterado — use "
            "mode='confirmed' para confirmar sem mudança.",
            fields={field: "no_change"},
        )
    return merged, addressed


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
