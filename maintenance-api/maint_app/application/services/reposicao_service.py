from __future__ import annotations

from datetime import datetime, timezone
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

    @staticmethod
    def _as_naive(dt: datetime) -> datetime:
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    def _parse_datetime(self, value: Any, *, field_name: str) -> datetime:
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                raise ValueError(f"{field_name} é obrigatória.")
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if isinstance(value, datetime):
            return value
        raise ValueError(f"{field_name} é obrigatória.")

    def validate_payload(
        self,
        payload: dict[str, Any],
        *,
        exclude_reposicao_id: str | None = None,
    ) -> dict[str, Any]:
        filial = str(payload.get("filial") or "").strip()
        codigo_ferramenta = str(payload.get("codigo_ferramenta") or "").strip()
        codigo_peca = str(payload.get("codigo_peca") or "").strip()
        motivo_id = str(payload.get("motivo_id") or "").strip()
        golpes = payload.get("golpes")
        data_reposicao = payload.get("data_reposicao")

        if filial not in {"01", "02"}:
            raise ValueError("Filial inválida. Use 01 ou 02.")
        if not codigo_ferramenta:
            raise ValueError("Código da ferramenta é obrigatório.")
        if not codigo_peca:
            raise ValueError("Código da peça é obrigatório.")
        if not motivo_id:
            raise ValueError("Motivo é obrigatório.")

        try:
            golpes_int = int(golpes)
        except (TypeError, ValueError) as exc:
            raise ValueError("Golpes deve ser um número inteiro maior que zero.") from exc
        if golpes_int <= 0:
            raise ValueError("Golpes deve ser maior que zero.")

        data_reposicao_dt = self._parse_datetime(data_reposicao, field_name="Data de reposição")

        raw_data_ultima = payload.get("data_ultima_reposicao")
        if raw_data_ultima:
            data_ultima_reposicao_dt = self._parse_datetime(
                raw_data_ultima,
                field_name="Data da última reposição",
            )
        elif exclude_reposicao_id is None:
            ultima = self._reposicao_repo.get_ultima_data(
                filial=filial,
                codigo_ferramenta=codigo_ferramenta,
                codigo_peca=codigo_peca,
            )
            data_ultima_reposicao_dt = ultima
        else:
            # Edição: não inferir última reposição do banco — regra de ordem vale no cadastro novo.
            data_ultima_reposicao_dt = None

        if data_ultima_reposicao_dt and self._as_naive(data_reposicao_dt) <= self._as_naive(
            data_ultima_reposicao_dt
        ):
            raise ValueError("Data de reposição deve ser posterior à última reposição.")

        return {
            "filial": filial,
            "codigo_ferramenta": codigo_ferramenta,
            "codigo_peca": codigo_peca,
            "data_reposicao": data_reposicao_dt,
            "data_ultima_reposicao": data_ultima_reposicao_dt,
            "golpes": golpes_int,
            "motivo_id": motivo_id,
            "observacao": (payload.get("observacao") or "").strip() or None,
        }

    def sugerir_golpes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
        data_inicial: str | None = None,
        data_final: str | None = None,
    ) -> dict[str, Any]:
        ultima = self._reposicao_repo.get_ultima_data(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            codigo_peca=codigo_peca,
        )
        if data_inicial:
            resolved_inicial = data_inicial
        elif ultima:
            resolved_inicial = ultima.replace(tzinfo=None).isoformat(timespec="seconds")
        else:
            resolved_inicial = "2000-01-01T00:00:00"

        if data_final:
            resolved_final = data_final
        else:
            resolved_final = datetime.utcnow().replace(microsecond=0).isoformat()

        total = 0
        if self._totvs is not None:
            data = self._totvs.obter_golpes(
                filial=filial,
                codigo_ferramenta=codigo_ferramenta,
                data_inicial=resolved_inicial,
                data_final=resolved_final,
            )
            total = int(data.get("total_golpes") or 0)

        return {
            "total_golpes": total,
            "data_ultima_reposicao": ultima.isoformat() if ultima else None,
            "data_inicial": resolved_inicial,
            "data_final": resolved_final,
        }

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
        normalized = self.validate_payload(
            {**existing, **payload},
            exclude_reposicao_id=reposicao_id,
        )
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
