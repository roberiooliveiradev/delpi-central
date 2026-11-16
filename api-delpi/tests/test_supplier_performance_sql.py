from unittest.mock import patch

import pytest

from app.infrastructure.persistence.totvs.supplies_repositories.supplier_performance_sql import (
    build_supplier_performance_sql,
    MAX_SOURCE_ROWS,
)
from app.infrastructure.persistence.totvs.supplies_repositories.supplier_performance_repository import (
    SupplierPerformanceRepository,
)


def test_parameterized_source_grains_and_date_anchors():
    sql, params = build_supplier_performance_sql(
        ["01", "02"], "2026-11-01", "2026-11-16"
    )
    assert sql.count("?") == len(params)
    assert params == (
        "01",
        "02",
        "2026-11-01",
        "2026-11-16",
        "3019",
        "MP",
        "01",
        "02",
        "2026-11-01",
        "2026-11-16",
    )
    assert "2026-11-01" not in sql
    assert "I.Data_Laudo >= ?" in sql
    assert "V.DT_DIGITACAO >= ?" in sql
    assert "GROUP BY I.Filial, I.Id_Inspecao" in sql
    assert "UNION ALL" in sql and "JOIN inspection_facts" not in sql
    assert "V.DIAS >= 0" in sql  # early and same-day count as on-time
    assert "OR EXISTS" in sql and "P.B1_TIPO = ?" in sql
    assert "conditional_count" in sql and "urgent_count" in sql
    assert f"TOP {MAX_SOURCE_ROWS + 1}" in sql


def test_repository_rejects_overflow_instead_of_silent_truncation():
    with patch.object(
        SupplierPerformanceRepository, "__enter__"
    ) as enter, patch.object(SupplierPerformanceRepository, "__exit__"):
        enter.return_value.execute_query.return_value = [{}] * (MAX_SOURCE_ROWS + 1)
        with pytest.raises(ValueError, match="limite"):
            SupplierPerformanceRepository().read_counts(
                branches=["01"], date_from="2026-11-01", date_to="2026-11-16"
            )
