from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.application.use_cases.third_party_materials.export_returns_use_case import (
    ExportThirdPartyMaterialsReturnsUseCase,
)
from app.application.use_cases.third_party_materials.get_shipment_use_case import (
    GetThirdPartyMaterialsShipmentUseCase,
)
from app.application.use_cases.third_party_materials.get_summary_use_case import (
    GetThirdPartyMaterialsSummaryUseCase,
)
from app.application.use_cases.third_party_materials.list_shipments_use_case import (
    ListThirdPartyMaterialsShipmentsUseCase,
)


def _row(recno: int, *, return_recno: int | None = None, nf: str = "004400278") -> dict:
    return {
        "RECNO_REMESSA": recno,
        "FILIAL": "01",
        "ID_REMESSA": "UCVMKI",
        "NF_RECEBIMENTO": nf,
        "SERIE_RECEBIMENTO": "1",
        "EMISSAO_RECEBIMENTO": "2026-06-18",
        "DIGITACAO_RECEBIMENTO": "2026-06-22",
        "TES_RECEBIMENTO": "085",
        "PRODUTO": "10211413",
        "REFERENCIA_CLIENTE": "10018137",
        "DESCRICAO_PRODUTO": "VENTILADOR",
        "UNIDADE_MEDIDA": "PC",
        "TIPO_PRODUTO": "MP",
        "GRUPO_PRODUTO": "1021",
        "PRODUTO_BLOQUEADO": "N",
        "TIPO_PARCEIRO": "C",
        "COD_PARCEIRO": "000001",
        "LOJA_PARCEIRO": "11",
        "NOME_PARCEIRO": "WEG",
        "NOME_REDUZIDO_PARCEIRO": "WEG",
        "PARCEIRO_BLOQUEADO": "N",
        "QTD_RECEBIDA": Decimal("4800"),
        "QTD_DEVOLVIDA_TOTAL": Decimal("3181"),
        "SALDO_A_ENTREGAR": Decimal("1619"),
        "STATUS_REMESSA": "PARCIAL",
        "POSSUI_SALDO": "S",
        "IND_ATENDIDO": "",
        "QTD_RETORNOS_SOMADA": Decimal("3181"),
        "DIFERENCA_CONTROLE": Decimal("0"),
        "RECNO_RETORNO": return_recno,
        "NF_RETORNO": "102188" if return_recno else None,
        "SERIE_RETORNO": "1" if return_recno else None,
        "EMISSAO_RETORNO": "2026-07-01" if return_recno else None,
        "DIGITACAO_RETORNO": "2026-07-01" if return_recno else None,
        "TES_RETORNO": "090" if return_recno else None,
        "QTD_RETORNO": Decimal("100") if return_recno else None,
        "QTD_DEVOLVIDA_ACUMULADA": Decimal("100") if return_recno else None,
        "SALDO_APOS_RETORNO": Decimal("4700") if return_recno else None,
        "TIPO_PARCEIRO_RETORNO": "C" if return_recno else None,
        "COD_PARCEIRO_RETORNO": "000001" if return_recno else None,
        "LOJA_PARCEIRO_RETORNO": "11" if return_recno else None,
    }


def test_empty_branch_is_rejected() -> None:
    with pytest.raises(ValueError, match="Filial é obrigatória"):
        ThirdPartyMaterialsQueryRequest.from_query(branch="  ", product="10211413")


def test_customer_reference_is_useful_filter() -> None:
    request = ThirdPartyMaterialsQueryRequest.from_query(
        branch="01", customer_reference=" 10018137 "
    )
    assert request.customer_reference == "10018137"
    assert request.has_useful_filter() is True


def test_list_use_case_pages_by_recno_and_groups_returns() -> None:
    repository = MagicMock()
    repository.count_shipments.return_value = 43
    repository.list_shipment_recnos.return_value = [27062725]
    repository.list_rows_by_recnos.return_value = [
        _row(27062725, return_recno=11),
        _row(27062725, return_recno=12),
    ]
    use_case = ListThirdPartyMaterialsShipmentsUseCase(repository)
    result = use_case.execute(
        ThirdPartyMaterialsQueryRequest.from_query(branch="01", product="10211413")
    )
    assert result["total"] == 43
    assert result["page"] == 1
    assert len(result["items"]) == 1
    assert len(result["items"][0]["returns"]) == 2
    repository.list_rows_by_recnos.assert_called_once()


def test_get_shipment_returns_none_when_missing() -> None:
    repository = MagicMock()
    repository.get_rows_by_recno.return_value = []
    use_case = GetThirdPartyMaterialsShipmentUseCase(repository)
    assert use_case.execute(shipment_recno=1, branch="01") is None


def test_summary_maps_unique_shipment_kpis() -> None:
    repository = MagicMock()
    repository.get_summary.return_value = {
        "total_shipments": 43,
        "open_shipments": 3,
        "partial_shipments": 1,
        "no_return_shipments": 2,
        "pending_balance": Decimal("11419"),
    }
    result = GetThirdPartyMaterialsSummaryUseCase(repository).execute(
        ThirdPartyMaterialsQueryRequest.from_query(branch="01", product="10211413")
    )
    assert result == {
        "total_shipments": 43,
        "open_shipments": 3,
        "partial_shipments": 1,
        "no_return_shipments": 2,
        "pending_balance": 11419.0,
    }


def test_export_csv_contains_notice_and_rows() -> None:
    repository = MagicMock()
    repository.list_export_rows.return_value = [_row(27062725, return_recno=11)]
    result = ExportThirdPartyMaterialsReturnsUseCase(repository).execute(
        ThirdPartyMaterialsQueryRequest.from_query(
            branch="01", product="10211413", export_format="csv"
        )
    )
    content = result["stream"].read().decode("utf-8-sig")
    assert "Saldo e quantidades da remessa se repetem" in content
    assert "004400278" in content
    assert result["exported_count"] == 1
