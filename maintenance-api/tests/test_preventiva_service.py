from unittest.mock import MagicMock
from datetime import datetime, timezone

import maint_app.application.services.preventiva_service as preventiva_module
from maint_app.application.list_query import ListQuery
from maint_app.application.services.preventiva_service import (
    PreventivaService,
    _match_status,
    _trim_golpes_history,
)


def setup_function():
    preventiva_module._alertas_snapshot_cache.clear()
    preventiva_module._snapshot_build_locks.clear()


def test_match_status_critico():
    rules = [
        {"descricao": "CRÍTICO", "operador": ">=", "percentual": 95},
        {"descricao": "ATENÇÃO", "operador": ">=", "percentual": 80},
        {"descricao": "OK", "operador": "<", "percentual": 80},
    ]
    assert _match_status(96, rules) == "CRÍTICO"
    assert _match_status(85, rules) == "ATENÇÃO"
    assert _match_status(50, rules) == "OK"


def test_trim_golpes_history_keeps_last_points():
    long_series = list(range(1, 20))
    assert _trim_golpes_history(long_series) == list(range(8, 20))


def test_listar_alertas_usa_batch_maps():
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
    reposicao_repo.media_golpes_map.return_value = {("23-001", "P1"): 100.0}
    reposicao_repo.golpes_history_map.return_value = {("23-001", "P1"): [80_000, 90_000]}

    totvs = MagicMock()
    totvs.obter_golpes_batch.return_value = {
        "items": [{"codigo_ferramenta": "23-001", "total_golpes": 96}],
        "total": 1,
    }

    service = PreventivaService(
        reposicao_repo=reposicao_repo,
        status_repo=status_repo,
        totvs_gateway=totvs,
    )
    alertas, total = service.listar_alertas(filial="01")

    status_repo.list_active.assert_called_once_with(filial="01")
    reposicao_repo.media_golpes_map.assert_called_once_with(filial="01")
    reposicao_repo.golpes_history_map.assert_called_once_with(filial="01")
    totvs.obter_golpes_batch.assert_called_once()
    assert total == 1
    assert len(alertas) == 1
    assert alertas[0]["status"] == "CRÍTICO"
    assert alertas[0]["golpes_atuais"] == 96
    assert alertas[0]["golpes_history"] == [80_000, 90_000]


def test_resumo_compartilha_snapshot_cache():
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
        {"descricao": "OK", "operador": "<", "percentual": 80},
    ]
    reposicao_repo.media_golpes_map.return_value = {("23-001", "P1"): 100.0}
    reposicao_repo.golpes_history_map.return_value = {("23-001", "P1"): [50_000]}
    totvs = MagicMock()
    totvs.obter_golpes_batch.return_value = {
        "items": [{"codigo_ferramenta": "23-001", "total_golpes": 50}],
    }

    service = PreventivaService(
        reposicao_repo=reposicao_repo,
        status_repo=status_repo,
        totvs_gateway=totvs,
    )
    resumo = service.resumo_alertas(filial="01")
    service.listar_alertas(filial="01")

    assert resumo["total"] == 1
    assert reposicao_repo.list_ultimas_por_par.call_count == 1
    assert totvs.obter_golpes_batch.call_count == 1


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
    reposicao_repo.media_golpes_map.return_value = {("23-001", "30190006"): 100.0}
    reposicao_repo.golpes_history_map.return_value = {("23-001", "30190006"): [50_000]}

    totvs = MagicMock()
    totvs.obter_golpes_batch.return_value = {
        "items": [{"codigo_ferramenta": "23-001", "total_golpes": 50}],
    }
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


def test_listar_alertas_enriquece_somente_pagina_sem_filtro_texto():
    reposicao_repo = MagicMock()
    status_repo = MagicMock()
    rows = [
        {
            "codigo_ferramenta": f"23-{index:03d}",
            "codigo_peca": f"301900{index:02d}",
            "data_reposicao": datetime(2026, 6, 1, tzinfo=timezone.utc),
        }
        for index in range(1, 6)
    ]
    reposicao_repo.list_ultimas_por_par.return_value = rows
    status_repo.list_active.return_value = [
        {"descricao": "OK", "operador": "<", "percentual": 80},
    ]
    reposicao_repo.media_golpes_map.return_value = {
        (row["codigo_ferramenta"], row["codigo_peca"]): 100.0 for row in rows
    }
    reposicao_repo.golpes_history_map.return_value = {
        (row["codigo_ferramenta"], row["codigo_peca"]): [50_000] for row in rows
    }

    totvs = MagicMock()
    totvs.obter_golpes_batch.return_value = {
        "items": [{"codigo_ferramenta": row["codigo_ferramenta"], "total_golpes": 50} for row in rows],
    }
    totvs.obter_ferramenta.return_value = {"descricao": "FERRAMENTA"}
    totvs.listar_pecas.return_value = {"items": []}
    totvs.listar_componentes.return_value = {"items": []}

    service = PreventivaService(
        reposicao_repo=reposicao_repo,
        status_repo=status_repo,
        totvs_gateway=totvs,
    )
    alertas, total = service.listar_alertas(
        filial="01",
        query=ListQuery(page=1, page_size=2, sort_by="ferramenta", sort_dir="asc"),
    )

    assert total == 5
    assert len(alertas) == 2
    assert totvs.obter_ferramenta.call_count == 2


def test_fetch_golpes_fallback_threadpool_when_batch_falha():
    reposicao_repo = MagicMock()
    status_repo = MagicMock()
    reposicao_repo.list_ultimas_por_par.return_value = [
        {
            "codigo_ferramenta": "23-001",
            "codigo_peca": "P1",
            "data_reposicao": datetime(2026, 6, 1, tzinfo=timezone.utc),
        }
    ]
    status_repo.list_active.return_value = [{"descricao": "OK", "operador": "<", "percentual": 80}]
    reposicao_repo.media_golpes_map.return_value = {("23-001", "P1"): 100.0}
    reposicao_repo.golpes_history_map.return_value = {("23-001", "P1"): []}

    totvs = MagicMock()
    totvs.obter_golpes_batch.side_effect = RuntimeError("batch unavailable")
    totvs.obter_golpes.return_value = {"total_golpes": 42}

    service = PreventivaService(
        reposicao_repo=reposicao_repo,
        status_repo=status_repo,
        totvs_gateway=totvs,
    )
    alertas, _total = service.listar_alertas(filial="01")

    totvs.obter_golpes.assert_called_once()
    assert alertas[0]["golpes_atuais"] == 42


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


def test_obter_detalhe_consolida_payload():
    reposicao_repo = MagicMock()
    status_repo = MagicMock()
    reposicao_repo.list_ultimas_por_par.return_value = [
        {
            "codigo_ferramenta": "23-001",
            "codigo_peca": "30190006",
            "data_reposicao": datetime(2026, 6, 1, tzinfo=timezone.utc),
        }
    ]
    status_repo.list_active.return_value = [{"descricao": "OK", "operador": "<", "percentual": 80}]
    reposicao_repo.media_golpes_map.return_value = {("23-001", "30190006"): 100.0}
    reposicao_repo.golpes_history_map.return_value = {("23-001", "30190006"): [50_000]}
    reposicao_repo.list_preventiva_by_ferramenta.return_value = [
        {
            "reposicao_id": "abc",
            "data_reposicao": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "golpes": 50_000,
        }
    ]

    totvs = MagicMock()
    totvs.obter_golpes_batch.return_value = {
        "items": [{"codigo_ferramenta": "23-001", "total_golpes": 50}],
    }
    totvs.obter_ferramenta.return_value = {"codigo": "23-001", "descricao": "MINI APLICADOR"}
    totvs.listar_pecas.return_value = {
        "items": [{"codigo": "30190006", "descricao": "GRAMPEADOR DO ISOLANTE"}]
    }
    totvs.listar_componentes.return_value = {
        "items": [{"codigo": "30190006", "descricao": "GRAMPEADOR DO ISOLANTE", "estoque_local_01": 3}]
    }

    service = PreventivaService(
        reposicao_repo=reposicao_repo,
        status_repo=status_repo,
        totvs_gateway=totvs,
    )
    detalhe = service.obter_detalhe(
        filial="01",
        codigo_ferramenta="23-001",
        codigo_peca="30190006",
    )

    assert detalhe["alerta"] is not None
    assert detalhe["ferramenta"]["descricao"] == "MINI APLICADOR"
    assert detalhe["pecaDescricao"] == "GRAMPEADOR DO ISOLANTE"
    assert detalhe["estoqueLocal01"] == 3.0
    assert len(detalhe["historico"]) == 1
