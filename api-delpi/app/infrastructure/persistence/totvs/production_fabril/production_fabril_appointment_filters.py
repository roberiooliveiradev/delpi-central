from __future__ import annotations

from datetime import date
from typing import Tuple

from app.domain.production.production_efficiency_valid_range import (
    PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
    PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
)
from app.domain.production.production_fabril_appointment_scope import (
    DEFAULT_PRODUCTION_BRANCHES,
    EXCLUDED_WORK_CENTERS,
    STATUS_REGISTRO_OK,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def parse_csv_filter_values(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if "," not in text:
        return [text]
    values = [part.strip() for part in text.split(",") if part.strip()]
    return values or None


def _apply_exact_multi_filter(
    qb: QueryBuilder,
    column: str,
    raw: str | None,
) -> None:
    values = parse_csv_filter_values(raw)
    if not values:
        return
    if len(values) == 1:
        qb.eq(column, values[0])
    else:
        qb.in_list(column, values)


def _column(name: str, *, prefix: str | None) -> str:
    if prefix:
        return f"{prefix}.{name}"
    return name


def build_fabril_view_filters(
    *,
    date_start: date | str,
    date_end: date | str,
    branch: str | None = None,
    branches: tuple[str, ...] = DEFAULT_PRODUCTION_BRANCHES,
    op: str | None = None,
    work_center: str | None = None,
    operator_code: str | None = None,
    employee: str | None = None,
    status_ok_only: bool = True,
    efficiency_cap_pct: int | None = None,
    column_prefix: str | None = None,
) -> Tuple[str, tuple]:
    """Filtros da view `vw_Apontamentos_Eficiencia` (eficiência fabril e OEE)."""
    qb = QueryBuilder()

    filial_col = _column("FILIAL", prefix=column_prefix)
    data_col = _column("DATA_PRODUCAO", prefix=column_prefix)
    op_col = _column("OP", prefix=column_prefix)
    ct_col = _column("CENTRO_TRABALHO", prefix=column_prefix)
    operador_col = _column("NOME_OPERADOR", prefix=column_prefix)
    cod_operador_col = _column("COD_OPERADOR", prefix=column_prefix)
    status_col = _column("STATUS_REGISTRO", prefix=column_prefix)
    eficiencia_col = _column("EFICIENCIA_PERCENTUAL", prefix=column_prefix)

    start_value = date_start.isoformat() if isinstance(date_start, date) else date_start
    end_value = date_end.isoformat() if isinstance(date_end, date) else date_end

    qb.gte(data_col, start_value)
    qb.lte(data_col, end_value)

    if branch:
        qb.eq(filial_col, branch)
    else:
        qb.in_list(filial_col, list(branches))

    qb.raw(f"LTRIM(RTRIM(ISNULL({filial_col}, ''))) <> ''")

    if op:
        _apply_exact_multi_filter(qb, op_col, op)

    if work_center:
        selected = parse_csv_filter_values(work_center) or []
        allowed = [value for value in selected if value not in EXCLUDED_WORK_CENTERS]
        if not allowed:
            qb.raw("1=0")
        elif len(allowed) == 1:
            qb.eq(ct_col, allowed[0])
        else:
            qb.in_list(ct_col, allowed)
    else:
        for excluded in EXCLUDED_WORK_CENTERS:
            qb.raw(f"LTRIM(RTRIM({ct_col})) <> ?")
            qb._params.append(excluded)

    if operator_code:
        _apply_exact_multi_filter(qb, cod_operador_col, operator_code)

    if employee:
        qb.like(operador_col, employee, case_insensitive=True)

    if efficiency_cap_pct is not None:
        qb.raw(
            f"({eficiencia_col} IS NULL OR "
            f"({eficiencia_col} >= ? AND {eficiencia_col} <= ?))"
        )
        qb._params.append(PRODUCTION_EFFICIENCY_VALID_MIN_PCT)
        qb._params.append(efficiency_cap_pct)

    if status_ok_only:
        qb.eq(status_col, STATUS_REGISTRO_OK)

    return qb.build()
