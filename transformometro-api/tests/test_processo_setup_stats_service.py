from __future__ import annotations

from unittest.mock import MagicMock, patch

from tm_app.application.services.processo_setup_stats_service import ProcessoSetupStatsService
from tm_app.infrastructure.persistence.repositories.processo_setup_stats_repository import (
    ProcessoSetupStatsRepository,
)


def test_enrich_processos_merges_setup_stats():
    rows = [{"processo_id": "p1", "nome_processo": "A"}]
    stats = {
        "p1": {
            "instancia_count": 1,
            "diagram_node_count": 2,
            "decomposition_node_count": 3,
            "has_baseline": True,
            "has_melhoria": False,
            "has_medicao": True,
        }
    }
    with patch(
        "tm_app.application.services.processo_setup_stats_service.ProcessoSetupStatsRepository"
    ) as repo_cls:
        repo_cls.return_value.fetch_by_processo_ids = MagicMock(return_value=stats)
        enriched = ProcessoSetupStatsService().enrich_processos(rows)

    assert enriched[0]["setup_stats"]["instancia_count"] == 1
    assert enriched[0]["setup_stats"]["has_baseline"] is True


def test_enrich_processos_uses_empty_stats_when_missing():
    rows = [{"processo_id": "p2", "nome_processo": "B"}]
    with patch(
        "tm_app.application.services.processo_setup_stats_service.ProcessoSetupStatsRepository"
    ) as repo_cls:
        repo_cls.return_value.fetch_by_processo_ids = MagicMock(return_value={})
        repo_cls.empty_stats = ProcessoSetupStatsRepository.empty_stats
        enriched = ProcessoSetupStatsService().enrich_processos(rows)

    assert enriched[0]["setup_stats"]["instancia_count"] == 0
    assert enriched[0]["setup_stats"]["has_medicao"] is False
