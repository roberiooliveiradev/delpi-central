"""Comex Stat NCM imports CSV normalizer (PROC-0076 R2 / EX1 foundation).

Pure, bounded parser for an already-fetched *official MDIC import CSV*.
No network or persistence is performed here. The caller must provide a
business-approved allowlist of NCM codes; no default/all-NCM fallback.

The output is a candidate monthly aggregate, NOT an international metal
spot quote and NOT DELPI's actual purchase price.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable, TextIO

REQUIRED_COLUMNS = frozenset({
    "CO_ANO", "CO_MES", "CO_NCM", "CO_PAIS", "SG_UF_NCM",
    "KG_LIQUIDO", "VL_FOB",
})
NCM_PATTERN = re.compile(r"^[0-9]{8}$")
# Hard bound against runaway memory/parse — sized to accept the real
# official annual files (IMP_2025.csv ≈ 175 MB / ≈2.4 M data rows, and
# still growing year over year) with a wide safety margin.
MAX_ROWS = 25_000_000


class ComexCsvContractError(ValueError):
    """Invalid or unsafe source extract; do not persist partial aggregates."""


@dataclass(frozen=True)
class MonthlyImportAggregate:
    reference_month: date
    ncm_code: str
    country_code: str
    state_code: str
    fob_usd_total: Decimal
    net_weight_kg_total: Decimal
    contributing_rows: int
    unit_value_usd_per_t: Decimal | None
    quality_status: str


def _nonnegative_decimal(raw: str | None, column: str, line: int) -> Decimal:
    try:
        value = Decimal(str(raw or "").strip())
    except InvalidOperation as exc:
        raise ComexCsvContractError(
            f"invalid {column} at CSV record {line}"
        ) from exc
    if not value.is_finite() or value < 0:
        raise ComexCsvContractError(f"invalid {column} at CSV record {line}")
    return value


def normalize_import_csv(
    source: TextIO | Iterable[str],
    *,
    approved_ncm_codes: frozenset[str],
    max_rows: int = MAX_ROWS,
) -> list[MonthlyImportAggregate]:
    """Aggregate official import CSV by (month, NCM, origin country, UF).

    SUM(FOB USD) / (SUM(net kg) / 1000) is the monthly indicative
    unit value. Ratios are NEVER averaged across underlying rows.
    Only approved NCMs are retained; source totals outside that subset
    are neither imported nor mistaken for a complete universe.
    """
    if not approved_ncm_codes or any(
        NCM_PATTERN.fullmatch(ncm) is None for ncm in approved_ncm_codes
    ):
        raise ComexCsvContractError("explicit approved 8-digit NCM allowlist required")
    if max_rows <= 0 or max_rows > MAX_ROWS:
        raise ComexCsvContractError("invalid bounded CSV row limit")

    reader = csv.DictReader(source, delimiter=";", strict=True)
    if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
        raise ComexCsvContractError("MDIC import CSV missing required columns")

    groups: dict[tuple[date, str, str, str], list] = defaultdict(
        lambda: [Decimal("0"), Decimal("0"), 0]
    )
    for line, row in enumerate(reader, start=1):
        if line > max_rows:
            raise ComexCsvContractError("MDIC import CSV exceeded row limit")
        if None in row or any(row.get(col) is None for col in REQUIRED_COLUMNS):
            raise ComexCsvContractError(f"malformed CSV record {line}")
        ncm = row["CO_NCM"].strip()
        if not NCM_PATTERN.fullmatch(ncm):
            raise ComexCsvContractError(f"invalid NCM at CSV record {line}")
        if ncm not in approved_ncm_codes:
            continue
        try:
            year = int(row["CO_ANO"])
            month = int(row["CO_MES"])
            reference_month = date(year, month, 1)
        except (ValueError, TypeError) as exc:
            raise ComexCsvContractError(
                f"invalid reference month at CSV record {line}"
            ) from exc
        country = row["CO_PAIS"].strip()
        state = row["SG_UF_NCM"].strip().upper()
        if not country or not state:
            raise ComexCsvContractError(f"missing dimensions at CSV record {line}")
        kg = _nonnegative_decimal(row["KG_LIQUIDO"], "KG_LIQUIDO", line)
        fob = _nonnegative_decimal(row["VL_FOB"], "VL_FOB", line)
        entry = groups[(reference_month, ncm, country, state)]
        entry[0] += fob
        entry[1] += kg
        entry[2] += 1

    result: list[MonthlyImportAggregate] = []
    for (reference_month, ncm, country, state), (fob, kg, count) in sorted(
        groups.items()
    ):
        unit_value = fob * Decimal("1000") / kg if kg > 0 else None
        result.append(
            MonthlyImportAggregate(
                reference_month=reference_month,
                ncm_code=ncm,
                country_code=country,
                state_code=state,
                fob_usd_total=fob,
                net_weight_kg_total=kg,
                contributing_rows=count,
                unit_value_usd_per_t=unit_value,
                quality_status="validated" if kg > 0 else "invalid_weight",
            )
        )
    return result
