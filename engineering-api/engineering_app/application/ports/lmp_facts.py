"""Port de leitura do contrato facts LMP (F-LMP-01..04, api-delpi).

A Engineering API consome exclusivamente os contratos oficiais facts —
nenhum SQL, nenhum repositório TOTVS, nenhum import de `app.*`. O adapter
traduz envelope/erros para estados honestos (`LmpFactsResult.status`).
"""

from __future__ import annotations

from typing import Protocol

from engineering_app.application.models.lmp import (
    LmpFactsResult,
    LmpPiCountsResult,
)
from engineering_app.application.ports.home_sources import HomeSourceContext


class LmpFactsSource(Protocol):
    """Fonte oficial de fatos LMP — owner de integração: api-delpi."""

    system: str
    endpoint: str

    async def fetch_facts(
        self,
        ctx: HomeSourceContext,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
        listing_type: str | None,
        page: int,
        page_size: int,
        include_qtd_pi: bool,
    ) -> LmpFactsResult:
        """F-LMP-01 — fatos por (ov, revisão, ciclo) qualificados no período."""
        ...

    async def fetch_pi_counts(
        self,
        ctx: HomeSourceContext,
        *,
        ov_keys: list[dict[str, str]],
        branch: str | None,
    ) -> LmpPiCountsResult:
        """F-LMP-04 — contagens PI por chave (branch, sale_number, revision)."""
        ...
