"""SQL for the R12/R15 closing-state markers (doc 129).

Read-only probes over proven physical markers — SB9010 snapshot presence,
SX6 ``MV_ULMES`` per branch and TTAT write windows (``B1_CUSTD`` /
``D3_CUSTO1``). No writes, no inference: markers are returned raw and the
BFF composes the governed state projection.
"""

from __future__ import annotations

from typing import Any


def _in_placeholders(values: tuple[str, ...]) -> str:
    return ", ".join("?" for _ in values)


def build_snapshot_branch_counts_query(
    *, snapshot_date: str, branches: tuple[str, ...]
) -> tuple[str, list[Any]]:
    """SB9010 row presence per branch for one ``B9_DATA`` snapshot."""
    sql = f"""
SELECT RTRIM(B9_FILIAL) AS branch_code, COUNT(*) AS row_count
  FROM SB9010 WITH (NOLOCK)
 WHERE D_E_L_E_T_ = ''
   AND B9_DATA = ?
   AND B9_FILIAL IN ({_in_placeholders(branches)})
 GROUP BY B9_FILIAL
"""
    return sql, [snapshot_date, *branches]


def build_last_snapshot_dates_query(
    *, branches: tuple[str, ...]
) -> tuple[str, list[Any]]:
    """Most recent ``B9_DATA`` per branch — independent of the requested
    competence, so a missing snapshot is reported against the latest
    available evidence, never as zero."""
    sql = f"""
SELECT RTRIM(B9_FILIAL) AS branch_code, MAX(B9_DATA) AS last_snapshot_date
  FROM SB9010 WITH (NOLOCK)
 WHERE D_E_L_E_T_ = ''
   AND B9_FILIAL IN ({_in_placeholders(branches)})
 GROUP BY B9_FILIAL
"""
    return sql, [*branches]


def build_mv_ulmes_query(
    *, branches: tuple[str, ...]
) -> tuple[str, list[Any]]:
    """``SX6010.MV_ULMES`` per branch — the technical last-closing
    marker (proven in data, writer pending — E5)."""
    sql = f"""
SELECT RTRIM(X6_FIL) AS branch_code, RTRIM(X6_CONTEUD) AS param_value
  FROM SX6010 WITH (NOLOCK)
 WHERE D_E_L_E_T_ = ''
   AND X6_VAR = 'MV_ULMES'
   AND X6_FIL IN ({_in_placeholders(branches)})
"""
    return sql, [*branches]


def build_ttat_write_window_query(
    *,
    log_table: str,
    field_name: str,
    window_start: str,
    window_end: str,
) -> tuple[str, list[Any]]:
    """Aggregated TTAT write evidence for one audited field inside a
    datetime window — observed evidence, never execution proof."""
    sql = f"""
SELECT COUNT(*) AS write_count,
       MIN(TTAT_DTIME) AS first_at,
       MAX(TTAT_DTIME) AS last_at
  FROM {log_table} WITH (NOLOCK)
 WHERE TTAT_FIELD = ?
   AND TTAT_DTIME >= ?
   AND TTAT_DTIME <= ?
"""
    return sql, [field_name, window_start, window_end]
