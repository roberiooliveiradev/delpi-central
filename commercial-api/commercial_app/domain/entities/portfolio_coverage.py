from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortfolioCoverageRef:
    id: str
    display_name: str


@dataclass(frozen=True, slots=True)
class OverlappingCustomerCoverage:
    customer_code: str
    customer_store: str
    customer_name: str | None
    portfolios: tuple[PortfolioCoverageRef, ...]

    @property
    def portfolio_ids(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.portfolios)


@dataclass(frozen=True, slots=True)
class PortfolioOverlapSummary:
    id: str
    display_name: str
    overlapping_customer_count: int


@dataclass(frozen=True, slots=True)
class UncoveredCustomer:
    customer_code: str
    customer_store: str
    customer_name: str | None = None
    open_value: float | None = None


@dataclass(frozen=True, slots=True)
class CoverageGapStatus:
    """Gap = clientes do universo operacional em 0 carteiras ativas."""

    available: bool
    reason: str | None = None
    universe: str | None = None
    uncovered_count: int = 0
    uncovered: tuple[UncoveredCustomer, ...] = ()


@dataclass(frozen=True, slots=True)
class PortfolioCoverageAudit:
    overlapping: tuple[OverlappingCustomerCoverage, ...]
    portfolios_with_overlap: tuple[PortfolioOverlapSummary, ...]
    gap: CoverageGapStatus

    @property
    def overlapping_count(self) -> int:
        return len(self.overlapping)


@dataclass(frozen=True, slots=True)
class CustomerOverlapWarning:
    code: str
    message: str
    other_portfolios: tuple[PortfolioCoverageRef, ...]


@dataclass(frozen=True, slots=True)
class CustomerSharedCoverageItem:
    """Cliente presente em 2+ carteiras ativas do escopo (E6.4)."""

    customer_code: str
    customer_store: str
    portfolios: tuple[PortfolioCoverageRef, ...]

    @property
    def shared(self) -> bool:
        return len(self.portfolios) >= 2
