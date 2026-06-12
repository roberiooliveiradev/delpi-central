from __future__ import annotations

from datetime import datetime
from typing import Any

from maint_app.application.services.filial_access_scope_service import FilialAccessScope
from maint_app.domain.ports.mini_applicators_totvs_port import MiniApplicatorsTotvsPort
from maint_app.infrastructure.persistence.repositories.operational_repositories import (
    ReposicaoRepository,
)


class ReposicaoService:
    def __init__(
        self,
        reposicao_repo: ReposicaoRepository | None = None,
        totvs_gateway: MiniApplicatorsTotvsPort | None = None,
    ) -> None:
        self._reposicao_repo = reposicao_repo or ReposicaoRepository()
        self._totvs = totvs_gateway

    def validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        filial = str(payload.get("filial") or "").strip()
        codigo_ferramenta = str(payload.get("codigo_ferramenta") or "").strip()
        codigo_peca = str(payload.get("codigo_peca") or "").strip()
        motivo_id = payload.get("motivo_id")
        golpes = payload.get("golpes")
        data_reposicao = payload.get("data_reposicao")

        if filial not in {"01", "02"}:
            raise ValueError("Filial inválida. Use 01 ou 02.")
        if not codigo_ferramenta:
            raise ValueError("Código da ferramenta é obrigatório.")
        if not codigo_peca:
            raise ValueError("Código da peça é obrigatório.")
        if motivo_id is None:
            raise ValueError("Motivo é obrigatório.")

        try:
            golpes_int = int(golpes)
        except (TypeError, ValueError) as exc:
            raise ValueError("Golpes deve ser um número inteiro maior que zero.") from exc
        if golpes_int <= 0:
            raise ValueError("Golpes deve ser maior que zero.")

        if isinstance(data_reposicao, str):
            data_reposicao_dt = datetime.fromisoformat(data_reposicao.replace("Z", "+00:00"))
        elif isinstance(data_reposicao, datetime):
            data_reposicao_dt = data_reposicao
        else:
            raise ValueError("Data de reposição é obrigatória.")

        ultima = self._reposicao_repo.get_ultima_data(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            codigo_peca=codigo_peca,
        )
        if ultima and data_reposicao_dt <= ultima:
            raise ValueError("Data de reposição deve ser posterior à última reposição.")

        return {
            "filial": filial,
            "codigo_ferramenta": codigo_ferramenta,
            "codigo_peca": codigo_peca,
            "data_reposicao": data_reposicao_dt,
            "data_ultima_reposicao": ultima,
            "golpes": golpes_int,
            "motivo_id": int(motivo_id),
            "observacao": (payload.get("observacao") or "").strip() or None,
        }

    def sugerir_golpes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
    ) -> int:
        if self._totvs is None:
            return 0
        ultima = self._reposicao_repo.get_ultima_data(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            codigo_peca=codigo_peca,
        )
        data_inicial = ultima.date().isoformat() if ultima else "2000-01-01"
        data_final = datetime.utcnow().date().isoformat()
        data = self._totvs.obter_golpes(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            data_inicial=data_inicial,
            data_final=data_final,
        )
        return int(data.get("total_golpes") or 0)

    def create(
        self,
        payload: dict[str, Any],
        *,
        scope: FilialAccessScope,
        user: Any | None,
    ) -> dict[str, Any]:
        normalized = self.validate_payload(payload)
        from maint_app.application.services.filial_access_scope_service import (
            FilialAccessScopeService,
        )

        FilialAccessScopeService().assert_manage_filial(
            scope,
            normalized["filial"],
            user=user,
        )
        return self._reposicao_repo.create(normalized)

    def update(
        self,
        reposicao_id: str,
        payload: dict[str, Any],
        *,
        scope: FilialAccessScope,
        user: Any | None,
    ) -> dict[str, Any] | None:
        existing = self._reposicao_repo.get_by_id(reposicao_id)
        if not existing:
            return None
        normalized = self.validate_payload({**existing, **payload})
        from maint_app.application.services.filial_access_scope_service import (
            FilialAccessScopeService,
        )

        FilialAccessScopeService().assert_manage_filial(
            scope,
            normalized["filial"],
            user=user,
        )
        return self._reposicao_repo.update(reposicao_id, normalized)

    def delete(
        self,
        reposicao_id: str,
        *,
        scope: FilialAccessScope,
        user: Any | None,
    ) -> bool:
        existing = self._reposicao_repo.get_by_id(reposicao_id)
        if not existing:
            return False
        from maint_app.application.services.filial_access_scope_service import (
            FilialAccessScopeService,
        )

        FilialAccessScopeService().assert_manage_filial(
            scope,
            str(existing["filial"]),
            user=user,
        )
        return self._reposicao_repo.soft_delete(reposicao_id)
