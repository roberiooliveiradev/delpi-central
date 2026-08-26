from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from maint_app.domain.ports.mini_applicators_totvs_port import MiniApplicatorsTotvsPort
from maint_app.application.list_query import ListQuery, paginate_slice
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

_ALERTAS_SNAPSHOT_TTL_SECONDS = 300
_alertas_snapshot_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}


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

    def resumo_alertas(self, *, filial: str) -> dict[str, int]:
        rules = self._status_repo.list_active(filial=filial)
        alertas = self._get_alertas_snapshot(filial=filial, rules=rules)
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
        peca: str | None = None,
        status: str | None = None,
        statuses: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = query or ListQuery(page=1, page_size=20, sort_by="percentual", sort_dir="desc")
        rules = self._status_repo.list_active(filial=filial)
        status_values = statuses if statuses is not None else ([status] if status else [])
        normalized_statuses = [
            str(item).strip().upper()
            for item in status_values
            if str(item).strip() and str(item).strip().upper() not in {"", "TODOS"}
        ]

        alertas = self._get_alertas_snapshot(filial=filial, rules=rules)
        alertas = self._enriquecer_descricoes(alertas, filial=filial)
        alertas = self._filter_alertas(
            alertas,
            ferramenta=ferramenta,
            peca=peca,
            statuses=normalized_statuses,
        )
        alertas = self._sort_alertas(alertas, query.sort_by, query.sort_dir)
        return paginate_slice(alertas, query)

    def obter_detalhe(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
    ) -> dict[str, Any]:
        rules = self._status_repo.list_active(filial=filial)
        alertas = self._get_alertas_snapshot(filial=filial, rules=rules)
        alerta = next(
            (
                item
                for item in alertas
                if item["codigo_ferramenta"] == codigo_ferramenta
                and item["codigo_peca"] == codigo_peca
            ),
            None,
        )
        historico = self.listar_historico(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            codigo_peca=codigo_peca,
        )

        ferramenta_payload: dict[str, Any] | None = None
        peca_descricao: str | None = None
        estoque_local_01: float | None = None

        if self._totvs is not None:
            try:
                ferramenta_payload = self._totvs.obter_ferramenta(codigo_ferramenta)
            except Exception:
                ferramenta_payload = None

            try:
                pecas_payload = self._totvs.listar_pecas(codigo_ferramenta)
                for peca in self._extract_items(pecas_payload):
                    if str(peca.get("codigo") or "").strip() == codigo_peca:
                        peca_descricao = str(peca.get("descricao") or "") or None
                        break
            except Exception:
                pass

            try:
                componentes_payload = self._totvs.listar_componentes(
                    codigo_ferramenta=codigo_ferramenta,
                    filial=filial,
                )
                for componente in self._extract_items(componentes_payload):
                    if str(componente.get("codigo") or "").strip() == codigo_peca:
                        if not peca_descricao:
                            peca_descricao = str(componente.get("descricao") or "") or None
                        raw_stock = componente.get("estoque_local_01")
                        if raw_stock is not None:
                            estoque_local_01 = float(raw_stock)
                        break
            except Exception:
                pass

        ferramenta_item = None
        if isinstance(ferramenta_payload, dict):
            ferramenta_item = {
                "codigo": codigo_ferramenta,
                "descricao": self._extract_descricao(ferramenta_payload),
            }

        return {
            "alerta": alerta,
            "ferramenta": ferramenta_item,
            "pecaDescricao": peca_descricao,
            "estoqueLocal01": estoque_local_01,
            "historico": historico,
        }

    def listar_historico(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
    ) -> list[dict[str, Any]]:
        rows = self._reposicao_repo.list_preventiva_by_ferramenta(
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

    def listar_ultimas_reposicoes(
        self,
        *,
        filial: str,
        query: ListQuery | None = None,
        ferramenta: str | None = None,
        peca: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = query or ListQuery(page=1, page_size=20, sort_by="data", sort_dir="desc")
        rows, total = self._reposicao_repo.list_ultimas_por_par_paged(
            filial=filial,
            query=query,
            ferramenta=ferramenta,
            peca=peca,
        )
        items = [
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
        enriched = self._enriquecer_descricoes(items, filial=filial)
        filtered = self._filter_ultimas(enriched, ferramenta=ferramenta, peca=peca)
        return filtered, total

    def _get_alertas_snapshot(
        self,
        *,
        filial: str,
        rules: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        now = time.monotonic()
        cached = _alertas_snapshot_cache.get(filial)
        if cached and (now - cached[0]) < _ALERTAS_SNAPSHOT_TTL_SECONDS:
            return [dict(item) for item in cached[1]]

        rows = self._reposicao_repo.list_ultimas_por_par(filial=filial)
        media_map = self._reposicao_repo.media_golpes_map(filial=filial)
        history_map = self._reposicao_repo.golpes_history_map(filial=filial)
        golpes_map = self._fetch_golpes_batch(filial=filial, rows=rows)
        alertas = self._build_alertas(
            rows,
            filial=filial,
            rules=rules,
            media_map=media_map,
            history_map=history_map,
            golpes_map=golpes_map,
        )
        _alertas_snapshot_cache[filial] = (now, alertas)
        return [dict(item) for item in alertas]

    @staticmethod
    def _format_data_inicial(data_ultima: Any) -> str:
        if isinstance(data_ultima, datetime):
            return data_ultima.replace(tzinfo=None).isoformat(timespec="seconds")
        raw = str(data_ultima or "").strip()
        return raw if "T" in raw else f"{raw[:10]}T00:00:00"

    def _fetch_golpes_batch(
        self,
        *,
        filial: str,
        rows: list[dict[str, Any]],
    ) -> dict[tuple[str, str], int]:
        if self._totvs is None or not rows:
            return {}

        data_final = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0).isoformat()
        items: list[dict[str, str]] = []
        keys: list[tuple[str, str]] = []
        for row in rows:
            codigo_ferramenta = str(row["codigo_ferramenta"])
            codigo_peca = str(row["codigo_peca"])
            keys.append((codigo_ferramenta, codigo_peca))
            items.append(
                {
                    "codigo_ferramenta": codigo_ferramenta,
                    "data_inicial": self._format_data_inicial(row["data_reposicao"]),
                    "data_final": data_final,
                }
            )

        if hasattr(self._totvs, "obter_golpes_batch"):
            try:
                payload = self._totvs.obter_golpes_batch(filial=filial, items=items)
                batch_items = payload.get("items") if isinstance(payload, dict) else None
                if isinstance(batch_items, list):
                    result: dict[tuple[str, str], int] = {}
                    for index, batch_item in enumerate(batch_items):
                        if not isinstance(batch_item, dict) or index >= len(keys):
                            continue
                        result[keys[index]] = int(batch_item.get("total_golpes") or 0)
                    if len(result) == len(keys):
                        return result
            except Exception:
                pass

        return self._fetch_golpes_threadpool(
            filial=filial,
            rows=rows,
            data_final=data_final,
        )

    def _fetch_golpes_threadpool(
        self,
        *,
        filial: str,
        rows: list[dict[str, Any]],
        data_final: str,
    ) -> dict[tuple[str, str], int]:
        if self._totvs is None or not rows:
            return {}

        result: dict[tuple[str, str], int] = {}
        max_workers = min(len(rows), 8)

        def _fetch_one(row: dict[str, Any]) -> tuple[tuple[str, str], int]:
            codigo_ferramenta = str(row["codigo_ferramenta"])
            codigo_peca = str(row["codigo_peca"])
            key = (codigo_ferramenta, codigo_peca)
            try:
                payload = self._totvs.obter_golpes(
                    filial=filial,
                    codigo_ferramenta=codigo_ferramenta,
                    data_inicial=self._format_data_inicial(row["data_reposicao"]),
                    data_final=data_final,
                )
                return key, int(payload.get("total_golpes") or 0)
            except Exception:
                return key, 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_fetch_one, row) for row in rows]
            for future in as_completed(futures):
                key, total = future.result()
                result[key] = total
        return result

    def _build_alertas(
        self,
        rows: list[dict[str, Any]],
        *,
        filial: str,
        rules: list[dict[str, Any]],
        media_map: dict[tuple[str, str], float] | None = None,
        history_map: dict[tuple[str, str], list[int]] | None = None,
        golpes_map: dict[tuple[str, str], int] | None = None,
    ) -> list[dict[str, Any]]:
        if media_map is None:
            media_map = self._reposicao_repo.media_golpes_map(filial=filial)
        if history_map is None:
            history_map = self._reposicao_repo.golpes_history_map(filial=filial)
        if golpes_map is None:
            golpes_map = self._fetch_golpes_batch(filial=filial, rows=rows)

        alertas: list[dict[str, Any]] = []
        for row in rows:
            key = (str(row["codigo_ferramenta"]), str(row["codigo_peca"]))
            media = media_map.get(key, 0.0)
            golpes_atuais = golpes_map.get(key, 0)
            percentual = (golpes_atuais / media * 100) if media > 0 else 0.0
            status_value = _match_status(percentual, rules) if media > 0 else "SEM STATUS"
            alertas.append(
                {
                    "filial": filial,
                    "codigo_ferramenta": row["codigo_ferramenta"],
                    "codigo_peca": row["codigo_peca"],
                    "data_ultima_reposicao": row["data_reposicao"],
                    "media_golpes": round(media, 2),
                    "golpes_atuais": golpes_atuais,
                    "golpes_history": history_map.get(key, []),
                    "percentual_uso": round(percentual, 2),
                    "status": status_value,
                }
            )
        return alertas

    @staticmethod
    def _matches_search(
        term: str | None,
        codigo: str,
        descricao: str | None,
    ) -> bool:
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
        peca: str | None,
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
        if peca:
            result = [
                item
                for item in result
                if self._matches_search(
                    peca,
                    str(item["codigo_peca"]),
                    str(item.get("descricao_peca") or ""),
                )
            ]
        if statuses:
            allowed = set(statuses)
            result = [item for item in result if str(item.get("status")) in allowed]
        return result

    def _filter_ultimas(
        self,
        items: list[dict[str, Any]],
        *,
        ferramenta: str | None,
        peca: str | None,
    ) -> list[dict[str, Any]]:
        result = items
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
        if peca:
            result = [
                item
                for item in result
                if self._matches_search(
                    peca,
                    str(item["codigo_peca"]),
                    str(item.get("descricao_peca") or ""),
                )
            ]
        return result

    @staticmethod
    def _sort_alertas(
        alertas: list[dict[str, Any]],
        sort_by: str | None,
        sort_dir: str,
    ) -> list[dict[str, Any]]:
        reverse = sort_dir == "desc"
        key_name = (sort_by or "percentual").strip().lower()

        def sort_key(item: dict[str, Any]):
            if key_name == "status":
                return STATUS_RANK.get(str(item.get("status")), 99)
            if key_name == "ferramenta":
                return str(item.get("codigo_ferramenta") or "")
            if key_name == "peca":
                return str(item.get("codigo_peca") or "")
            if key_name == "ultima":
                return str(item.get("data_ultima_reposicao") or "")
            if key_name == "golpes_atuais":
                return float(item.get("golpes_atuais") or 0)
            if key_name == "media":
                return float(item.get("media_golpes") or 0)
            return float(item.get("percentual_uso") or 0)

        return sorted(alertas, key=sort_key, reverse=reverse)

    def _enriquecer_descricoes(
        self,
        items: list[dict[str, Any]],
        *,
        filial: str,
    ) -> list[dict[str, Any]]:
        if not items:
            return items

        ferramentas = {str(item["codigo_ferramenta"]) for item in items}
        ferramenta_descricoes, peca_descricoes = self._resolver_descricoes(
            ferramentas,
            filial=filial,
        )

        for item in items:
            codigo_ferramenta = str(item["codigo_ferramenta"])
            codigo_peca = str(item["codigo_peca"])
            item["descricao_ferramenta"] = ferramenta_descricoes.get(codigo_ferramenta, "")
            item["descricao_peca"] = peca_descricoes.get((codigo_ferramenta, codigo_peca), "")

        return items

    def _resolver_descricoes(
        self,
        ferramentas: set[str],
        *,
        filial: str,
    ) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
        ferramenta_descricoes: dict[str, str] = {}
        peca_descricoes: dict[tuple[str, str], str] = {}

        if self._totvs is None:
            return ferramenta_descricoes, peca_descricoes

        for codigo_ferramenta in sorted(ferramentas):
            try:
                ferramenta_payload = self._totvs.obter_ferramenta(codigo_ferramenta)
                ferramenta_descricoes[codigo_ferramenta] = self._extract_descricao(ferramenta_payload)
            except Exception:
                ferramenta_descricoes[codigo_ferramenta] = ""

            try:
                pecas_payload = self._totvs.listar_pecas(codigo_ferramenta)
                for peca in self._extract_items(pecas_payload):
                    codigo_peca = str(peca.get("codigo") or "").strip()
                    if not codigo_peca:
                        continue
                    peca_descricoes[(codigo_ferramenta, codigo_peca)] = str(peca.get("descricao") or "")
            except Exception:
                pass

            try:
                componentes_payload = self._totvs.listar_componentes(
                    codigo_ferramenta=codigo_ferramenta,
                    filial=filial,
                )
                for componente in self._extract_items(componentes_payload):
                    codigo_peca = str(componente.get("codigo") or "").strip()
                    if not codigo_peca:
                        continue
                    key = (codigo_ferramenta, codigo_peca)
                    if key not in peca_descricoes or not peca_descricoes[key]:
                        peca_descricoes[key] = str(componente.get("descricao") or "")
            except Exception:
                pass

        return ferramenta_descricoes, peca_descricoes

    @staticmethod
    def _extract_items(payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        data = payload.get("data", payload)
        if isinstance(data, dict):
            items = data.get("items")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

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
