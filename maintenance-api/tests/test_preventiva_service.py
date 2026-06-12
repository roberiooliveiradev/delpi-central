from unittest.mock import MagicMock
from datetime import datetime, timezone

from maint_app.application.services.preventiva_service import PreventivaService, _match_status


def test_match_status_critico():
    rules = [
        {"descricao": "CRÍTICO", "operador": ">=", "percentual": 95},
        {"descricao": "ATENÇÃO", "operador": ">=", "percentual": 80},
        {"descricao": "OK", "operador": "<", "percentual": 80},
    ]
    assert _match_status(96, rules) == "CRÍTICO"
    assert _match_status(85, rules) == "ATENÇÃO"
    assert _match_status(50, rules) == "OK"


def test_listar_alertas_ordenacao():
    reposicao_repo = MagicMock()
    status_repo = MagicMock()
    reposicao_repo.list_ultimas_por_par.return_value = [
        {
            "codigo_ferramenta": "23-001",
            "codigo_peca": "P1",
            "data_reposicao": datetime(2026, 6, 1, tzinfo=timezone.utc),
        }
    ]
    status_repo.list_active.return_value = [
        {"descricao": "CRÍTICO", "operador": ">=", "percentual": 95},
        {"descricao": "ATENÇÃO", "operador": ">=", "percentual": 80},
        {"descricao": "OK", "operador": "<", "percentual": 80},
    ]
    reposicao_repo.media_golpes.return_value = 100.0

    totvs = MagicMock()
    totvs.obter_golpes.return_value = {"total_golpes": 96}

    service = PreventivaService(
        reposicao_repo=reposicao_repo,
        status_repo=status_repo,
        totvs_gateway=totvs,
    )
    alertas, total = service.listar_alertas(filial="01")

    status_repo.list_active.assert_called_once_with(filial="01")
    assert total == 1
    assert len(alertas) == 1
    assert alertas[0]["status"] == "CRÍTICO"
    assert alertas[0]["golpes_atuais"] == 96


def test_listar_alertas_enriquece_descricoes():
    reposicao_repo = MagicMock()
    status_repo = MagicMock()
    reposicao_repo.list_ultimas_por_par.return_value = [
        {
            "codigo_ferramenta": "23-001",
            "codigo_peca": "30190006",
            "data_reposicao": datetime(2026, 6, 1, tzinfo=timezone.utc),
        }
    ]
    status_repo.list_active.return_value = [
        {"descricao": "OK", "operador": "<", "percentual": 80},
    ]
    reposicao_repo.media_golpes.return_value = 100.0

    totvs = MagicMock()
    totvs.obter_golpes.return_value = {"total_golpes": 50}
    totvs.obter_ferramenta.return_value = {"codigo": "23-001", "descricao": "MINI APLICADOR"}
    totvs.listar_pecas.return_value = {
        "items": [{"codigo": "30190006", "descricao": "GRAMPEADOR DO ISOLANTE"}]
    }
    totvs.listar_componentes.return_value = {"items": []}

    service = PreventivaService(
        reposicao_repo=reposicao_repo,
        status_repo=status_repo,
        totvs_gateway=totvs,
    )
    alertas, _total = service.listar_alertas(filial="01")

    assert alertas[0]["descricao_ferramenta"] == "MINI APLICADOR"
    assert alertas[0]["descricao_peca"] == "GRAMPEADOR DO ISOLANTE"


def test_listar_historico_exclui_motivos_marcados():
    reposicao_repo = MagicMock()
    reposicao_repo.list_preventiva_by_ferramenta.return_value = [
        {
            "reposicao_id": "abc",
            "data_reposicao": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "golpes": 80_000,
        }
    ]

    service = PreventivaService(reposicao_repo=reposicao_repo, status_repo=MagicMock())
    historico = service.listar_historico(
        filial="01",
        codigo_ferramenta="23-014",
        codigo_peca="30190026",
    )

    reposicao_repo.list_preventiva_by_ferramenta.assert_called_once_with(
        filial="01",
        codigo_ferramenta="23-014",
        codigo_peca="30190026",
    )
    assert len(historico) == 1
    assert historico[0]["golpes"] == 80_000
