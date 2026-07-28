"""Use cases — lançamento-notas-fiscais."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence

from app.domain.services.lancamento_notas_fiscais.history_serialization import (
    history_changes_json_safe,
)
from app.application.services.lnf_portal_notification_service import notify_block_assignee
from app.shared.utils.person_name import format_person_name
from app.domain.services.lancamento_notas_fiscais.exceptions import (
    DuplicateFiscalKeyError,
    InvoicePostingConflictError,
    InvoicePostingDuplicateError,
    InvoicePostingError,
    InvoicePostingErpQueryError,
    InvoicePostingForbiddenError,
    InvoicePostingInvalidTransitionError,
    InvoicePostingNotFoundError,
    InvoicePostingReconciliationBusyError,
    InvoicePostingValidationError,
    SupplierBlockedError,
    SupplierNotFoundError,
)
from app.domain.services.lancamento_notas_fiscais.fiscal_normalization import (
    BLOCK_REASONS,
    DEFAULT_RECONCILIATION_LIMIT,
    MAX_RECONCILIATION_LIMIT,
    RECONCILIATION_REFRESH_COOLDOWN_SECONDS,
    TERMINAL_STATUSES,
    FiscalNormalizationError,
    normalize_branch,
    normalize_document,
    normalize_series,
)
from app.domain.services.lancamento_notas_fiscais.purchase_order_grouping_service import (
    find_purchase_order_group,
    format_linked_po_label,
    format_linked_po_labels,
    group_open_purchase_order_lines,
    linked_po_snapshots_from_request,
)
from app.domain.services.lancamento_notas_fiscais.reconciliation_matching import (
    classify_candidates,
    parse_erp_entry_date,
)

COMMENT_MAX_LEN = 4000
_FISCAL_KEY_FIELDS = frozenset(
    {
        "branch_code",
        "document_number",
        "document_match_key",
        "series",
        "supplier_code",
        "supplier_store",
    }
)


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


def _field_values_equal(old: Any, new: Any) -> bool:
    """Compara valor persistido (já serializado na leitura) com valor tipado do update."""
    if old is None and new is None:
        return True
    if isinstance(new, Decimal):
        try:
            return Decimal(str(old)) == new
        except (InvalidOperation, TypeError, ValueError):
            return False
    if isinstance(new, datetime):
        try:
            parsed = _parse_datetime(old, field="campo")
        except InvoicePostingValidationError:
            return False
        return parsed == new
    if isinstance(new, date) and not isinstance(new, datetime):
        try:
            parsed = _parse_date(old, field="campo")
        except InvoicePostingValidationError:
            return False
        return parsed == new
    return str(old if old is not None else "") == str(
        new if new is not None else ""
    )


def _parse_amount(raw: Any) -> Decimal:
    text = str(raw if raw is not None else "").strip()
    if not text:
        raise InvoicePostingValidationError("Valor da nota inválido.")
    # Aceita formato BR (1.234,56) e ponto decimal (1234.56).
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise InvoicePostingValidationError("Valor da nota inválido.") from exc
    if value < 0:
        raise InvoicePostingValidationError("Valor da nota não pode ser negativo.")
    return value.quantize(Decimal("0.01"))


def _parse_date(raw: Any, *, field: str) -> date:
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    text = str(raw or "").strip()
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise InvoicePostingValidationError(f"{field} inválida.") from exc


def _parse_datetime(raw: Any, *, field: str) -> datetime:
    if isinstance(raw, datetime):
        return raw
    text = str(raw or "").strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise InvoicePostingValidationError(f"{field} inválida.") from exc


def _raise_duplicate(existing: dict[str, Any] | None) -> None:
    meta = {}
    if existing:
        meta = {
            "existing_request_id": existing.get("id"),
            "existing_status": existing.get("status"),
        }
    raise InvoicePostingDuplicateError(
        "Já existe solicitação ativa com a mesma chave fiscal.",
        meta=meta,
    )


def allowed_actions(request: dict[str, Any], actor: Actor) -> list[str]:
    status = request.get("status")
    is_owner = request.get("created_by_user_id") == actor.user_id
    actions: list[str] = []
    if status in TERMINAL_STATUSES:
        if actor.can_view_all or is_owner:
            actions.append("view")
        return actions

    if actor.can_view_all or is_owner:
        actions.append("view")
    if status in {"pending", "blocked"} and (
        (actor.has_create and is_owner) or actor.has_process or actor.has_manage
    ):
        actions.append("edit")
    if status == "pending" and (actor.has_process or actor.has_manage):
        actions.append("start")
    if status in {"pending", "in_progress"} and (actor.has_process or actor.has_manage):
        actions.append("block")
    if status == "blocked" and (actor.has_process or actor.has_manage):
        actions.append("resume")
    if status not in TERMINAL_STATUSES and (actor.has_process or actor.has_manage):
        actions.append("post_manual")
        actions.append("link_purchase_order")
    if (actor.has_create and is_owner and status == "pending") or (
        actor.has_manage and status not in TERMINAL_STATUSES
    ):
        actions.append("cancel")
    if actor.has_create and is_owner or actor.has_process or actor.has_manage:
        actions.append("comment")
    return actions


class SearchSuppliersUseCase:
    def __init__(self, suppliers: Any) -> None:
        self._suppliers = suppliers

    def execute(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if len(q) < 2:
            raise InvoicePostingValidationError(
                "Informe ao menos 2 caracteres para pesquisar fornecedores."
            )
        return self._suppliers.search_suppliers(query=q, limit=limit)


class CreateInvoicePostingRequestUseCase:
    def __init__(self, requests: Any, suppliers: Any) -> None:
        self._requests = requests
        self._suppliers = suppliers

    def execute(self, payload: dict[str, Any], actor: Actor) -> dict[str, Any]:
        try:
            branch = normalize_branch(payload.get("branch_code") or payload.get("branch"))
            document = normalize_document(
                payload.get("document_number") or payload.get("document")
            )
            series = normalize_series(payload.get("series"), required=True)
        except FiscalNormalizationError as exc:
            raise InvoicePostingValidationError(str(exc)) from exc

        supplier_code = str(payload.get("supplier_code") or "").strip()
        supplier_store = str(payload.get("supplier_store") or "").strip()
        if not supplier_code or not supplier_store:
            raise InvoicePostingValidationError("Informe código e loja do fornecedor.")

        supplier = self._suppliers.get_supplier(
            supplier_code=supplier_code, supplier_store=supplier_store
        )
        if supplier is None:
            raise SupplierNotFoundError("Fornecedor não encontrado no Protheus.")
        if supplier.get("blocked"):
            raise SupplierBlockedError("Fornecedor bloqueado não pode ser usado.")

        amount = _parse_amount(payload.get("amount"))
        issue_date = _parse_date(payload.get("issue_date"), field="Data de emissão")
        received_at = _parse_datetime(
            payload.get("received_at"), field="Data/hora de recebimento"
        )
        observation = str(payload.get("observation") or "").strip() or None

        duplicate = self._requests.find_active_by_fiscal_key(
            branch_code=branch,
            supplier_code=supplier["supplier_code"],
            supplier_store=supplier["supplier_store"],
            document_match_key=document.document_match_key,
            series=series,
        )
        if duplicate:
            _raise_duplicate(duplicate)

        fields = {
            "branch_code": branch,
            "document_number": document.document_number,
            "document_match_key": document.document_match_key,
            "series": series,
            "supplier_code": supplier["supplier_code"],
            "supplier_store": supplier["supplier_store"],
            "supplier_name": supplier["supplier_name"],
            "supplier_short_name": supplier.get("supplier_short_name"),
            "issue_date": issue_date,
            "amount": amount,
            "received_at": received_at,
            "observation": observation,
            "status": "pending",
            "created_by_user_id": actor.user_id,
            "created_by_name": actor.user_name,
        }
        history = {
            "event_type": "created",
            "actor_origin": "user",
            "actor_user_id": actor.user_id,
            "actor_name": actor.user_name,
            "from_status": None,
            "to_status": "pending",
            "changes": {
                "branch_code": branch,
                "document_number": document.document_number,
                "document_match_key": document.document_match_key,
                "series": series,
                "supplier_code": supplier["supplier_code"],
                "supplier_store": supplier["supplier_store"],
            },
            "justification": None,
        }
        try:
            return self._requests.create_request_with_history(
                request_fields=fields,
                history_fields=history,
            )
        except DuplicateFiscalKeyError:
            existing = self._requests.find_active_by_fiscal_key(
                branch_code=branch,
                supplier_code=supplier["supplier_code"],
                supplier_store=supplier["supplier_store"],
                document_match_key=document.document_match_key,
                series=series,
            )
            _raise_duplicate(existing)


class ListInvoicePostingRequestsUseCase:
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
            raise InvoicePostingForbiddenError("Sem permissão para consultar solicitações.")
        owner_filter = None if actor.can_view_all else actor.user_id
        return self._requests.list_requests(
            filters=filters,
            created_by_user_id=owner_filter,
            page=page,
            page_size=page_size,
        )


class GetInvoicePostingRequestUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(self, request_id: str, actor: Actor) -> dict[str, Any]:
        request = self._requests.get_request(request_id)
        if request is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")
        is_owner = request.get("created_by_user_id") == actor.user_id
        if not actor.can_view_all and not (actor.has_create and is_owner):
            raise InvoicePostingForbiddenError("Sem permissão para consultar esta solicitação.")
        return {
            "request": request,
            "history": self._requests.list_history(request_id),
            "comments": self._requests.list_comments(request_id),
            "allowed_actions": allowed_actions(request, actor),
        }


class ListRequestOpenPurchaseOrdersUseCase:
    """Lista pedidos de compra abertos (SC7) agrupados por PC + data de entrega."""

    def __init__(self, requests: Any, purchase_orders: Any) -> None:
        self._requests = requests
        self._purchase_orders = purchase_orders

    def execute(self, request_id: str, actor: Actor) -> dict[str, Any]:
        request = self._requests.get_request(request_id)
        if request is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")
        is_owner = request.get("created_by_user_id") == actor.user_id
        if not actor.can_view_all and not (actor.has_create and is_owner):
            raise InvoicePostingForbiddenError(
                "Sem permissão para consultar pedidos desta solicitação."
            )

        branch = str(request.get("branch_code") or "").strip()
        supplier_code = str(request.get("supplier_code") or "").strip()
        supplier_store = str(request.get("supplier_store") or "").strip()
        items = self._purchase_orders.list_open_purchase_orders_by_supplier(
            branch_code=branch,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
        )
        groups = group_open_purchase_order_lines(items)
        order_numbers = sorted(
            {
                str(group.get("order_number") or "").strip()
                for group in groups
                if group.get("order_number")
            }
        )
        return {
            "request_id": request_id,
            "branch_code": branch,
            "supplier_code": supplier_code,
            "supplier_store": supplier_store,
            "supplier_name": request.get("supplier_name"),
            "order_count": len(order_numbers),
            "group_count": len(groups),
            "item_count": len(items),
            "groups": groups,
            "linked": linked_po_snapshots_from_request(request),
            "can_link": "link_purchase_order" in allowed_actions(request, actor),
        }


class LinkRequestPurchaseOrderUseCase:
    """Substitui o conjunto de grupos de PC amarrados à solicitação."""

    def __init__(self, requests: Any, purchase_orders: Any) -> None:
        self._requests = requests
        self._purchase_orders = purchase_orders

    def execute(
        self,
        request_id: str,
        actor: Actor,
        *,
        groups: list[dict[str, Any]] | None = None,
        order_number: str | None = None,
        delivery_date: str | None = None,
    ) -> dict[str, Any]:
        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")
        if current["status"] in TERMINAL_STATUSES:
            raise InvoicePostingInvalidTransitionError(
                "Solicitação terminal não pode amarrar pedido de compra."
            )
        if not (actor.has_process or actor.has_manage):
            raise InvoicePostingForbiddenError(
                "Sem permissão para amarrar pedido de compra."
            )

        wanted = self._normalize_wanted_groups(
            groups=groups,
            order_number=order_number,
            delivery_date=delivery_date,
        )

        previous = linked_po_snapshots_from_request(current)
        branch = str(current.get("branch_code") or "").strip()
        supplier_code = str(current.get("supplier_code") or "").strip()
        supplier_store = str(current.get("supplier_store") or "").strip()

        resolved_rows: list[dict[str, Any]] = []
        if wanted:
            items = self._purchase_orders.list_open_purchase_orders_by_supplier(
                branch_code=branch,
                supplier_code=supplier_code,
                supplier_store=supplier_store,
            )
            open_groups = group_open_purchase_order_lines(items)
            linked_at = datetime.now(timezone.utc)
            seen: set[tuple[str, str | None]] = set()
            for item in wanted:
                key = (item["order_number"], item["delivery_date"])
                if key in seen:
                    continue
                seen.add(key)
                group = find_purchase_order_group(
                    open_groups,
                    order_number=item["order_number"],
                    delivery_date=item["delivery_date"],
                )
                if group is None:
                    label = format_linked_po_label(
                        order_number=item["order_number"],
                        delivery_date=item["delivery_date"],
                    )
                    raise InvoicePostingValidationError(
                        f"Pedido de compra informado não está aberto para este fornecedor: {label}."
                    )
                issue_raw = group.get("issue_date")
                issue_date = (
                    _parse_date(issue_raw, field="Data de emissão do pedido")
                    if issue_raw
                    else None
                )
                delivery_key = item["delivery_date"]
                parsed_delivery = (
                    _parse_date(delivery_key, field="Data de entrega do pedido")
                    if delivery_key
                    else None
                )
                resolved_rows.append(
                    {
                        "order_number": group["order_number"],
                        "delivery_date": parsed_delivery,
                        "issue_date": issue_date,
                        "open_value": group.get("open_value"),
                        "product_count": group.get("product_count"),
                        "linked_at": linked_at,
                        "linked_by_user_id": actor.user_id,
                        "linked_by_name": actor.user_name,
                    }
                )

        to_snapshots = [
            {
                "order_number": row["order_number"],
                "delivery_date": (
                    row["delivery_date"].isoformat()
                    if isinstance(row.get("delivery_date"), date)
                    else row.get("delivery_date")
                ),
                "issue_date": (
                    row["issue_date"].isoformat()
                    if isinstance(row.get("issue_date"), date)
                    else row.get("issue_date")
                ),
                "open_value": row.get("open_value"),
                "product_count": row.get("product_count"),
                "linked_at": (
                    row["linked_at"].isoformat()
                    if isinstance(row.get("linked_at"), datetime)
                    else row.get("linked_at")
                ),
                "linked_by_user_id": row.get("linked_by_user_id"),
                "linked_by_name": row.get("linked_by_name"),
            }
            for row in resolved_rows
        ]

        label_from = format_linked_po_labels(previous)
        label_to = format_linked_po_labels(to_snapshots)
        if previous and to_snapshots:
            justification = f"Pedidos amarrados: {label_from} → {label_to}"
        elif to_snapshots:
            justification = f"Pedidos amarrados: {label_to}"
        elif previous:
            justification = f"Pedidos desamarrados: {label_from}"
        else:
            justification = "Pedidos amarrados: (nenhum)"

        first = resolved_rows[0] if resolved_rows else None
        mirror_updates = {
            "linked_po_number": first["order_number"] if first else None,
            "linked_po_delivery_date": first.get("delivery_date") if first else None,
            "linked_po_issue_date": first.get("issue_date") if first else None,
            "linked_po_open_value": first.get("open_value") if first else None,
            "linked_po_product_count": first.get("product_count") if first else None,
            "linked_po_linked_at": first.get("linked_at") if first else None,
            "linked_po_linked_by_user_id": first.get("linked_by_user_id") if first else None,
            "linked_po_linked_by_name": first.get("linked_by_name") if first else None,
        }

        history_fields = {
            "event_type": "purchase_order_linked",
            "actor_origin": "user",
            "actor_user_id": actor.user_id,
            "actor_name": actor.user_name,
            "from_status": current["status"],
            "to_status": current["status"],
            "changes": history_changes_json_safe(
                {"linked_po": {"from": previous, "to": to_snapshots}}
            ),
            "justification": justification,
        }

        if hasattr(self._requests, "replace_linked_purchase_orders"):
            return self._requests.replace_linked_purchase_orders(
                request_id=request_id,
                rows=resolved_rows,
                history_fields=history_fields,
                mirror_updates=mirror_updates,
            )

        # Fallback (testes sem junction): espelha só o primeiro e lista em memória
        updated = self._requests.update_request_with_history(
            request_id=request_id,
            updates=mirror_updates,
            history_fields=history_fields,
        )
        if hasattr(self._requests, "set_linked_purchase_orders"):
            self._requests.set_linked_purchase_orders(request_id, to_snapshots)
            refreshed = self._requests.get_request(request_id)
            return refreshed or updated
        updated["linked_purchase_orders"] = to_snapshots
        return updated

    @staticmethod
    def _normalize_wanted_groups(
        *,
        groups: list[dict[str, Any]] | None,
        order_number: str | None,
        delivery_date: str | None,
    ) -> list[dict[str, str | None]]:
        raw_groups: list[dict[str, Any]]
        if groups is not None:
            raw_groups = list(groups)
        elif order_number is not None:
            raw_groups = [
                {"order_number": order_number, "delivery_date": delivery_date}
            ]
        else:
            raise InvoicePostingValidationError(
                "Informe os pedidos de compra a amarrar."
            )

        wanted: list[dict[str, str | None]] = []
        for item in raw_groups:
            number = str(item.get("order_number") or "").strip()
            if not number:
                raise InvoicePostingValidationError(
                    "Informe o número do pedido de compra."
                )
            raw_delivery = item.get("delivery_date")
            if raw_delivery is not None and str(raw_delivery).strip() == "":
                raw_delivery = None
            delivery_key: str | None = None
            if raw_delivery is not None:
                parsed = _parse_date(
                    raw_delivery, field="Data de entrega do pedido"
                )
                delivery_key = parsed.isoformat()
            wanted.append(
                {"order_number": number, "delivery_date": delivery_key}
            )
        return wanted


class UpdateInvoicePostingRequestUseCase:
    def __init__(
        self,
        requests: Any,
        suppliers: Any,
        reconciler: Any | None = None,
    ) -> None:
        self._requests = requests
        self._suppliers = suppliers
        self._reconciler = reconciler

    def execute(
        self, request_id: str, payload: dict[str, Any], actor: Actor
    ) -> dict[str, Any]:
        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")
        if current["status"] in TERMINAL_STATUSES:
            raise InvoicePostingInvalidTransitionError(
                "Solicitação terminal não pode ser corrigida."
            )

        is_owner = current["created_by_user_id"] == actor.user_id
        if actor.has_manage or actor.has_process:
            pass
        elif actor.has_create and is_owner and current["status"] in {"pending", "blocked"}:
            pass
        else:
            raise InvoicePostingForbiddenError("Sem permissão para corrigir esta solicitação.")

        updates: dict[str, Any] = {}
        changes: dict[str, Any] = {}

        def _set(field: str, new_value: Any) -> None:
            old = current.get(field)
            if not _field_values_equal(old, new_value):
                updates[field] = new_value
                changes[field] = {"from": old, "to": new_value}

        try:
            if "branch_code" in payload or "branch" in payload:
                branch = normalize_branch(
                    payload.get("branch_code", payload.get("branch", current["branch_code"]))
                )
                _set("branch_code", branch)
            if "document_number" in payload or "document" in payload:
                document = normalize_document(
                    payload.get(
                        "document_number",
                        payload.get("document", current["document_number"]),
                    )
                )
                _set("document_number", document.document_number)
                _set("document_match_key", document.document_match_key)
            if "series" in payload:
                _set("series", normalize_series(payload.get("series"), required=True))
        except FiscalNormalizationError as exc:
            raise InvoicePostingValidationError(str(exc)) from exc

        supplier_code = current["supplier_code"]
        supplier_store = current["supplier_store"]
        supplier_changed = False
        if "supplier_code" in payload:
            supplier_code = str(payload.get("supplier_code") or "").strip()
            supplier_changed = True
        if "supplier_store" in payload:
            supplier_store = str(payload.get("supplier_store") or "").strip()
            supplier_changed = True
        if supplier_changed:
            supplier = self._suppliers.get_supplier(
                supplier_code=supplier_code, supplier_store=supplier_store
            )
            if supplier is None:
                raise SupplierNotFoundError("Fornecedor não encontrado no Protheus.")
            if supplier.get("blocked"):
                raise SupplierBlockedError("Fornecedor bloqueado não pode ser usado.")
            _set("supplier_code", supplier["supplier_code"])
            _set("supplier_store", supplier["supplier_store"])
            _set("supplier_name", supplier["supplier_name"])
            _set("supplier_short_name", supplier.get("supplier_short_name"))

        if "issue_date" in payload:
            _set("issue_date", _parse_date(payload.get("issue_date"), field="Data de emissão"))
        if "amount" in payload:
            _set("amount", _parse_amount(payload.get("amount")))
        if "received_at" in payload:
            _set(
                "received_at",
                _parse_datetime(payload.get("received_at"), field="Recebimento"),
            )
        if "observation" in payload:
            obs = str(payload.get("observation") or "").strip() or None
            _set("observation", obs)

        if not updates:
            return current

        branch = updates.get("branch_code", current["branch_code"])
        supplier_code = updates.get("supplier_code", current["supplier_code"])
        supplier_store = updates.get("supplier_store", current["supplier_store"])
        document_match_key = updates.get(
            "document_match_key", current["document_match_key"]
        )
        series = updates.get("series", current["series"])
        duplicate = self._requests.find_active_by_fiscal_key(
            branch_code=branch,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            document_match_key=document_match_key,
            series=series,
            exclude_id=request_id,
        )
        if duplicate:
            _raise_duplicate(duplicate)

        history = {
            "event_type": "updated",
            "actor_origin": "user",
            "actor_user_id": actor.user_id,
            "actor_name": actor.user_name,
            "from_status": current["status"],
            "to_status": current["status"],
            "changes": history_changes_json_safe(changes),
            "justification": None,
        }
        try:
            updated = self._requests.update_request_with_history(
                request_id=request_id,
                updates=updates,
                history_fields=history,
            )
        except DuplicateFiscalKeyError:
            existing = self._requests.find_active_by_fiscal_key(
                branch_code=branch,
                supplier_code=supplier_code,
                supplier_store=supplier_store,
                document_match_key=document_match_key,
                series=series,
                exclude_id=request_id,
            )
            if existing is None:
                raise InvoicePostingDuplicateError(
                    "Já existe solicitação ativa com a mesma chave fiscal."
                ) from None
            _raise_duplicate(existing)

        fiscal_changed = bool(_FISCAL_KEY_FIELDS.intersection(updates))
        if fiscal_changed and self._reconciler is not None:
            try:
                self._reconciler.try_reconcile_requests([request_id])
            except Exception:
                # Correção já persistida — falha de ERP não deve derrubar o PATCH.
                pass
            refreshed = self._requests.get_request(request_id)
            if refreshed is not None:
                return refreshed
        return updated


class StartInvoicePostingRequestUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(self, request_id: str, actor: Actor) -> dict[str, Any]:
        if not (actor.has_process or actor.has_manage):
            raise InvoicePostingForbiddenError("Sem permissão para iniciar atendimento.")
        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")

        if current["status"] == "in_progress":
            if current.get("assignee_user_id") == actor.user_id:
                return current
            if actor.has_manage:
                pass  # admin pode reassumir
            else:
                raise InvoicePostingConflictError(
                    "Solicitação já atribuída a outro responsável.",
                    meta={"assignee_user_id": current.get("assignee_user_id")},
                )
        elif current["status"] != "pending":
            raise InvoicePostingInvalidTransitionError(
                "Somente solicitações pending podem ser iniciadas."
            )

        updates = {
            "status": "in_progress",
            "assignee_user_id": actor.user_id,
            "assignee_name": actor.user_name,
        }
        history = {
            "event_type": "status_changed",
            "actor_origin": "user",
            "actor_user_id": actor.user_id,
            "actor_name": actor.user_name,
            "from_status": current["status"],
            "to_status": "in_progress",
            "changes": {
                "assignee_user_id": {
                    "from": current.get("assignee_user_id"),
                    "to": actor.user_id,
                }
            },
            "justification": None,
        }
        return self._requests.update_request_with_history(
            request_id=request_id, updates=updates, history_fields=history
        )


class BlockInvoicePostingRequestUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(
        self,
        request_id: str,
        *,
        actor: Actor,
        block_reason: str,
        block_description: str,
        assignee_user_id: str,
        assignee_name: str,
    ) -> dict[str, Any]:
        if not (actor.has_process or actor.has_manage):
            raise InvoicePostingForbiddenError("Sem permissão para bloquear.")
        reason = str(block_reason or "").strip()
        description = str(block_description or "").strip()
        responsible_id = str(assignee_user_id or "").strip()
        responsible_name = format_person_name(str(assignee_name or "").strip())
        if reason not in BLOCK_REASONS:
            raise InvoicePostingValidationError("Motivo de bloqueio inválido.")
        if not description:
            raise InvoicePostingValidationError("Descrição do bloqueio é obrigatória.")
        if not responsible_id or not responsible_name:
            raise InvoicePostingValidationError(
                "Responsável pela correção da pendência é obrigatório."
            )

        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")
        if current["status"] not in {"pending", "in_progress"}:
            raise InvoicePostingInvalidTransitionError(
                "Somente pending ou in_progress podem ser bloqueadas."
            )

        updates = {
            "status": "blocked",
            "block_reason": reason,
            "block_description": description,
            "assignee_user_id": responsible_id,
            "assignee_name": responsible_name,
        }

        history = {
            "event_type": "status_changed",
            "actor_origin": "user",
            "actor_user_id": actor.user_id,
            "actor_name": actor.user_name,
            "from_status": current["status"],
            "to_status": "blocked",
            "changes": {
                "block_reason": reason,
                "block_description": description,
                "assignee_user_id": {
                    "from": current.get("assignee_user_id"),
                    "to": responsible_id,
                },
                "assignee_name": {
                    "from": current.get("assignee_name"),
                    "to": responsible_name,
                },
            },
            "justification": description,
        }
        updated = self._requests.update_request_with_history(
            request_id=request_id, updates=updates, history_fields=history
        )
        notify_block_assignee(
            request=updated,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
        )
        return updated


class ResumeInvoicePostingRequestUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(self, request_id: str, actor: Actor) -> dict[str, Any]:
        if not (actor.has_process or actor.has_manage):
            raise InvoicePostingForbiddenError("Sem permissão para retomar.")
        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")
        if current["status"] != "blocked":
            raise InvoicePostingInvalidTransitionError(
                "Somente solicitações blocked podem ser retomadas."
            )

        updates = {
            "status": "in_progress",
            "block_reason": None,
            "block_description": None,
            # preserva assignee_*
        }
        history = {
            "event_type": "status_changed",
            "actor_origin": "user",
            "actor_user_id": actor.user_id,
            "actor_name": actor.user_name,
            "from_status": "blocked",
            "to_status": "in_progress",
            "changes": {"block_reason": None, "block_description": None},
            "justification": None,
        }
        return self._requests.update_request_with_history(
            request_id=request_id, updates=updates, history_fields=history
        )


class CancelInvoicePostingRequestUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(
        self, request_id: str, *, actor: Actor, justification: str
    ) -> dict[str, Any]:
        text = str(justification or "").strip()
        if not text:
            raise InvoicePostingValidationError("Justificativa de cancelamento é obrigatória.")

        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")

        if current["status"] == "posted":
            raise InvoicePostingInvalidTransitionError(
                "Solicitação lançada não pode ser cancelada."
            )

        is_owner = current["created_by_user_id"] == actor.user_id
        if actor.has_manage:
            authorized = True
        elif actor.has_create and is_owner and current["status"] in {
            "pending",
            "cancelled",
        }:
            authorized = True
        else:
            authorized = False

        if not authorized:
            raise InvoicePostingForbiddenError(
                "Sem permissão para cancelar esta solicitação."
            )

        if current["status"] == "cancelled":
            return current

        now = datetime.now(timezone.utc)
        updates = {
            "status": "cancelled",
            "cancel_justification": text,
            "cancelled_at": now,
            "cancelled_by_user_id": actor.user_id,
            "cancelled_by_name": actor.user_name,
            "block_reason": None,
            "block_description": None,
        }
        history = {
            "event_type": "cancelled",
            "actor_origin": "user",
            "actor_user_id": actor.user_id,
            "actor_name": actor.user_name,
            "from_status": current["status"],
            "to_status": "cancelled",
            "changes": {},
            "justification": text,
        }
        return self._requests.update_request_with_history(
            request_id=request_id, updates=updates, history_fields=history
        )


class PostManualInvoicePostingRequestUseCase:
    """Confirmação de lançamento no Protheus quando a conciliação automática não casou."""

    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(
        self,
        request_id: str,
        *,
        actor: Actor,
        justification: str | None = None,
    ) -> dict[str, Any]:
        if not (actor.has_process or actor.has_manage):
            raise InvoicePostingForbiddenError(
                "Sem permissão para marcar a solicitação como lançada."
            )

        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")

        if current["status"] == "posted":
            return current
        if current["status"] == "cancelled":
            raise InvoicePostingInvalidTransitionError(
                "Solicitação cancelada não pode ser marcada como lançada."
            )

        text = str(justification or "").strip() or None
        now = datetime.now(timezone.utc)
        updates = {
            "status": "posted",
            "completion_source": "manual",
            "reconciled_at": now,
            "block_reason": None,
            "block_description": None,
            "divergence_alert": False,
            "divergence_detected_at": None,
            "divergence_detail": None,
        }
        history = {
            "event_type": "manual_posted",
            "actor_origin": "user",
            "actor_user_id": actor.user_id,
            "actor_name": actor.user_name,
            "from_status": current["status"],
            "to_status": "posted",
            "changes": {"completion_source": "manual"},
            "justification": text,
        }
        return self._requests.update_request_with_history(
            request_id=request_id, updates=updates, history_fields=history
        )


class AddInvoicePostingCommentUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(self, request_id: str, *, actor: Actor, body: str) -> dict[str, Any]:
        text = str(body or "").strip()
        if not text:
            raise InvoicePostingValidationError("Comentário não pode ser vazio.")
        if len(text) > COMMENT_MAX_LEN:
            raise InvoicePostingValidationError("Comentário excede o tamanho máximo.")

        current = self._requests.get_request(request_id)
        if current is None:
            raise InvoicePostingNotFoundError("Solicitação não encontrada.")
        is_owner = current["created_by_user_id"] == actor.user_id
        if not (
            (actor.has_create and is_owner)
            or actor.has_process
            or actor.has_manage
        ):
            raise InvoicePostingForbiddenError("Sem permissão para comentar.")

        return self._requests.add_comment(
            request_id=request_id,
            author_user_id=actor.user_id,
            author_name=actor.user_name,
            body=text,
        )


def resolve_reconciliation_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_RECONCILIATION_LIMIT
    try:
        value = int(limit)
    except (TypeError, ValueError) as exc:
        raise InvoicePostingValidationError(
            "Limite de conciliação inválido."
        ) from exc
    if value < 1 or value > MAX_RECONCILIATION_LIMIT:
        raise InvoicePostingValidationError(
            f"Limite deve estar entre 1 e {MAX_RECONCILIATION_LIMIT}."
        )
    return value


class RunInvoicePostingReconciliationUseCase:
    def __init__(self, requests, sf1_query) -> None:
        self._requests = requests
        self._sf1 = sf1_query

    def execute_batch(
        self,
        *,
        limit: int | None = None,
        request_ids: Sequence[str] | None = None,
        order_by: str = "fifo",
    ) -> dict[str, int]:
        """Núcleo de matching/persistência — sem lock e sem checagem de permissão."""
        resolved_limit = resolve_reconciliation_limit(limit)
        if request_ids:
            resolved_limit = max(resolved_limit, len(list(request_ids)))
            resolved_limit = min(resolved_limit, MAX_RECONCILIATION_LIMIT)
        candidates = self._requests.list_reconciliation_candidates(
            limit=resolved_limit,
            prioritize_ids=list(request_ids) if request_ids else None,
            order_by=order_by,
        )
        examined = len(candidates)
        empty = {
            "examined": examined,
            "matched": 0,
            "posted": 0,
            "not_found": 0,
            "ambiguous": 0,
            "failed": 0,
        }
        if not candidates:
            return empty

        keys = [
            {
                "branch_code": c["branch_code"],
                "supplier_code": c["supplier_code"],
                "supplier_store": c["supplier_store"],
                "document_match_key": c["document_match_key"],
                "series": c["series"],
            }
            for c in candidates
        ]

        try:
            sf1_rows = self._sf1.find_active_by_fiscal_keys(keys)
        except Exception as exc:
            raise InvoicePostingErpQueryError(
                "Falha ao consultar notas no ERP."
            ) from exc

        decisions = classify_candidates(candidates, sf1_rows)
        not_found = sum(1 for d in decisions if d.outcome == "not_found")
        ambiguous = sum(1 for d in decisions if d.outcome == "ambiguous")
        matched_decisions = [d for d in decisions if d.outcome == "matched"]
        matched = len(matched_decisions)

        batch_items: list[dict[str, Any]] = []
        for decision in matched_decisions:
            assert decision.sf1_row is not None
            batch_items.append(
                {
                    "request_id": decision.request["id"],
                    "from_status": decision.request.get("status"),
                    "sf1_recno": decision.sf1_row.get("sf1_recno"),
                    "erp_entry_date": parse_erp_entry_date(
                        decision.sf1_row.get("erp_entry_date_raw")
                    ),
                }
            )

        posted = 0
        if batch_items:
            try:
                posted = self._requests.mark_reconciled_posted_batch(batch_items)
            except Exception as exc:
                raise InvoicePostingError(
                    "Falha ao persistir conciliações."
                ) from exc

        return {
            "examined": examined,
            "matched": matched,
            "posted": posted,
            "not_found": not_found,
            "ambiguous": ambiguous,
            "failed": max(matched - posted, 0),
        }

    def try_reconcile_requests(self, request_ids: Sequence[str]) -> dict[str, int]:
        """Best-effort para 1+ IDs (ex.: após correção fiscal). Sem permissão manage."""
        ids = [str(x) for x in request_ids if str(x).strip()]
        if not ids:
            return {
                "examined": 0,
                "matched": 0,
                "posted": 0,
                "not_found": 0,
                "ambiguous": 0,
                "failed": 0,
            }
        if not self._requests.try_acquire_reconciliation_lock():
            return {
                "examined": 0,
                "matched": 0,
                "posted": 0,
                "not_found": 0,
                "ambiguous": 0,
                "failed": 0,
            }
        try:
            return self.execute_batch(
                limit=len(ids),
                request_ids=ids,
                order_by="recent",
            )
        finally:
            self._requests.release_reconciliation_lock()

    def execute(self, *, actor: Actor, limit: int | None = None) -> dict[str, int]:
        if not actor.has_manage:
            raise InvoicePostingForbiddenError(
                "Sem permissão para executar a conciliação."
            )

        if not self._requests.try_acquire_reconciliation_lock():
            raise InvoicePostingReconciliationBusyError(
                "Já existe uma conciliação em andamento."
            )

        try:
            self._requests.mark_reconciliation_refresh_started()
            return self.execute_batch(limit=limit, order_by="fifo")
        finally:
            self._requests.release_reconciliation_lock()


class RefreshInvoicePostingReconciliationUseCase:
    """Conciliação sob demanda na abertura do plugin — resposta mínima."""

    def __init__(
        self,
        requests,
        run_use_case: RunInvoicePostingReconciliationUseCase,
        *,
        cooldown_seconds: int = RECONCILIATION_REFRESH_COOLDOWN_SECONDS,
    ) -> None:
        self._requests = requests
        self._run = run_use_case
        self._cooldown_seconds = int(cooldown_seconds)

    def execute(self, *, actor: Actor) -> dict[str, Any]:
        if not actor.can_open_plugin:
            raise InvoicePostingForbiddenError(
                "Sem permissão para atualizar a fila."
            )

        if self._requests.is_reconciliation_refresh_cooldown_active(
            self._cooldown_seconds
        ):
            return {"status": "skipped", "updated": 0}

        if not self._requests.try_acquire_reconciliation_lock():
            return {"status": "skipped", "updated": 0}

        try:
            if self._requests.is_reconciliation_refresh_cooldown_active(
                self._cooldown_seconds
            ):
                return {"status": "skipped", "updated": 0}

            self._requests.mark_reconciliation_refresh_started()
            try:
                summary = self._run.execute_batch(
                    limit=DEFAULT_RECONCILIATION_LIMIT,
                    order_by="recent",
                )
            except InvoicePostingErpQueryError:
                return {"status": "failed", "updated": 0}
            except InvoicePostingError:
                return {"status": "failed", "updated": 0}

            return {
                "status": "completed",
                "updated": int(summary.get("posted") or 0),
            }
        finally:
            self._requests.release_reconciliation_lock()
