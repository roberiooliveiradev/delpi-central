"""Orquestra ranking TOTVS + flag already_registered do cadastro Postgres."""

from __future__ import annotations

from typing import Any

from maint_app.domain.ports.machine_programs_totvs_port import MachineProgramsTotvsPort
from maint_app.infrastructure.persistence.repositories.programas_maquina_repository import (
    ProgramasMaquinaProdutosRepository,
)


class ProgramasMaquinaService:
    def __init__(
        self,
        *,
        totvs_gateway: MachineProgramsTotvsPort,
        produtos_repo: ProgramasMaquinaProdutosRepository | None = None,
    ) -> None:
        self._totvs = totvs_gateway
        self._produtos = produtos_repo or ProgramasMaquinaProdutosRepository()

    def ranking(
        self,
        *,
        filial: str,
        data_inicial: str | None = None,
        data_final: str | None = None,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        data = self._totvs.listar_top_intermediates(
            filial=filial,
            data_inicial=data_inicial,
            data_final=data_final,
            page=page,
            page_size=page_size,
            search=search,
            authorization=authorization,
        )
        registered = self._produtos.list_active_codes(filial=filial)
        items = []
        for raw in data.get("items") or []:
            if not isinstance(raw, dict):
                continue
            code = str(raw.get("intermediate_code") or "").strip()
            item = dict(raw)
            item["already_registered"] = code in registered
            items.append(item)
        return {
            "items": items,
            "page": data.get("page", page),
            "page_size": data.get("page_size", page_size),
            "total": data.get("total", len(items)),
            "total_pages": data.get("total_pages", 0),
            "summary": data.get("summary") or {},
        }
