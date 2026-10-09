"""Helpdesk read service — TÉO projection of Helpdesk/GLPI demand.

Semantics carried to the caller:
- the BFF response is the current Helpdesk/GLPI truth as projected by
  the owner — TÉO never supplements ticket state from memory;
- ticket-reported causes are INFORMED, never proven root cause;
- `can_*` flags are Helpdesk-domain facts computed by the BFF — guidance
  for future writes, never authorization TÉO may expand;
- knowledge about tickets is not process truth and not authorization.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.helpdesk.helpdesk_read_port import (
    HELPDESK_CATALOG_KINDS,
    HELPDESK_READ_ACTIONS,
    TICKET_FILTER_KEYS,
    HelpdeskReadPort,
)
from tm_app.infrastructure.gateways.helpdesk_bff_gateway import (
    HelpdeskBffGateway,
)

_AUTHORITY = "helpdesk_bff_glpi"
_NOTE = (
    "Helpdesk/GLPI demand — knowledge, not authorization and not "
    "process truth. `can_*` flags report what the BFF/GLPI allow this "
    "user; reported causes remain INFORMED until validated."
)


def _validation(message: str, error_code: str = "VALIDATION") -> GptActionsError:
    return GptActionsError(
        message, 400, {"error_kind": "validation", "error_code": error_code}
    )


class HelpdeskReadService:
    def __init__(self, gateway: HelpdeskReadPort | None = None) -> None:
        self._gateway = gateway or HelpdeskBffGateway()

    def read_helpdesk(
        self,
        authorization: str,
        *,
        action: str,
        ticket_id: int | None = None,
        catalog_kind: str | None = None,
        q: str | None = None,
        status: str | None = None,
        urgency_id: int | None = None,
        category_id: int | None = None,
        assignee_id: int | None = None,
        updated_from: str | None = None,
        updated_to: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        sort: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        purpose: str | None = None,
        limit: int | None = None,
        document_id: int | None = None,
        include_content: bool = False,
    ) -> dict[str, Any]:
        """Canonical read surface: action=session|capabilities|tickets|
        ticket|attachment|catalog. Fail-closed on contradictory input."""
        act = str(action or "").strip().lower()
        if act not in HELPDESK_READ_ACTIONS:
            raise _validation(
                "action deve ser 'session', 'capabilities', 'tickets', "
                "'ticket', 'attachment' ou 'catalog'.",
                "INVALID_ACTION",
            )
        filters = {
            "q": q,
            "status": status,
            "urgency_id": urgency_id,
            "category_id": category_id,
            "assignee_id": assignee_id,
            "updated_from": updated_from,
            "updated_to": updated_to,
            "created_from": created_from,
            "created_to": created_to,
            "sort": sort,
            "page": page,
            "page_size": page_size,
        }
        provided = {
            k for k, v in filters.items() if v is not None and str(v).strip() != ""
        }

        if act == "ticket":
            if ticket_id is None or int(ticket_id) <= 0:
                raise _validation(
                    "ticket_id é obrigatório para action=ticket.",
                    "TICKET_ID_REQUIRED",
                )
            if catalog_kind or provided or purpose or limit is not None or document_id is not None:
                raise _validation(
                    "catalog_kind/filtros/document_id não se aplicam a "
                    "action=ticket.",
                    "INVALID_FIELD",
                )
            return {
                "schema": "helpdesk_ticket_v1",
                "authority": _AUTHORITY,
                "note": _NOTE,
                "ticket": self._gateway.ticket(authorization, int(ticket_id)),
            }

        if act == "attachment":
            if ticket_id is None or int(ticket_id) <= 0:
                raise _validation(
                    "ticket_id é obrigatório para action=attachment.",
                    "TICKET_ID_REQUIRED",
                )
            if document_id is None or int(document_id) <= 0:
                raise _validation(
                    "document_id é obrigatório para action=attachment.",
                    "DOCUMENT_ID_REQUIRED",
                )
            if catalog_kind or provided or purpose or limit is not None:
                raise _validation(
                    "catalog_kind/filtros não se aplicam a action=attachment.",
                    "INVALID_FIELD",
                )
            doc = self._gateway.attachment(
                authorization, int(ticket_id), int(document_id)
            )
            content = doc.get("content") or b""
            result = {
                "schema": "helpdesk_attachment_v1",
                "authority": _AUTHORITY,
                "note": _NOTE,
                "ticket_id": int(ticket_id),
                "document": {
                    "document_id": int(document_id),
                    "filename": doc.get("filename"),
                    "mime": doc.get("mime"),
                    "byte_size": len(content),
                },
            }
            if include_content:
                # Bytes ride MCP content blocks — never inside the JSON
                # payload itself. The transport converts/omits them.
                result["content"] = content
                result["content_delivery"] = "inline"
            else:
                result["content_delivery"] = "metadata_only"
            return result

        if act == "catalog":
            if ticket_id is not None or document_id is not None or provided - {"q"}:
                raise _validation(
                    "ticket_id/document_id/filtros de ticket não se "
                    "aplicam a action=catalog.",
                    "INVALID_FIELD",
                )
            kind = str(catalog_kind or "").strip()
            if kind not in HELPDESK_CATALOG_KINDS:
                raise _validation(
                    f"catalog_kind inválido ou ausente. Permitidos: "
                    f"{', '.join(HELPDESK_CATALOG_KINDS)}.",
                    "INVALID_CATALOG_KIND",
                )
            # Only the users catalog supports search/purpose/limit —
            # reject inappropriate parameters instead of silently
            # dropping them.
            if kind != "users" and (q or purpose or limit is not None):
                raise _validation(
                    "q/purpose/limit só se aplicam a catalog_kind=users.",
                    "INVALID_FIELD",
                )
            return {
                "schema": "helpdesk_catalog_v1",
                "authority": _AUTHORITY,
                "note": _NOTE,
                "catalog_kind": kind,
                **self._gateway.catalog(
                    authorization, kind, q=q, purpose=purpose, limit=limit
                ),
            }

        if act == "tickets":
            if ticket_id is not None or document_id is not None:
                raise _validation(
                    "ticket_id/document_id não se aplicam a "
                    "action=tickets.",
                    "INVALID_FIELD",
                )
            if catalog_kind or purpose or limit is not None:
                raise _validation(
                    "catalog_kind/purpose/limit não se aplicam a "
                    "action=tickets.",
                    "INVALID_FIELD",
                )
            return {
                "schema": "helpdesk_tickets_v1",
                "authority": _AUTHORITY,
                "note": _NOTE,
                **self._gateway.tickets(authorization, filters),
            }

        # session / capabilities — no parameters allowed
        if (
            ticket_id is not None
            or document_id is not None
            or catalog_kind
            or provided
            or purpose
            or limit is not None
        ):
            raise _validation(
                f"action={act} não aceita parâmetros.",
                "INVALID_FIELD",
            )
        data = (
            self._gateway.session(authorization)
            if act == "session"
            else self._gateway.capabilities(authorization)
        )
        return {
            "schema": f"helpdesk_{act}_v1",
            "authority": _AUTHORITY,
            "note": _NOTE,
            **data,
        }
