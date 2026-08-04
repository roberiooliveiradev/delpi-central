from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from app.domain.entities.pedidos_venda_abertos.customer_outbound_invoice import (
    CustomerOutboundInvoicesPage,
)
from app.domain.ports.pedidos_venda_abertos.customer_outbound_invoices_repository_port import (
    CustomerOutboundInvoicesRepositoryPort,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def _parse_iso_date(value: str, field_name: str) -> date:
    text = (value or "").strip()
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(f"Parâmetro '{field_name}' inválido. Use AAAA-MM-DD.") from exc


def default_period_last_days(days: int = 90) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


@dataclass(frozen=True)
class ListCustomerOutboundInvoicesRequest:
    customer_code: str
    customer_store: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    page_size: int = 20
    situation: Optional[str] = None
    search: Optional[str] = None


class ListCustomerOutboundInvoicesUseCase:
    MAX_PAGE_SIZE = 100

    def __init__(self, repository: CustomerOutboundInvoicesRepositoryPort):
        self._repository = repository

    def execute(self, request: ListCustomerOutboundInvoicesRequest) -> CustomerOutboundInvoicesPage:
        code = (request.customer_code or "").strip()
        store = (request.customer_store or "").strip()
        if not code:
            raise ValueError("Código do cliente é obrigatório.")
        if not store:
            raise ValueError("Loja do cliente é obrigatória.")

        default_start, default_end = default_period_last_days(90)
        start_raw = (request.start_date or "").strip() or default_start
        end_raw = (request.end_date or "").strip() or default_end
        start = _parse_iso_date(start_raw, "start_date")
        end = _parse_iso_date(end_raw, "end_date")
        if start > end:
            raise ValueError("Período inválido: start_date não pode ser maior que end_date.")

        page = max(int(request.page or 1), 1)
        page_size = int(request.page_size or 20)
        if page_size < 1:
            raise ValueError("page_size deve ser >= 1.")
        if page_size > self.MAX_PAGE_SIZE:
            raise ValueError(f"page_size máximo permitido é {self.MAX_PAGE_SIZE}.")

        situation = (request.situation or "all").strip().lower()
        if situation not in {"all", "emitted", "return", "devolucao", "devolução"}:
            raise ValueError(
                "situation inválida. Use: all, emitted ou return."
            )

        search = (request.search or "").strip() or None

        qb = QueryBuilder()
        start_protheus = qb.convert_date_to_protheus(start.isoformat())
        end_protheus = qb.convert_date_to_protheus(end.isoformat())
        if not start_protheus or not end_protheus:
            raise ValueError("Não foi possível converter o período para o formato do Protheus.")

        return self._repository.list_customer_outbound_invoices(
            customer_code=code,
            customer_store=store,
            start_date=start_protheus,
            end_date=end_protheus,
            page=page,
            page_size=page_size,
            situation=situation,
            search=search,
        )
