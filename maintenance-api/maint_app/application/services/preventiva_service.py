from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from maint_app.domain.ports.mini_applicators_totvs_port import MiniApplicatorsTotvsPort
from maint_app.infrastructure.persistence.repositories.operational_repositories import (
    ReposicaoRepository,
    StatusPecaRepository,
)

STATUS_RANK = {
    "CRÍTICO": 0,
    "ATENÇÃO": 1,
    "OK": 2,
    "SEM STATUS": 3,
}


def _match_status(percentual_uso: float, rules: list[dict[str, Any]]) -> str:
    for rule in rules:
        operador = str(rule.get("operador") or "")
        limite = int(rule.get("percentual") or 0)
        descricao = str(rule.get("descricao") or "SEM STATUS")
        if operador == ">=" and percentual_uso >= limite:
            return descricao
        if operador == ">" and percentual_uso > limite:
            return descricao
        if operador == "<=" and percentual_uso <= limite:
            return descricao
        if operador == "<" and percentual_uso < limite:
            return descricao
    return "SEM STATUS"


class PreventivaService:
    def __init__(
        self,
        reposicao_repo: ReposicaoRepository | None = None,
        status_repo: StatusPecaRepository | None = None,
        totvs_gateway: MiniApplicatorsTotvsPort | None = None,
    ) -> None:
        self._reposicao_repo = reposicao_repo or ReposicaoRepository()
        self._status_repo = status_repo or StatusPecaRepository()
        self._totvs = totvs_gateway

    def listar_alertas(self, *, filial: str) -> list[dict[str, Any]]:
        rules = self._status_repo.list_active()
        ultimas = self._reposicao_repo.list_ultimas_por_par(filial=filial)
        alertas: list[dict[str, Any]] = []

        for row in ultimas:
            media = self._reposicao_repo.media_golpes(
                filial=filial,
                codigo_ferramenta=row["codigo_ferramenta"],
                codigo_peca=row["codigo_peca"],
            )
            golpes_atuais = self._obter_golpes_atuais(
                filial=filial,
                codigo_ferramenta=row["codigo_ferramenta"],
                codigo_peca=row["codigo_peca"],
                data_ultima=row["data_reposicao"],
            )
            percentual = (golpes_atuais / media * 100) if media > 0 else 0.0
            status = _match_status(percentual, rules) if media > 0 else "SEM STATUS"

            alertas.append(
                {
                    "filial": filial,
                    "codigo_ferramenta": row["codigo_ferramenta"],
                    "codigo_peca": row["codigo_peca"],
                    "data_ultima_reposicao": row["data_reposicao"],
                    "media_golpes": round(media, 2),
                    "golpes_atuais": golpes_atuais,
                    "percentual_uso": round(percentual, 2),
                    "status": status,
                }
            )

        alertas.sort(
            key=lambda item: (
                STATUS_RANK.get(str(item["status"]), 99),
                str(item["codigo_ferramenta"]),
                str(item["codigo_peca"]),
            )
        )
        return alertas

    def listar_historico(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
    ) -> list[dict[str, Any]]:
        rows = self._reposicao_repo.list_by_ferramenta(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            codigo_peca=codigo_peca,
        )
        return [
            {
                "reposicao_id": str(row["reposicao_id"]),
                "data_reposicao": row["data_reposicao"],
                "golpes": int(row["golpes"]),
            }
            for row in rows
        ]

    def listar_ultimas_reposicoes(self, *, filial: str) -> list[dict[str, Any]]:
        rows = self._reposicao_repo.list_ultimas_por_par(filial=filial)
        return [
            {
                "reposicao_id": str(row["reposicao_id"]),
                "filial": row["filial"],
                "codigo_ferramenta": row["codigo_ferramenta"],
                "codigo_peca": row["codigo_peca"],
                "data_reposicao": row["data_reposicao"],
                "golpes": int(row["golpes"]),
            }
            for row in rows
        ]

    def _obter_golpes_atuais(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
        data_ultima: Any,
    ) -> int:
        if self._totvs is None:
            return 0

        if isinstance(data_ultima, datetime):
            data_inicial = data_ultima.date().isoformat()
        else:
            data_inicial = str(data_ultima)[:10]

        data_final = datetime.now(timezone.utc).date().isoformat()
        try:
            payload = self._totvs.obter_golpes(
                filial=filial,
                codigo_ferramenta=codigo_ferramenta,
                data_inicial=data_inicial,
                data_final=data_final,
            )
            return int(payload.get("total_golpes") or 0)
        except Exception:
            return 0
