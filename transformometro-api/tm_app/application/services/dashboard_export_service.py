from __future__ import annotations

import csv
import io
from typing import Any

from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardCalculoRepository,
)


class DashboardExportService:
    def build_csv(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> str:
        rows = DashboardCalculoRepository().query_export_rows(
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(
            [
                "codigo_processo",
                "nome_processo",
                "familia_processo",
                "agrupador_ferramenta",
                "filial_id",
                "setor_id",
                "competencia",
                "cenario_tipo",
                "economia_bruta",
                "economia_liquida_mes",
                "investimento_unico_mes",
                "custo_recorrente_mes",
                "horas_economizadas_mes",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.get("codigo_processo"),
                    row.get("nome_processo"),
                    row.get("familia_processo"),
                    row.get("agrupador_ferramenta"),
                    row.get("filial_id"),
                    row.get("setor_id"),
                    row.get("competencia"),
                    row.get("cenario_tipo"),
                    row.get("economia_bruta"),
                    row.get("economia_liquida_mes"),
                    row.get("investimento_unico_mes"),
                    row.get("custo_recorrente_mes"),
                    row.get("horas_economizadas_mes"),
                ]
            )
        return buffer.getvalue()
