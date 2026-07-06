from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_SETUP_STATS_SQL = """
    SELECT
        p.processo_id,
        COALESCE(inst.cnt, 0)::int AS instancia_count,
        COALESCE(jsonb_array_length(pd.conteudo->'nodes'), 0)::int AS diagram_node_count,
        COALESCE(jsonb_array_length(pdc.conteudo->'nodes'), 0)::int AS decomposition_node_count,
        COALESCE(rev.has_baseline, FALSE) AS has_baseline,
        COALESCE(rev.has_melhoria, FALSE) AS has_melhoria,
        COALESCE(med.has_medicao, FALSE) AS has_medicao
    FROM transformometro.processos p
    LEFT JOIN (
        SELECT processo_id, COUNT(*)::int AS cnt
        FROM transformometro.processo_instancias
        WHERE deletado = FALSE
        GROUP BY processo_id
    ) inst ON inst.processo_id = p.processo_id
    LEFT JOIN transformometro.processo_diagramas pd ON pd.processo_id = p.processo_id
    LEFT JOIN transformometro.processo_decomposicao pdc ON pdc.processo_id = p.processo_id
    LEFT JOIN (
        SELECT
            processo_id,
            BOOL_OR(lower(coalesce(cenario_tipo, '')) = 'baseline') AS has_baseline,
            BOOL_OR(lower(coalesce(cenario_tipo, '')) = 'melhoria') AS has_melhoria
        FROM transformometro.revisoes
        WHERE deletado = FALSE
        GROUP BY processo_id
    ) rev ON rev.processo_id = p.processo_id
    LEFT JOIN (
        SELECT DISTINCT r.processo_id, TRUE AS has_medicao
        FROM transformometro.revisoes r
        JOIN transformometro.medicoes m
            ON m.revisao_id = r.revisao_id AND m.deletado = FALSE
        WHERE r.deletado = FALSE
    ) med ON med.processo_id = p.processo_id
    WHERE p.processo_id = ANY(%s::uuid[])
      AND p.deletado = FALSE
"""

_EMPTY_STATS = {
    "instancia_count": 0,
    "diagram_node_count": 0,
    "decomposition_node_count": 0,
    "has_baseline": False,
    "has_melhoria": False,
    "has_medicao": False,
}


class ProcessoSetupStatsRepository(PluginBaseRepository):
    def fetch_by_processo_ids(self, processo_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not processo_ids:
            return {}
        rows = self.fetch_all(_SETUP_STATS_SQL, (processo_ids,))
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            pid = str(row.get("processo_id") or "")
            if not pid:
                continue
            result[pid] = {
                "instancia_count": int(row.get("instancia_count") or 0),
                "diagram_node_count": int(row.get("diagram_node_count") or 0),
                "decomposition_node_count": int(row.get("decomposition_node_count") or 0),
                "has_baseline": bool(row.get("has_baseline")),
                "has_melhoria": bool(row.get("has_melhoria")),
                "has_medicao": bool(row.get("has_medicao")),
            }
        return result

    @staticmethod
    def empty_stats() -> dict[str, Any]:
        return dict(_EMPTY_STATS)
