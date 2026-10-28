"""Ports de leitura das fontes oficiais da Visão geral (F3.OVERVIEW).

Um port por família de indicadores com backend oficial comprovado no
G0 (doc 18): `lmp` e `transforma` via api-delpi Engineering, mais o
port de scores do Strategic Indicators para IDD. O use case não
conhece campos de sistemas downstream nem reproduz regras de domínio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from engineering_app.application.models.overview import OverviewIndicator
from engineering_app.application.ports.home_sources import HomeSourceContext

FetchStatus = Literal["available", "empty", "unavailable", "forbidden"]


@dataclass(frozen=True)
class OverviewQuery:
    """Filtros já validados na borda HTTP — ISO dates, YYYY-MM, branch."""

    start_date: str | None = None
    end_date: str | None = None
    competence: str | None = None
    branch: str | None = None


@dataclass(frozen=True)
class IndicatorFetch:
    """Resultado normalizado de uma família de indicadores."""

    status: FetchStatus
    indicators: tuple[OverviewIndicator, ...] = ()
    reason: str | None = None
    message: str | None = None


class OverviewFamilySource(Protocol):
    """Fonte oficial de uma família de indicadores da Visão geral."""

    system: str
    endpoint: str

    async def fetch(
        self, ctx: HomeSourceContext, *, query: OverviewQuery
    ) -> IndicatorFetch:
        """Lê os indicadores da família em nome do usuário.

        O adapter traduz o resultado para IndicatorFetch:
        - available/empty conforme o owner responder;
        - forbidden quando o owner negar acesso (401/403 downstream);
        - unavailable com reason para transporte/timeout/contrato.
        """
        ...


class OverviewSiSource(Protocol):
    """Scores do Strategic Indicators (owner de metas/IDD)."""

    system: str
    endpoint: str

    async def fetch_scores(
        self, ctx: HomeSourceContext, *, query: OverviewQuery
    ) -> dict[str, float] | None:
        """Mapa indicator_id → score oficial; None quando indisponível
        ou negado — ausência de IDD nunca apaga os indicadores."""
        ...
