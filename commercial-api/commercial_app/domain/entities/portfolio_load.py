from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TotvsLoadMetricsStatus:
    """Valor aberto / atenção dependem de agregação TOTVS (api-delpi).

    MVP E6.2: indisponível até wiring barato de open-orders por carteira.
    """

    available: bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PortfolioLoadItem:
    id: str
    display_name: str
    active: bool
    customer_count: int
    member_count: int
    open_value: float | None = None
    attention_count: int | None = None


@dataclass(frozen=True, slots=True)
class PersonLoadItem:
    user_id: str
    portfolio_ids: tuple[str, ...]
    portfolio_count: int
    customer_count: int
    open_value: float | None = None
    attention_count: int | None = None


@dataclass(frozen=True, slots=True)
class PortfolioLoadSummary:
    portfolios: tuple[PortfolioLoadItem, ...]
    by_person: tuple[PersonLoadItem, ...]
    totvs_metrics: TotvsLoadMetricsStatus
