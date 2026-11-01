"""Repository port for the R09 billing × MOD breakdown.

The port is intentionally row-oriented: the use case owns the DLP204
assembly semantics (level attribution, propagated quantity, typed
absence) while the adapter only returns Protheus rows.
"""

from __future__ import annotations

from typing import Any, Protocol


class BillingModBreakdownRepositoryPort(Protocol):
    def fetch_billed_quantities(
        self, *, period_start: str, period_end: str, branch: str
    ) -> list[dict[str, Any]]:
        """Per-product billed quantity on the D2_EMISSAO axis.

        Each row carries ``product_code``, ``has_billing`` (any
        ``F4_DUPLIC='S'`` line, anchor-membership predicate) and
        ``billed_qty`` (Σ ``D2_QUANT`` with ``D2_TIPO<>'D'`` — the QTDFAT
        rule proven in doc 85 §9 BR-R09-006).
        """
        ...

    def fetch_structure_edges(
        self, *, parent_codes: list[str], branch: str
    ) -> list[dict[str, Any]]:
        """Direct SG1 children of ``parent_codes`` (``Estrut`` semantics).

        Rows: ``parent_code``, ``component_code``, ``component_seq``
        (``G1_TRT``), ``quantity_per_unit`` — one row per SG1 edge;
        dedup/validity/qty>0 filtering is applied by the caller.
        """
        ...

    def fetch_route_operations(
        self, *, product_codes: list[str], branch: str
    ) -> list[dict[str, Any]]:
        """Cadastral SG2 operations of ``product_codes`` with MOD bridge.

        Rows: ``product_code``, ``operation``, ``operation_description``,
        ``resource``, ``std_time`` (raw ``G2_TEMPAD``), ``mod_item``,
        ``mod_description``, ``mod_unit`` (from ``SH1010.H1_CCUSTO`` →
        ``SB1010`` when the resource maps to a ``MOD*`` item).
        """
        ...
