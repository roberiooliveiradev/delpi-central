"""Use cases — solicitação de emissão de nota fiscal."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.services.invoice_issuance_portal_notification_service import (
    notify_request_created,
    notify_request_issued,
    notify_request_returned,
    notify_request_cancelled,
)
from app.domain.services.invoice_issuance.carrier_contact import (
    carrier_snapshot_fields,
    enrich_request_carrier,
)
from app.domain.services.invoice_issuance.constants import (
    FREIGHT_MODES,
    INVOICE_TYPES,
    PARTY_TYPES,
    TERMINAL_STATUSES,
    VALID_BRANCHES,
    default_stock_write_off,
)
from app.domain.services.invoice_issuance.open_sales_orders import group_open_sales_orders
from app.domain.services.invoice_issuance.review_checklist import build_review_checklist
from app.domain.services.invoice_issuance.exceptions import (
    InvoiceIssuanceForbiddenError,
    InvoiceIssuanceInvalidTransitionError,
    InvoiceIssuanceNotFoundError,
    InvoiceIssuanceValidationError,
    PartyBlockedError,
    PartyNotFoundError,
    ProductNotFoundError,
)
from app.shared.utils.person_name import format_person_name


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: str
    user_name: str
    has_access: bool = False
    has_create: bool = False
    has_view: bool = False
    has_process: bool = False
    has_manage: bool = False

    @property
    def can_view_all(self) -> bool:
        return self.has_view or self.has_process or self.has_manage

    @property
    def can_open_plugin(self) -> bool:
        return (
            self.has_access
            or self.has_create
            or self.has_view
            or self.has_process
            or self.has_manage
        )


def allowed_actions(request: dict[str, Any], actor: Actor) -> list[str]:
    status = request.get("status")
    is_owner = request.get("created_by_user_id") == actor.user_id
    actions: list[str] = []
    if actor.can_view_all or is_owner:
        actions.append("view")
    if status in TERMINAL_STATUSES:
        return actions
    if status == "returned" and actor.has_create and is_owner:
        actions.append("edit")
        actions.append("resubmit")
    if status == "pending" and (actor.has_process or actor.has_manage):
        actions.append("start")
    if status == "in_progress" and (actor.has_process or actor.has_manage):
        actions.append("return")
        actions.append("issue")
    if (actor.has_create and is_owner and status == "pending") or (
        actor.has_manage and status not in TERMINAL_STATUSES
    ) or (actor.has_process and status == "in_progress"):
        actions.append("cancel")
    return actions


def _require_branch(raw: Any) -> str:
    branch = str(raw or "").strip()
    if branch not in VALID_BRANCHES:
        raise InvoiceIssuanceValidationError("Filial inválida. Use 01 ou 02.")
    return branch


def _parse_decimal(raw: Any, *, field: str, min_value: Decimal) -> Decimal:
    text = str(raw if raw is not None else "").strip()
    if not text:
        raise InvoiceIssuanceValidationError(f"{field} inválido.")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise InvoiceIssuanceValidationError(f"{field} inválido.") from exc
    if value < min_value:
        raise InvoiceIssuanceValidationError(f"{field} deve ser maior que {min_value}.")
    return value


def _parse_items(raw: Any, *, invoice_type: str) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise InvoiceIssuanceValidationError("Informe ao menos um item.")
    items: list[dict[str, Any]] = []
    for index, row in enumerate(raw, start=1):
        if not isinstance(row, dict):
            raise InvoiceIssuanceValidationError(f"Item {index} inválido.")
        code = str(row.get("product_code") or "").strip()
        description = str(row.get("product_description") or "").strip()
        if not code:
            raise InvoiceIssuanceValidationError(f"Item {index}: informe o código.")
        quantity = _parse_decimal(row.get("quantity"), field=f"Quantidade do item {index}", min_value=Decimal("0.0001"))
        unit_price = _parse_decimal(
            row.get("unit_price"),
            field=f"Valor unitário do item {index}",
            min_value=Decimal("0"),
        )
        sales_order = str(row.get("sales_order") or "").strip() or None
        sales_order_item = str(row.get("sales_order_item") or "").strip() or None
        customer_order_number = str(row.get("customer_order_number") or "").strip() or None
        if bool(sales_order) != bool(sales_order_item):
            raise InvoiceIssuanceValidationError(
                f"Item {index}: informe o pedido de venda e o item juntos."
            )
        if sales_order:
            sales_order = sales_order[:20]
            sales_order_item = (sales_order_item or "")[:6]
        if customer_order_number:
            customer_order_number = customer_order_number[:60]
        raw_write_off = row.get("stock_write_off")
        items.append(
            {
                "product_code": code,
                "product_description": description or code,
                "quantity": quantity,
                "unit_price": unit_price,
                "stock_write_off": (
                    default_stock_write_off(invoice_type)
                    if raw_write_off is None
                    else bool(raw_write_off)
                ),
                "sales_order": sales_order,
                "sales_order_item": sales_order_item,
                "customer_order_number": customer_order_number,
            }
        )
    return items


def _payload_fields(
    payload: dict[str, Any], party: dict[str, Any], items: list[dict[str, Any]]
) -> dict[str, Any]:
    invoice_type = str(payload.get("invoice_type") or "").strip()
    if invoice_type not in INVOICE_TYPES:
        raise InvoiceIssuanceValidationError("Tipo de nota fiscal inválido.")
    other = str(payload.get("invoice_type_other") or "").strip() or None
    if invoice_type == "other" and not other:
        raise InvoiceIssuanceValidationError("Descreva o tipo de nota fiscal.")
    if invoice_type != "other":
        other = None
    freight = str(payload.get("freight_mode") or "").strip()
    if freight not in FREIGHT_MODES:
        raise InvoiceIssuanceValidationError("Informe a modalidade de transporte (CIF ou FOB).")
    weight = _parse_decimal(payload.get("weight_kg"), field="Peso", min_value=Decimal("0.001"))
    try:
        volumes = int(payload.get("volume_count"))
    except (TypeError, ValueError) as exc:
        raise InvoiceIssuanceValidationError("Informe a quantidade de volumes.") from exc
    if volumes <= 0:
        raise InvoiceIssuanceValidationError("Informe a quantidade de volumes.")
    return {
        "party_type": party["party_type"],
        "party_code": party["party_code"],
        "party_store": party["party_store"],
        "party_name": party["party_name"],
        "tax_id": party.get("tax_id"),
        "invoice_type": invoice_type,
        "invoice_type_other": other,
        "freight_mode": freight,
        "weight_kg": weight,
        "volume_count": volumes,
        "purchase_order_number": None,
        "observation": str(payload.get("observation") or "").strip() or None,
        "checklist": build_review_checklist(
            party_code=party.get("party_code"),
            party_store=party.get("party_store"),
            items=items,
            invoice_type=invoice_type,
            invoice_type_other=other,
            freight_mode=freight,
            weight_kg=weight,
            volume_count=volumes,
        ),
    }


class SearchPartiesUseCase:
    def __init__(self, lookups: Any, suppliers: Any) -> None:
        self._lookups = lookups
        self._suppliers = suppliers

    def execute(self, *, party_type: str, query: str, limit: int = 20) -> list[dict[str, Any]]:
        kind = str(party_type or "").strip()
        if kind not in PARTY_TYPES:
            raise InvoiceIssuanceValidationError("Informe se o destinatário é cliente ou fornecedor.")
        q = (query or "").strip()
        if len(q) < 2:
            raise InvoiceIssuanceValidationError("Informe ao menos 2 caracteres para pesquisar.")
        if kind == "customer":
            return self._lookups.search_customers(query=q, limit=limit)
        rows = self._suppliers.search_suppliers(query=q, limit=limit)
        return [
            {
                "party_type": "supplier",
                "party_code": row.get("supplier_code"),
                "party_store": row.get("supplier_store"),
                "party_name": row.get("supplier_name"),
                "tax_id": row.get("tax_id"),
                "blocked": bool(row.get("blocked")),
            }
            for row in rows
        ]


class SearchIssuanceProductsUseCase:
    def __init__(self, lookups: Any) -> None:
        self._lookups = lookups

    def execute(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if len(q) < 2:
            raise InvoiceIssuanceValidationError("Informe ao menos 2 caracteres para pesquisar itens.")
        return self._lookups.search_products(query=q, limit=limit)


class SearchIssuanceCarriersUseCase:
    def __init__(self, lookups: Any) -> None:
        self._lookups = lookups

    def execute(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if len(q) < 2:
            raise InvoiceIssuanceValidationError(
                "Informe ao menos 2 caracteres para pesquisar transportadora."
            )
        return self._lookups.search_carriers(query=q, limit=limit)


class GetWarehouse01BalanceUseCase:
    def __init__(self, lookups: Any) -> None:
        self._lookups = lookups

    def execute(self, *, product_code: str, branch_code: str) -> dict[str, Any]:
        code = str(product_code or "").strip()
        if not code:
            raise InvoiceIssuanceValidationError("Informe o código do item.")
        return self._lookups.get_warehouse_01_balance(
            product_code=code,
            branch_code=_require_branch(branch_code),
        )


class ListInvoiceIssuanceOpenSalesOrdersUseCase:
    """Pedidos de venda em aberto do cliente, na filial do wizard (TOTVS puro)."""

    def __init__(self, open_orders: Any) -> None:
        self._open_orders = open_orders

    def execute(
        self, *, branch_code: str, party_code: str, party_store: str
    ) -> dict[str, Any]:
        branch = _require_branch(branch_code)
        code = str(party_code or "").strip()
        store = str(party_store or "").strip()
        if not code or not store:
            raise InvoiceIssuanceValidationError(
                "Informe o cliente (código e loja) para listar pedidos em aberto."
            )
        try:
            result = self._open_orders.execute_for_customer(code, store)
        except ValueError as exc:
            raise InvoiceIssuanceValidationError(str(exc)) from exc
        raw_items = list(getattr(result, "items", None) or [])
        orders = group_open_sales_orders(raw_items, branch_code=branch)
        return {
            "branch_code": branch,
            "party_code": code,
            "party_store": store,
            "orders": orders,
            "orders_count": len(orders),
            "lines_count": sum(int(order.get("lines_count") or 0) for order in orders),
        }


class _PartyResolver:
    def __init__(self, lookups: Any, suppliers: Any) -> None:
        self._lookups = lookups
        self._suppliers = suppliers

    def resolve(self, payload: dict[str, Any]) -> dict[str, Any]:
        party_type = str(payload.get("party_type") or "").strip()
        code = str(payload.get("party_code") or "").strip()
        store = str(payload.get("party_store") or "").strip()
        if party_type not in PARTY_TYPES or not code or not store:
            raise InvoiceIssuanceValidationError("Informe o destinatário cadastrado no TOTVS.")
        if party_type == "customer":
            party = self._lookups.get_customer(party_code=code, party_store=store)
        else:
            supplier = self._suppliers.get_supplier(supplier_code=code, supplier_store=store)
            party = None
            if supplier:
                party = {
                    "party_type": "supplier",
                    "party_code": supplier["supplier_code"],
                    "party_store": supplier["supplier_store"],
                    "party_name": supplier["supplier_name"],
                    "tax_id": supplier.get("tax_id"),
                    "blocked": supplier.get("blocked"),
                }
        if party is None:
            raise PartyNotFoundError(
                "Destinatário não encontrado no Protheus. Providencie o cadastro antes de solicitar."
            )
        if party.get("blocked"):
            raise PartyBlockedError("Destinatário bloqueado não pode ser usado.")
        return party


def _snapshot_items(lookups: Any, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        product = lookups.get_product(code=item["product_code"])
        if product is None:
            raise ProductNotFoundError(f"Item {item['product_code']} não encontrado no cadastro.")
        if product.get("blocked"):
            raise InvoiceIssuanceValidationError(
                f"Item {item['product_code']} está bloqueado no cadastro."
            )
        out.append({**item, "product_description": product.get("description") or item["product_description"]})
    return out


def _resolve_carrier(lookups: Any, payload: dict[str, Any]) -> dict[str, Any]:
    code = str(payload.get("carrier_code") or "").strip() or None
    name = str(payload.get("carrier_name") or "").strip() or None
    if not code:
        return {
            **carrier_snapshot_fields(None),
            "carrier_name": name,
        }
    carrier = lookups.get_carrier(carrier_code=code)
    if carrier is None:
        raise InvoiceIssuanceValidationError("Transportadora não encontrada no Protheus.")
    if carrier.get("blocked"):
        raise InvoiceIssuanceValidationError("Transportadora bloqueada não pode ser usada.")
    return carrier_snapshot_fields(carrier)


class CreateInvoiceIssuanceRequestUseCase:
    def __init__(self, requests: Any, lookups: Any, suppliers: Any) -> None:
        self._requests = requests
        self._lookups = lookups
        self._parties = _PartyResolver(lookups, suppliers)

    def execute(self, payload: dict[str, Any], actor: Actor) -> dict[str, Any]:
        if not actor.has_create and not actor.has_process and not actor.has_manage:
            raise InvoiceIssuanceForbiddenError("Sem permissão para solicitar emissão.")
        branch = _require_branch(payload.get("branch_code") or payload.get("branch"))
        party = self._parties.resolve(payload)
        items = _snapshot_items(
            self._lookups,
            _parse_items(
                payload.get("items"),
                invoice_type=str(payload.get("invoice_type") or "").strip(),
            ),
        )
        fields = {
            **_payload_fields(payload, party, items),
            **_resolve_carrier(self._lookups, payload),
        }
        created = self._requests.create_request_with_history(
            request_fields={
                **fields,
                "branch_code": branch,
                "status": "pending",
                "created_by_user_id": actor.user_id,
                "created_by_name": format_person_name(actor.user_name),
            },
            items=items,
            history_fields={
                "event_type": "created",
                "actor_origin": "user",
                "actor_user_id": actor.user_id,
                "actor_name": actor.user_name,
                "from_status": None,
                "to_status": "pending",
                "changes": {"party_code": party["party_code"]},
            },
        )
        notify_request_created(created, actor_user_id=actor.user_id)
        return created


class ListInvoiceIssuanceRequestsUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(
        self,
        *,
        actor: Actor,
        filters: dict[str, Any],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        if not actor.can_view_all and not actor.has_create:
            raise InvoiceIssuanceForbiddenError("Sem permissão para listar solicitações.")
        owner = None if actor.can_view_all else actor.user_id
        return self._requests.list_requests(
            filters=filters,
            created_by_user_id=owner,
            page=page,
            page_size=page_size,
        )


class GetInvoiceIssuanceRequestUseCase:
    def __init__(self, requests: Any, lookups: Any | None = None) -> None:
        self._requests = requests
        self._lookups = lookups

    def execute(self, request_id: str, actor: Actor) -> dict[str, Any]:
        request = self._requests.get_request(request_id)
        if request is None:
            raise InvoiceIssuanceNotFoundError("Solicitação não encontrada.")
        is_owner = request.get("created_by_user_id") == actor.user_id
        if not actor.can_view_all and not (actor.has_create and is_owner):
            raise InvoiceIssuanceForbiddenError("Sem permissão para consultar esta solicitação.")
        code = str(request.get("carrier_code") or "").strip()
        if code and self._lookups and not request.get("carrier_address"):
            try:
                live = self._lookups.get_carrier(carrier_code=code)
            except Exception:
                live = None
            request = enrich_request_carrier(request, live)
        return {
            "request": request,
            "history": self._requests.list_history(request_id),
            "allowed_actions": allowed_actions(request, actor),
        }


class UpdateReturnedInvoiceIssuanceRequestUseCase:
    def __init__(self, requests: Any, lookups: Any, suppliers: Any) -> None:
        self._requests = requests
        self._lookups = lookups
        self._parties = _PartyResolver(lookups, suppliers)

    def execute(self, request_id: str, payload: dict[str, Any], actor: Actor) -> dict[str, Any]:
        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoiceIssuanceNotFoundError("Solicitação não encontrada.")
        is_owner = current.get("created_by_user_id") == actor.user_id
        if current.get("status") != "returned" or not (actor.has_create and is_owner):
            raise InvoiceIssuanceForbiddenError(
                "Somente o solicitante pode corrigir uma solicitação devolvida."
            )
        party = self._parties.resolve(payload)
        items = _snapshot_items(
            self._lookups,
            _parse_items(
                payload.get("items"),
                invoice_type=str(payload.get("invoice_type") or "").strip(),
            ),
        )
        fields = {
            **_payload_fields(payload, party, items),
            **_resolve_carrier(self._lookups, payload),
        }
        return self._requests.update_returned_request(
            request_id=request_id,
            request_fields=fields,
            items=items,
            history_fields={
                "event_type": "updated",
                "actor_origin": "user",
                "actor_user_id": actor.user_id,
                "actor_name": actor.user_name,
                "from_status": "returned",
                "to_status": "returned",
                "changes": {"party_code": party["party_code"]},
            },
        )


class ResubmitInvoiceIssuanceRequestUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(self, request_id: str, actor: Actor) -> dict[str, Any]:
        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoiceIssuanceNotFoundError("Solicitação não encontrada.")
        is_owner = current.get("created_by_user_id") == actor.user_id
        if current.get("status") != "returned" or not (actor.has_create and is_owner):
            raise InvoiceIssuanceInvalidTransitionError(
                "Somente solicitações devolvidas podem ser reenviadas pelo solicitante."
            )
        updated = self._requests.update_status(
            request_id=request_id,
            status="pending",
            extra={"clear_return_reason": True},
            history_fields={
                "event_type": "resubmitted",
                "actor_origin": "user",
                "actor_user_id": actor.user_id,
                "actor_name": actor.user_name,
                "from_status": "returned",
                "to_status": "pending",
            },
        )
        notify_request_created(updated, actor_user_id=actor.user_id)
        return updated


class StartInvoiceIssuanceRequestUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(self, request_id: str, actor: Actor) -> dict[str, Any]:
        current = self._require_processable(request_id, actor, {"pending"})
        return self._requests.update_status(
            request_id=request_id,
            status="in_progress",
            extra={"assignee_user_id": actor.user_id, "assignee_name": actor.user_name},
            history_fields={
                "event_type": "started",
                "actor_origin": "user",
                "actor_user_id": actor.user_id,
                "actor_name": actor.user_name,
                "from_status": current["status"],
                "to_status": "in_progress",
            },
        )

    def _require_processable(self, request_id: str, actor: Actor, statuses: set[str]) -> dict[str, Any]:
        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoiceIssuanceNotFoundError("Solicitação não encontrada.")
        if not (actor.has_process or actor.has_manage):
            raise InvoiceIssuanceForbiddenError("Sem permissão para atender esta solicitação.")
        if current.get("status") not in statuses:
            raise InvoiceIssuanceInvalidTransitionError("Transição de status não permitida.")
        return current


class ReturnInvoiceIssuanceRequestUseCase(StartInvoiceIssuanceRequestUseCase):
    def execute(self, request_id: str, actor: Actor, *, reason: str) -> dict[str, Any]:
        text = str(reason or "").strip()
        if not text:
            raise InvoiceIssuanceValidationError("Informe o motivo da devolução.")
        current = self._require_processable(request_id, actor, {"in_progress"})
        updated = self._requests.update_status(
            request_id=request_id,
            status="returned",
            extra={"return_reason": text},
            history_fields={
                "event_type": "returned",
                "actor_origin": "user",
                "actor_user_id": actor.user_id,
                "actor_name": actor.user_name,
                "from_status": current["status"],
                "to_status": "returned",
                "justification": text,
            },
        )
        notify_request_returned(updated, actor_user_id=actor.user_id)
        return updated


class IssueInvoiceIssuanceRequestUseCase(StartInvoiceIssuanceRequestUseCase):
    def execute(self, request_id: str, actor: Actor) -> dict[str, Any]:
        current = self._require_processable(request_id, actor, {"in_progress"})
        updated = self._requests.update_status(
            request_id=request_id,
            status="issued",
            extra={"issued_at": datetime.now(timezone.utc)},
            history_fields={
                "event_type": "issued",
                "actor_origin": "user",
                "actor_user_id": actor.user_id,
                "actor_name": actor.user_name,
                "from_status": current["status"],
                "to_status": "issued",
            },
        )
        notify_request_issued(updated, actor_user_id=actor.user_id)
        return updated


class CancelInvoiceIssuanceRequestUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(self, request_id: str, actor: Actor, *, justification: str) -> dict[str, Any]:
        text = str(justification or "").strip()
        if not text:
            raise InvoiceIssuanceValidationError("Informe a justificativa do cancelamento.")
        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoiceIssuanceNotFoundError("Solicitação não encontrada.")
        if current.get("status") in TERMINAL_STATUSES:
            raise InvoiceIssuanceInvalidTransitionError("Solicitação já encerrada.")
        is_owner = current.get("created_by_user_id") == actor.user_id
        allowed = (
            (actor.has_create and is_owner and current.get("status") == "pending")
            or actor.has_manage
            or (actor.has_process and current.get("status") == "in_progress")
        )
        if not allowed:
            raise InvoiceIssuanceForbiddenError("Sem permissão para cancelar esta solicitação.")
        now = datetime.now(timezone.utc)
        updated = self._requests.update_status(
            request_id=request_id,
            status="cancelled",
            extra={
                "cancelled_at": now,
                "cancelled_by_user_id": actor.user_id,
                "cancelled_by_name": actor.user_name,
                "cancel_justification": text,
            },
            history_fields={
                "event_type": "cancelled",
                "actor_origin": "user",
                "actor_user_id": actor.user_id,
                "actor_name": actor.user_name,
                "from_status": current["status"],
                "to_status": "cancelled",
                "justification": text,
            },
        )
        notify_request_cancelled(updated, actor_user_id=actor.user_id)
        return updated
