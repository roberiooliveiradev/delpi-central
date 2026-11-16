from unittest.mock import patch

import pytest

from app.infrastructure.persistence.totvs.supplies_repositories.supplier_performance_export_sql import (
    MAX_EXPORT_ROWS_PER_SOURCE,
    build_delivery_evidence_sql,
    build_inspection_evidence_sql,
)
from app.infrastructure.persistence.totvs.supplies_repositories.supplier_performance_export_repository import (
    SupplierPerformanceExportRepository,
)


def test_sql_is_read_only_bounded_parameterized_and_grains_match_screen():
    for builder in (build_inspection_evidence_sql, build_delivery_evidence_sql):
        sql, params = builder(
            ["01", "02"], "2026-11-01", "2026-11-16",
            "000001", "01",
        )
        assert sql.count("?") == len(params)
        assert "000001" not in sql
        assert "2026-11-01" not in sql
        assert params[:4] == ("01", "02", "2026-11-01", "2026-11-16")
        assert params[-2:] == ("000001", "01")
        assert f"TOP {MAX_EXPORT_ROWS_PER_SOURCE + 1}" in sql
        assert "DATEADD(day, 1" in sql
        assert not any(word in sql.upper() for word in ("INSERT INTO ", "UPDATE ", "DELETE FROM "))
    quality_sql, _ = build_inspection_evidence_sql(["01"], "2026-11-01", "2026-11-16")
    assert "GROUP BY I.Filial, I.Id_Inspecao" in quality_sql
    assert "Eh_Aprovada" in quality_sql
    assert "Serie_Nota_Fiscal" in quality_sql
    assert "P.B1_TIPO = ?" in quality_sql
    delivery_sql, _ = build_delivery_evidence_sql(["01"], "2026-11-01", "2026-11-16")
    assert "V.DOCUMENTO" in delivery_sql
    assert "V.NUMERO_PEDIDO" in delivery_sql
    assert "V.DT_ENTREGA" in delivery_sql
    assert "V.DIAS" in delivery_sql
    # Must NOT silently differ from the deployed IDF delivery source.
    assert "TIPO_PRODUTO" not in delivery_sql.split("WHERE", 1)[1]


@pytest.mark.parametrize("source", ["inspections", "deliveries"])
def test_export_refuses_truncation(source):
    repository = SupplierPerformanceExportRepository()
    with patch.object(repository, "__enter__", return_value=repository), patch.object(
        repository, "__exit__", return_value=False
    ), patch.object(repository, "execute_query") as execute:
        if source == "inspections":
            execute.return_value = [{}] * (MAX_EXPORT_ROWS_PER_SOURCE + 1)
        else:
            execute.side_effect = [[], [{}] * (MAX_EXPORT_ROWS_PER_SOURCE + 1)]
        with pytest.raises(ValueError, match="12.000"):
            repository.read_evidence(
                branches=["01"], date_from="2026-11-01", date_to="2026-11-16"
            )
