from __future__ import annotations

import calendar
from datetime import date, datetime, timezone
from typing import Any

from maint_app.application.list_query import ListQuery, paginate_slice
from maint_app.domain.ports.mini_applicators_totvs_port import MiniApplicatorsTotvsPort
from maint_app.infrastructure.persistence.repositories.operational_repositories import (
    ReposicaoRepository,
    RevisaoProgramadaRealizacaoRepository,
    RevisaoProgramadaRepository,
)

REVISAO_STATUS_RANK = {
    "CRÍTICO": 0,
    "ATENÇÃO": 1,
    "OK": 2,
    "SEM STATUS": 3,
}


def _as_naive_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value).strip()
        if not raw:
            return None
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.replace(tzinfo=None)
    return parsed


def add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _resolve_data_referencia(row: dict[str, Any]) -> datetime | None:
    manual = _as_naive_datetime(row.get("data_ultima_revisao"))
    if manual is not None:
        return manual
    return _as_naive_datetime(row.get("data_criacao"))


def _calc_status_revisao(*, dias_restantes: int, intervalo_meses: int) -> str:
    if dias_restantes < 0:
        return "CRÍTICO"
    intervalo_dias = max(intervalo_meses * 30, 1)
    atencao_limite = max(15, int(intervalo_dias * 0.15))
    if dias_restantes <= atencao_limite:
        return "ATENÇÃO"
    return "OK"


class RevisaoProgramadaService:
    def __init__(
        self,
        revisao_repo: RevisaoProgramadaRepository | None = None,
        realizacao_repo: RevisaoProgramadaRealizacaoRepository | None = None,
        reposicao_repo: ReposicaoRepository | None = None,
        totvs_gateway: MiniApplicatorsTotvsPort | None = None,
    ) -> None:
        self._revisao_repo = revisao_repo or RevisaoProgramadaRepository()
        self._realizacao_repo = realizacao_repo or RevisaoProgramadaRealizacaoRepository()
        self._reposicao_repo = reposicao_repo or ReposicaoRepository()
        self._totvs = totvs_gateway

    def listar_programacoes(
        self,
        *,
        filial: str,
        query: ListQuery | None = None,
        search: str | None = None,
        codigo_ferramenta: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = query or ListQuery(page=1, page_size=20, sort_by="ferramenta", sort_dir="asc")
        return self._revisao_repo.list_active_paged(
            filial=filial,
            query=query,
            search=search,
            codigo_ferramenta=codigo_ferramenta,
        )

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        codigo = str(payload.get("codigo_ferramenta") or "").strip().upper()
        if not codigo:
            raise ValueError("Informe o código da ferramenta.")
        intervalo = int(payload.get("intervalo_meses") or 0)
        if intervalo < 1 or intervalo > 120:
            raise ValueError("Intervalo deve estar entre 1 e 120 meses.")
        if self._revisao_repo.exists_active(
            filial=payload["filial"],
            codigo_ferramenta=codigo,
        ):
            raise ValueError("Já existe revisão programada para esta ferramenta.")
        return self._revisao_repo.create(
            filial=payload["filial"],
            codigo_ferramenta=codigo,
            intervalo_meses=intervalo,
            observacao=payload.get("observacao"),
            data_ultima_revisao=payload.get("data_ultima_revisao"),
        )

    def update(self, revisao_id: str, *, filial: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        intervalo = payload.get("intervalo_meses")
        if intervalo is not None:
            intervalo = int(intervalo)
            if intervalo < 1 or intervalo > 120:
                raise ValueError("Intervalo deve estar entre 1 e 120 meses.")
        return self._revisao_repo.update(
            revisao_id,
            filial=filial,
            intervalo_meses=intervalo if "intervalo_meses" in payload else None,
            observacao=payload.get("observacao") if "observacao" in payload else None,
            data_ultima_revisao=payload.get("data_ultima_revisao")
            if "data_ultima_revisao" in payload
            else None,
            update_data_ultima_revisao="data_ultima_revisao" in payload,
        )

    def delete(self, revisao_id: str, *, filial: str) -> bool:
        return self._revisao_repo.soft_delete(revisao_id, filial=filial)

    def registrar_revisao(
        self,
        revisao_id: str,
        *,
        filial: str,
        data_revisao: str | None = None,
    ) -> dict[str, Any] | None:
        row = self._revisao_repo.registrar_revisao(
            revisao_id,
            filial=filial,
            data_revisao=data_revisao,
        )
        if row and row.get("data_ultima_revisao"):
            self._realizacao_repo.create(
                revisao_id=str(row["revisao_id"]),
                filial=filial,
                codigo_ferramenta=str(row["codigo_ferramenta"]),
                data_revisao=_as_naive_datetime(row["data_ultima_revisao"]) or datetime.now(),
                intervalo_meses=int(row["intervalo_meses"]),
                observacao=row.get("observacao"),
            )
        return row

    def listar_realizacoes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        query: ListQuery | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = query or ListQuery(page=1, page_size=10, sort_by="data", sort_dir="desc")
        return self._realizacao_repo.list_by_ferramenta_paged(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            query=query,
        )

    def atualizar_realizacao(
        self,
        realizacao_id: str,
        *,
        filial: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not self._realizacao_repo.get_by_id(realizacao_id, filial=filial):
            return None
        updated = self._realizacao_repo.update(
            realizacao_id,
            filial=filial,
            data_revisao=payload.get("data_revisao")
            if "data_revisao" in payload
            else None,
            observacao=payload.get("observacao") if "observacao" in payload else None,
            update_data_revisao="data_revisao" in payload,
            update_observacao="observacao" in payload,
        )
        if updated:
            self._sync_schedule_reference(
                revisao_id=str(updated["revisao_id"]),
                filial=filial,
            )
        return updated

    def remover_realizacao(self, realizacao_id: str, *, filial: str) -> bool:
        row = self._realizacao_repo.get_by_id(realizacao_id, filial=filial)
        if not row:
            return False
        revisao_id = str(row["revisao_id"])
        if not self._realizacao_repo.delete(realizacao_id, filial=filial):
            return False
        self._sync_schedule_reference(revisao_id=revisao_id, filial=filial)
        return True

    def _sync_schedule_reference(self, *, revisao_id: str, filial: str) -> None:
        latest = self._realizacao_repo.get_latest_data_revisao(
            revisao_id=revisao_id,
            filial=filial,
        )
        self._revisao_repo.update(
            revisao_id,
            filial=filial,
            data_ultima_revisao=latest,
            update_data_ultima_revisao=True,
        )

    def resumo_alertas(self, *, filial: str) -> dict[str, int]:
        alertas = self._build_alertas(filial=filial)
        return {
            "critico": sum(1 for item in alertas if item["status"] == "CRÍTICO"),
            "atencao": sum(1 for item in alertas if item["status"] == "ATENÇÃO"),
            "ok": sum(1 for item in alertas if item["status"] == "OK"),
            "sem_status": sum(1 for item in alertas if item["status"] == "SEM STATUS"),
            "total": len(alertas),
        }

    def listar_alertas(
        self,
        *,
        filial: str,
        query: ListQuery | None = None,
        ferramenta: str | None = None,
        statuses: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = query or ListQuery(page=1, page_size=20, sort_by="dias_restantes", sort_dir="asc")
        alertas = self._build_alertas(filial=filial)
        alertas = self._enriquecer_descricoes(alertas, filial=filial)
        alertas = self._filter_alertas(alertas, ferramenta=ferramenta, statuses=statuses)
        alertas = self._sort_alertas(alertas, query.sort_by, query.sort_dir)
        return paginate_slice(alertas, query)

    def _build_alertas(self, *, filial: str) -> list[dict[str, Any]]:
        rows = self._revisao_repo.list_active(filial=filial)
        hoje = datetime.now(timezone.utc).replace(tzinfo=None).date()
        alertas: list[dict[str, Any]] = []

        for row in rows:
            intervalo_meses = int(row["intervalo_meses"])
            data_referencia = _resolve_data_referencia(row)
            if data_referencia is None:
                alertas.append(
                    self._build_alerta_item(
                        row=row,
                        filial=filial,
                        data_referencia=None,
                        data_proxima=None,
                        dias_desde=None,
                        dias_restantes=None,
                        status="SEM STATUS",
                    )
                )
                continue

            data_proxima = add_months(data_referencia, intervalo_meses)
            dias_desde = (hoje - data_referencia.date()).days
            dias_restantes = (data_proxima.date() - hoje).days
            status = _calc_status_revisao(
                dias_restantes=dias_restantes,
                intervalo_meses=intervalo_meses,
            )
            alertas.append(
                self._build_alerta_item(
                    row=row,
                    filial=filial,
                    data_referencia=data_referencia,
                    data_proxima=data_proxima,
                    dias_desde=dias_desde,
                    dias_restantes=dias_restantes,
                    status=status,
                )
            )
        return alertas

    @staticmethod
    def _build_alerta_item(
        *,
        row: dict[str, Any],
        filial: str,
        data_referencia: datetime | None,
        data_proxima: datetime | None,
        dias_desde: int | None,
        dias_restantes: int | None,
        status: str,
    ) -> dict[str, Any]:
        return {
            "revisao_id": str(row["revisao_id"]),
            "filial": filial,
            "codigo_ferramenta": row["codigo_ferramenta"],
            "intervalo_meses": int(row["intervalo_meses"]),
            "observacao": row.get("observacao"),
            "data_ultima_revisao": row.get("data_ultima_revisao"),
            "data_referencia": data_referencia,
            "data_proxima_revisao": data_proxima,
            "dias_desde_revisao": dias_desde,
            "dias_restantes": dias_restantes,
            "status": status,
        }

    @staticmethod
    def _matches_search(term: str | None, codigo: str, descricao: str | None) -> bool:
        if not term or not term.strip():
            return True
        normalized = term.strip().lower()
        if normalized in codigo.lower():
            return True
        if descricao and normalized in descricao.lower():
            return True
        return False

    def _filter_alertas(
        self,
        alertas: list[dict[str, Any]],
        *,
        ferramenta: str | None,
        statuses: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        result = alertas
        if ferramenta:
            result = [
                item
                for item in result
                if self._matches_search(
                    ferramenta,
                    str(item["codigo_ferramenta"]),
                    str(item.get("descricao_ferramenta") or ""),
                )
            ]
        if statuses:
            allowed = set(statuses)
            result = [item for item in result if str(item.get("status")) in allowed]
        return result

    @staticmethod
    def _sort_alertas(
        alertas: list[dict[str, Any]],
        sort_by: str | None,
        sort_dir: str,
    ) -> list[dict[str, Any]]:
        reverse = sort_dir == "desc"
        key_name = (sort_by or "dias_restantes").strip().lower()

        def sort_key(item: dict[str, Any]):
            if key_name == "status":
                return REVISAO_STATUS_RANK.get(str(item.get("status")), 99)
            if key_name == "ferramenta":
                return str(item.get("codigo_ferramenta") or "")
            if key_name == "intervalo":
                return int(item.get("intervalo_meses") or 0)
            if key_name == "ultima":
                return str(item.get("data_referencia") or "")
            if key_name == "proxima":
                return str(item.get("data_proxima_revisao") or "")
            if key_name == "dias_desde":
                return int(item.get("dias_desde_revisao") if item.get("dias_desde_revisao") is not None else 999999)
            return int(item.get("dias_restantes") if item.get("dias_restantes") is not None else 999999)

        return sorted(alertas, key=sort_key, reverse=reverse)

    def _enriquecer_descricoes(
        self,
        items: list[dict[str, Any]],
        *,
        filial: str,
    ) -> list[dict[str, Any]]:
        if not items or self._totvs is None:
            return items

        ferramentas = {str(item["codigo_ferramenta"]) for item in items}
        descricoes: dict[str, str] = {}
        for codigo in sorted(ferramentas):
            try:
                payload = self._totvs.obter_ferramenta(codigo)
                descricoes[codigo] = self._extract_descricao(payload)
            except Exception:
                descricoes[codigo] = ""

        for item in items:
            codigo = str(item["codigo_ferramenta"])
            item["descricao_ferramenta"] = descricoes.get(codigo, "")
        return items

    @staticmethod
    def _extract_descricao(payload: Any) -> str:
        if not isinstance(payload, dict):
            return ""
        if payload.get("descricao"):
            return str(payload["descricao"])
        data = payload.get("data")
        if isinstance(data, dict) and data.get("descricao"):
            return str(data["descricao"])
        return ""
