from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.repositories.processo_setup_stats_repository import (
    ProcessoSetupStatsRepository,
)


class ProcessoSetupStatsService:
    def enrich_processos(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not rows:
            return rows
        ids = [str(row.get("processo_id") or "") for row in rows if row.get("processo_id")]
        stats_by_id = ProcessoSetupStatsRepository().fetch_by_processo_ids(ids)
        empty = ProcessoSetupStatsRepository.empty_stats()
        enriched: list[dict[str, Any]] = []
        for row in rows:
            merged = dict(row)
            pid = str(row.get("processo_id") or "")
            merged["setup_stats"] = stats_by_id.get(pid, empty)
            enriched.append(merged)
        return enriched
