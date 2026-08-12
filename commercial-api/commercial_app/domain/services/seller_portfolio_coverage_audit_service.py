from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from commercial_app.domain.entities.portfolio_coverage import (
    CoverageGapStatus,
    CustomerOverlapWarning,
    CustomerSharedCoverageItem,
    OverlappingCustomerCoverage,
    PortfolioCoverageAudit,
    PortfolioCoverageRef,
    PortfolioOverlapSummary,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)

_GAP_UNAVAILABLE_REASON = "customer_universe_not_available"
_OVERLAP_WARNING_CODE = "customer_in_other_portfolios"
_OVERLAP_WARNING_MESSAGE = (
    "Este cliente já está vinculado a outra(s) carteira(s) ativa(s). "
    "O vínculo foi mantido; revise a cobertura se for necessário."
)


def _normalize(value: str) -> str:
    return str(value or "").strip()


def customer_coverage_key(code: str, store: str) -> tuple[str, str]:
    return (_normalize(code), _normalize(store))


class SellerPortfolioCoverageAuditService:
    """Auditoria de cobertura entre carteiras ativas (overlapping).

    Gap (cobertura 0) depende de universo de clientes operacional (ex.: TOTVS);
    sem essa fonte, o relatório marca gap como indisponível.
    """

    def audit_active_portfolios(
        self,
        portfolios: Sequence[SellerPortfolio],
    ) -> PortfolioCoverageAudit:
        active = [item for item in portfolios if item.active]
        by_customer: dict[
            tuple[str, str],
            list[tuple[PortfolioCoverageRef, str | None]],
        ] = defaultdict(list)

        for portfolio in active:
            ref = PortfolioCoverageRef(
                id=portfolio.id,
                display_name=portfolio.display_name,
            )
            seen_in_portfolio: set[tuple[str, str]] = set()
            for customer in portfolio.customers:
                key = customer_coverage_key(
                    customer.customer_code,
                    customer.customer_store,
                )
                if not key[0] or not key[1] or key in seen_in_portfolio:
                    continue
                seen_in_portfolio.add(key)
                by_customer[key].append((ref, customer.customer_name))

        overlapping: list[OverlappingCustomerCoverage] = []
        portfolio_overlap_counts: dict[str, int] = defaultdict(int)
        portfolio_names: dict[str, str] = {}

        for (code, store), entries in sorted(
            by_customer.items(),
            key=lambda item: (item[0][0], item[0][1]),
        ):
            # Dedup por portfolio_id (mesmo cliente listado 2x na mesma carteira).
            unique_refs: dict[str, PortfolioCoverageRef] = {}
            preferred_name: str | None = None
            for ref, name in entries:
                unique_refs[ref.id] = ref
                portfolio_names[ref.id] = ref.display_name
                if preferred_name is None and name:
                    preferred_name = name
            if len(unique_refs) < 2:
                continue
            refs = tuple(unique_refs.values())
            overlapping.append(
                OverlappingCustomerCoverage(
                    customer_code=code,
                    customer_store=store,
                    customer_name=preferred_name,
                    portfolios=refs,
                )
            )
            for ref in refs:
                portfolio_overlap_counts[ref.id] += 1

        portfolios_with_overlap = tuple(
            PortfolioOverlapSummary(
                id=portfolio_id,
                display_name=portfolio_names.get(portfolio_id, portfolio_id),
                overlapping_customer_count=count,
            )
            for portfolio_id, count in sorted(
                portfolio_overlap_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        )

        return PortfolioCoverageAudit(
            overlapping=tuple(overlapping),
            portfolios_with_overlap=portfolios_with_overlap,
            gap=CoverageGapStatus(
                available=False,
                reason=_GAP_UNAVAILABLE_REASON,
            ),
        )

    def find_other_active_portfolios_for_customer(
        self,
        portfolios: Sequence[SellerPortfolio],
        *,
        customer_code: str,
        customer_store: str,
        exclude_portfolio_id: str | None = None,
    ) -> tuple[PortfolioCoverageRef, ...]:
        key = customer_coverage_key(customer_code, customer_store)
        if not key[0] or not key[1]:
            return ()
        exclude = _normalize(exclude_portfolio_id or "")
        found: dict[str, PortfolioCoverageRef] = {}
        for portfolio in portfolios:
            if not portfolio.active:
                continue
            if exclude and portfolio.id == exclude:
                continue
            for customer in portfolio.customers:
                if customer_coverage_key(
                    customer.customer_code,
                    customer.customer_store,
                ) == key:
                    found[portfolio.id] = PortfolioCoverageRef(
                        id=portfolio.id,
                        display_name=portfolio.display_name,
                    )
                    break
        return tuple(found.values())

    def build_link_overlap_warning(
        self,
        other_portfolios: Iterable[PortfolioCoverageRef],
    ) -> CustomerOverlapWarning | None:
        others = tuple(other_portfolios)
        if not others:
            return None
        return CustomerOverlapWarning(
            code=_OVERLAP_WARNING_CODE,
            message=_OVERLAP_WARNING_MESSAGE,
            other_portfolios=others,
        )

    def customer_keys_overlapping_in_portfolio(
        self,
        audit: PortfolioCoverageAudit,
        portfolio_id: str,
    ) -> set[tuple[str, str]]:
        pid = _normalize(portfolio_id)
        keys: set[tuple[str, str]] = set()
        for item in audit.overlapping:
            if pid in item.portfolio_ids:
                keys.add((item.customer_code, item.customer_store))
        return keys

    def lookup_shared_customer_memberships(
        self,
        portfolios: Sequence[SellerPortfolio],
        customer_keys: Sequence[tuple[str, str]],
    ) -> tuple[CustomerSharedCoverageItem, ...]:
        """Batch: para as chaves pedidas, retorna só as que estão em 2+ carteiras ativas."""
        wanted = {
            customer_coverage_key(code, store)
            for code, store in customer_keys
            if _normalize(code) and _normalize(store)
        }
        if not wanted:
            return ()

        by_customer: dict[tuple[str, str], dict[str, PortfolioCoverageRef]] = defaultdict(
            dict
        )
        for portfolio in portfolios:
            if not portfolio.active:
                continue
            ref = PortfolioCoverageRef(
                id=portfolio.id,
                display_name=portfolio.display_name,
            )
            seen_in_portfolio: set[tuple[str, str]] = set()
            for customer in portfolio.customers:
                key = customer_coverage_key(
                    customer.customer_code,
                    customer.customer_store,
                )
                if key not in wanted or key in seen_in_portfolio:
                    continue
                seen_in_portfolio.add(key)
                by_customer[key][ref.id] = ref

        items: list[CustomerSharedCoverageItem] = []
        for code, store in sorted(wanted, key=lambda item: (item[0], item[1])):
            refs = tuple(by_customer.get((code, store), {}).values())
            if len(refs) < 2:
                continue
            items.append(
                CustomerSharedCoverageItem(
                    customer_code=code,
                    customer_store=store,
                    portfolios=refs,
                )
            )
        return tuple(items)


def assignment_key(customer: SellerCustomerAssignment) -> tuple[str, str]:
    return customer_coverage_key(customer.customer_code, customer.customer_store)
