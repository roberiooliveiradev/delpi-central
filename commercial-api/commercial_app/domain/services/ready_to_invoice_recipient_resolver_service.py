"""Resolve notification recipients for ready_to_invoice entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from commercial_app.domain.entities.seller_portfolio import SellerPortfolio
from commercial_app.domain.services.ready_to_invoice_notification_content_service import (
    ReadyToInvoiceNotificationContentService,
)


def _customer_pair(item: Mapping[str, Any]) -> tuple[str, str]:
    code = str(
        item.get("codigo_cadastro") or item.get("codigo_cliente") or ""
    ).strip()
    store = str(item.get("loja_cadastro") or "").strip()
    return (code, store)


@dataclass(frozen=True, slots=True)
class ReadyToInvoiceRecipients:
    seller_user_ids: frozenset[str]
    billing_user_ids: frozenset[str]
    billing_permission_codes: tuple[str, ...]

    @property
    def all_user_ids(self) -> frozenset[str]:
        return self.seller_user_ids | self.billing_user_ids


class ReadyToInvoiceRecipientResolverService:
    """Sellers via portfolio membership; billing via declarative content config."""

    def __init__(
        self,
        *,
        billing_user_ids: Sequence[str] | None = None,
        billing_permission_codes: Sequence[str] | None = None,
    ) -> None:
        content = ReadyToInvoiceNotificationContentService
        self._billing_user_ids = frozenset(
            str(uid).strip()
            for uid in (
                billing_user_ids
                if billing_user_ids is not None
                else content.billing_user_ids()
            )
            if str(uid).strip()
        )
        self._billing_permission_codes = tuple(
            str(code).strip()
            for code in (
                billing_permission_codes
                if billing_permission_codes is not None
                else content.billing_permission_codes()
            )
            if str(code).strip()
        )

    def build_customer_sellers_index(
        self,
        portfolios: Sequence[SellerPortfolio],
    ) -> dict[tuple[str, str], frozenset[str]]:
        index: dict[tuple[str, str], set[str]] = {}
        for portfolio in portfolios:
            if not portfolio.active:
                continue
            member_ids = {
                str(member.user_id).strip()
                for member in portfolio.members
                if str(member.user_id).strip()
            }
            owner = str(portfolio.owner_user_id or portfolio.user_id or "").strip()
            if owner:
                member_ids.add(owner)
            if not member_ids:
                continue
            for customer in portfolio.customers:
                key = (
                    str(customer.customer_code or "").strip(),
                    str(customer.customer_store or "").strip(),
                )
                if not key[0] or not key[1]:
                    continue
                bucket = index.setdefault(key, set())
                bucket.update(member_ids)
        return {key: frozenset(users) for key, users in index.items()}

    def resolve_for_item(
        self,
        item: Mapping[str, Any],
        *,
        customer_sellers: Mapping[tuple[str, str], frozenset[str]],
    ) -> ReadyToInvoiceRecipients:
        sellers = customer_sellers.get(_customer_pair(item), frozenset())
        return ReadyToInvoiceRecipients(
            seller_user_ids=sellers,
            billing_user_ids=self._billing_user_ids,
            billing_permission_codes=self._billing_permission_codes,
        )
