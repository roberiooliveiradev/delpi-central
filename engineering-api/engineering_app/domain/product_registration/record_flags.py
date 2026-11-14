"""PRC-TRACK — bandeiras de produto acompanhado (record-scoped).

Semântica temporal ADR-04/CR-07:

- identidade única por ``record_id + target_key`` enquanto ``OPEN``;
- ``OPEN`` propaga-se às revisões posteriores enquanto aberta;
- ``RESOLVED`` na revisão R fica visível **somente** em R;
- ``REMOVED`` na revisão R some já em R;
- ocorrências encerradas são terminais — não há reopen; uma nova
  ocorrência no mesmo alvo gera novo ``flag_id``;
- eventos registram a revisão vigente no ato e **nunca** criam Vn.
"""

from __future__ import annotations

from typing import Any

from engineering_app.domain.product_registration.errors import (
    PrcValidationError,
)

RECORD_FLAG_STATUSES = ("OPEN", "RESOLVED", "REMOVED")
RECORD_FLAG_CLOSE_STATUSES = ("RESOLVED", "REMOVED")


def visible_status_at_revision(
    flag: dict[str, Any], revision_number: int
) -> str | None:
    """Estado da bandeira no corte da revisão informada.

    Retorna ``"OPEN"``, ``"RESOLVED"`` ou ``None`` (ausente no corte).
    """
    opened = int(flag.get("opened_revision_number") or 0)
    if revision_number < opened:
        return None
    closed_rev = flag.get("closed_revision_number")
    if closed_rev is None:
        return "OPEN"
    closed_rev = int(closed_rev)
    if revision_number < closed_rev:
        return "OPEN"
    if revision_number == closed_rev:
        return (
            "RESOLVED"
            if flag.get("closed_status") == "RESOLVED"
            else None
        )
    return None


def public_record_flag(
    row: dict[str, Any],
    *,
    at_status: str | None = None,
) -> dict[str, Any]:
    """Projeção REST da bandeira de produto.

    ``at_status`` = estado efetivo no corte consultado
    (``visible_status_at_revision``); quando omitido usa o status
    corrente da linha.
    """
    return {
        "id": row["id"],
        "recordId": row["record_id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "atStatus": at_status or row["status"],
        "subject": row["subject"],
        "targetPath": row.get("target_path"),
        "targetAttribute": row.get("target_attribute"),
        "supplierKey": row.get("supplier_key"),
        "targetKey": row.get("target_key"),
        "version": int(row["row_version"]),
        "openedRevisionNumber": row["opened_revision_number"],
        "closedRevisionNumber": row.get("closed_revision_number"),
        "originRequestId": row.get("origin_request_id"),
        "createdAt": row["created_at"],
        "createdBy": {
            "subject": row["created_by_subject"],
            "displayName": row.get("created_by_display_name"),
        },
        "updatedAt": row["updated_at"],
        "closedAt": row.get("closed_at"),
        "closedBy": {
            "subject": row.get("closed_by_subject"),
            "displayName": row.get("closed_by_display_name"),
        },
    }


def public_record_flag_event(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "flagId": row["flag_id"],
        "recordId": row["record_id"],
        "eventType": row["event_type"],
        "revisionNumber": row["revision_number"],
        "occurredAt": row["occurred_at"],
        "actor": {
            "subject": row["actor_subject"],
            "displayName": row.get("actor_display_name"),
        },
        "note": row.get("note"),
    }


def validate_close_transition(
    flag: dict[str, Any], *, to_status: str
) -> None:
    """CR-07 — OPEN é o único estado mutável; encerradas são terminais."""
    if to_status not in RECORD_FLAG_CLOSE_STATUSES:
        raise PrcValidationError(
            "Transição de bandeira inválida.",
            fields={"status": "enum"},
        )
    if flag["status"] != "OPEN":
        raise PrcValidationError(
            "Bandeira já encerrada — ocorrências RESOLVED/REMOVED são "
            "terminais; uma reincidência exige nova bandeira.",
            fields={"status": "terminal"},
        )


def validate_target_exists_in_snapshot(
    snapshot: dict[str, Any] | None,
    *,
    subject: str,
    target_path: str | None,
    supplier_key: dict[str, Any] | None,
) -> None:
    """Fail-closed: alvo deve existir na ficha vigente do produto.

    ``snapshot`` é o ``technical_snapshot`` da revisão corrente
    (``schemaVersion=2``: ``fields{path:{coverageState,value,…}}`` +
    ``supplierLinks{"code|store":{linkState,attributes}}``).
    """
    snap = snapshot or {}
    if subject == "FIELD":
        entry = (snap.get("fields") or {}).get(target_path or "")
        if not isinstance(entry, dict) or entry.get(
            "coverageState"
        ) != "present":
            raise PrcValidationError(
                "Alvo inexistente na ficha vigente do produto.",
                fields={"targetPath": "not_in_current_revision"},
            )
        return
    if subject == "SUPPLIER_LINK":
        key = supplier_key or {}
        code = str(key.get("supplierCode") or "").strip()
        store = str(key.get("store") or "").strip()
        link = (snap.get("supplierLinks") or {}).get(
            f"{code}|{store}"
        )
        if not isinstance(link, dict) or link.get(
            "linkState"
        ) != "present":
            raise PrcValidationError(
                "Vínculo de fornecedor inexistente na ficha vigente.",
                fields={"supplierKey": "not_in_current_revision"},
            )
        return
    raise PrcValidationError(
        "subject inválido para bandeira de produto.",
        fields={"subject": "enum"},
    )
