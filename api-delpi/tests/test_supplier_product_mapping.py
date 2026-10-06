"""Produto x Fornecedor — matching determinístico e SQL sem filial."""

from __future__ import annotations

from app.domain.services.lancamento_notas_fiscais.supplier_product_mapping_service import (
    resolve_supplier_product_codes,
)
from app.infrastructure.persistence.totvs.invoice_posting_repositories.supplier_product_mapping_sql import (
    chunk_supplier_product_codes,
    supplier_product_mapping_sql,
)
from app.infrastructure.persistence.totvs.invoice_posting_repositories.totvs_supplier_product_mapping_repository import (
    TotvsSupplierProductMappingRepository,
)


def test_sql_matches_supplier_store_and_codes_without_branch_or_top() -> None:
    sql = supplier_product_mapping_sql(3)
    folded = sql.upper()
    assert "A5_FILIAL" not in folded
    assert "LIKE" not in folded
    assert "TOP " not in folded
    assert "R_E_C_N_O_" not in folded
    assert "A5_FORNECE" in folded
    assert "A5_LOJA" in folded
    assert "A5_CODPRF" in folded
    assert "B1_DESC" in folded
    assert "D_E_L_E_T_" in folded
    assert sql.count("?") == 5


def test_repository_chunks_codes_and_binds_parameters() -> None:
    calls: list[tuple] = []

    def fetch(sql: str, params: tuple) -> list[dict[str, str]]:
        calls.append((sql, params))
        return [
            {
                "supplier_product_code": params[2],
                "internal_product_code": "000050",
                "internal_product_description": "PARAFUSO M6",
            }
        ]

    repository = TotvsSupplierProductMappingRepository()
    repository._fetch_preserving_codes = fetch  # type: ignore[method-assign]
    rows = repository.list_mappings(
        supplier_code="000192",
        supplier_store="01",
        supplier_product_codes=["00001234", "ABC-1.2", "00001234", ""],
        chunk_size=2,
    )
    assert [params[0:2] for _sql, params in calls] == [("000192", "01"), ("000192", "01")]
    assert calls[0][1][2:] == ("00001234", "ABC-1.2")
    assert calls[1][1][2:] == ("00001234",) or calls[1][1][2] == "00001234"
    assert "A5_FILIAL" not in calls[0][0]
    assert rows[0]["internal_product_code"] == "000050"
    assert chunk_supplier_product_codes(["a", "b", "c"], 2) == [["a", "b"], ["c"]]


def test_mapped_unmapped_duplicate_and_ambiguous() -> None:
    resolved = resolve_supplier_product_codes(
        ["00001234", "SEM", "DUP", "AMB", "ABC-1.2", "A.B/1"],
        [
            {
                "supplier_product_code": "00001234",
                "internal_product_code": "000050",
                "internal_product_description": "PARAFUSO M6",
            },
            {
                "supplier_product_code": "DUP",
                "internal_product_code": "DELPI001",
                "internal_product_description": "IGUAL",
            },
            {
                "supplier_product_code": "DUP",
                "internal_product_code": "DELPI001",
                "internal_product_description": "",
            },
            {
                "supplier_product_code": "AMB",
                "internal_product_code": "DELPI001",
                "internal_product_description": "UM",
            },
            {
                "supplier_product_code": "AMB",
                "internal_product_code": "DELPI999",
                "internal_product_description": "OUTRO",
            },
            {
                "supplier_product_code": "ABC-1.2",
                "internal_product_code": "PX1",
                "internal_product_description": "",
            },
            {
                "supplier_product_code": "A.B/1",
                "internal_product_code": "PX2",
                "internal_product_description": "COM PONTO",
            },
        ],
    )
    assert resolved["00001234"].mapping_status == "mapped"
    assert resolved["00001234"].internal_product_code == "000050"
    assert resolved["SEM"].mapping_status == "unmapped"
    assert resolved["SEM"].internal_product_code is None
    assert resolved["DUP"].mapping_status == "mapped"
    assert resolved["DUP"].internal_product_code == "DELPI001"
    assert resolved["AMB"].mapping_status == "ambiguous"
    assert resolved["AMB"].internal_product_code is None
    assert resolved["AMB"].internal_product_description is None
    assert resolved["ABC-1.2"].internal_product_code == "PX1"
    assert resolved["ABC-1.2"].internal_product_description is None
    assert resolved["A.B/1"].internal_product_code == "PX2"


def test_same_code_is_independent_per_call() -> None:
    shared = [
        {
            "supplier_product_code": "ABC",
            "internal_product_code": "P1",
            "internal_product_description": "LOJA 01",
        }
    ]
    other = [
        {
            "supplier_product_code": "ABC",
            "internal_product_code": "P2",
            "internal_product_description": "LOJA 02",
        }
    ]
    first = resolve_supplier_product_codes(["ABC"], shared)
    second = resolve_supplier_product_codes(["ABC"], other)
    assert first["ABC"].internal_product_code == "P1"
    assert second["ABC"].internal_product_code == "P2"
