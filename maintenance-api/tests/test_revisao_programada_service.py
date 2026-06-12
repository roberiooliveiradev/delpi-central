from datetime import datetime, timezone
from unittest.mock import MagicMock

from maint_app.application.services.revisao_programada_service import (
    RevisaoProgramadaService,
    _calc_status_revisao,
    add_months,
)


def test_add_months():
    base = datetime(2026, 1, 31)
    assert add_months(base, 1).month == 2
    assert add_months(base, 1).day == 28


def test_calc_status_revisao():
    assert _calc_status_revisao(dias_restantes=-1, intervalo_meses=3) == "CRÍTICO"
    assert _calc_status_revisao(dias_restantes=10, intervalo_meses=3) == "ATENÇÃO"
    assert _calc_status_revisao(dias_restantes=60, intervalo_meses=3) == "OK"


def test_listar_alertas_revisao_vencida():
    revisao_repo = MagicMock()
    reposicao_repo = MagicMock()
    revisao_repo.list_active.return_value = [
        {
            "revisao_id": "abc-123",
            "codigo_ferramenta": "23-001",
            "intervalo_meses": 3,
            "data_ultima_revisao": datetime(2025, 12, 1),
            "observacao": None,
            "data_criacao": datetime(2025, 12, 1),
        }
    ]
    reposicao_repo.map_ultima_reposicao_por_ferramenta.return_value = {}

    service = RevisaoProgramadaService(
        revisao_repo=revisao_repo,
        reposicao_repo=reposicao_repo,
        totvs_gateway=None,
    )
    alertas, total = service.listar_alertas(filial="01")

    assert total == 1
    assert alertas[0]["codigo_ferramenta"] == "23-001"
    assert alertas[0]["status"] == "CRÍTICO"
    assert alertas[0]["dias_restantes"] is not None
    assert alertas[0]["dias_restantes"] < 0


def test_listar_alertas_usa_data_criacao_quando_sem_revisao_manual():
    revisao_repo = MagicMock()
    reposicao_repo = MagicMock()
    data_criacao = datetime(2026, 3, 1)
    revisao_repo.list_active.return_value = [
        {
            "revisao_id": "abc-123",
            "codigo_ferramenta": "23-001",
            "intervalo_meses": 3,
            "data_ultima_revisao": None,
            "observacao": None,
            "data_criacao": data_criacao,
        }
    ]

    service = RevisaoProgramadaService(
        revisao_repo=revisao_repo,
        reposicao_repo=reposicao_repo,
        totvs_gateway=None,
    )
    alertas, _total = service.listar_alertas(filial="01")

    assert alertas[0]["data_referencia"] == data_criacao
    assert alertas[0]["status"] in {"OK", "ATENÇÃO", "CRÍTICO"}
    reposicao_repo.map_ultima_reposicao_por_ferramenta.assert_not_called()


def test_resumo_alertas_revisao():
    revisao_repo = MagicMock()
    reposicao_repo = MagicMock()
    revisao_repo.list_active.return_value = [
        {
            "revisao_id": "1",
            "codigo_ferramenta": "23-001",
            "intervalo_meses": 3,
            "data_ultima_revisao": datetime(2025, 1, 1),
            "observacao": None,
            "data_criacao": datetime(2025, 1, 1),
        },
        {
            "revisao_id": "2",
            "codigo_ferramenta": "23-002",
            "intervalo_meses": 6,
            "data_ultima_revisao": datetime.now(timezone.utc).replace(tzinfo=None),
            "observacao": None,
            "data_criacao": datetime(2026, 1, 1),
        },
    ]
    reposicao_repo.map_ultima_reposicao_por_ferramenta.return_value = {}

    service = RevisaoProgramadaService(
        revisao_repo=revisao_repo,
        reposicao_repo=reposicao_repo,
        totvs_gateway=None,
    )
    resumo = service.resumo_alertas(filial="01")

    assert resumo["total"] == 2
    assert resumo["critico"] >= 1
