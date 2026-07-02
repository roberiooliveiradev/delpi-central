from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService


class DashboardView(str, Enum):
    CONSOLIDATED = "consolidated"
    FILIAL = "filial"
    DEPARTMENT = "department"


_VIEW_ALIASES = {
    "consolidated": DashboardView.CONSOLIDATED,
    "consolidado": DashboardView.CONSOLIDATED,
    "filial": DashboardView.FILIAL,
    "branch": DashboardView.FILIAL,
    "department": DashboardView.DEPARTMENT,
    "departamento": DashboardView.DEPARTMENT,
    "setor": DashboardView.DEPARTMENT,
}


@dataclass(frozen=True)
class DashboardScopeFilters:
    view: DashboardView
    # ``filial_id``/``setor_id`` são CSV (uma ou várias unidades/setores) para compatibilidade
    # com os call sites existentes; ``filial_ids``/``setor_ids`` expõem o conjunto normalizado.
    filial_id: str | None
    setor_id: str | None

    @property
    def applies_process_filter(self) -> bool:
        return self.view != DashboardView.CONSOLIDATED

    @property
    def filial_ids(self) -> frozenset[str]:
        return _split_csv(self.filial_id)

    @property
    def setor_ids(self) -> frozenset[str]:
        return _split_csv(self.setor_id)


class DashboardViewScopeService:
    """Resolve visão analítica (consolidado / filial / departamento) em filtros canônicos."""

    def resolve(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
    ) -> DashboardScopeFilters:
        filial = _normalize_csv(filial_id)
        setor = _normalize_csv(setor_id)
        resolved_view = self._resolve_view(view=view, filial_id=filial, setor_id=setor)

        if resolved_view == DashboardView.CONSOLIDATED:
            return DashboardScopeFilters(
                view=DashboardView.CONSOLIDATED,
                filial_id=None,
                setor_id=None,
            )
        if resolved_view == DashboardView.FILIAL:
            if not filial:
                raise ValueError("visão filial exige filial_id")
            if setor:
                raise ValueError("visão filial não aceita setor_id; use view=department")
            return DashboardScopeFilters(
                view=DashboardView.FILIAL,
                filial_id=filial,
                setor_id=None,
            )

        if not filial or not setor:
            raise ValueError("visão departamento exige filial_id e setor_id")
        return DashboardScopeFilters(
            view=DashboardView.DEPARTMENT,
            filial_id=filial,
            setor_id=setor,
        )

    @staticmethod
    def _resolve_view(
        *,
        view: str | None,
        filial_id: str | None,
        setor_id: str | None,
    ) -> DashboardView:
        if view:
            key = view.strip().lower()
            if key not in _VIEW_ALIASES:
                allowed = ", ".join(sorted(_VIEW_ALIASES))
                raise ValueError(f"view inválida '{view}'; use: {allowed}")
            return _VIEW_ALIASES[key]
        if setor_id:
            return DashboardView.DEPARTMENT
        if filial_id:
            return DashboardView.FILIAL
        return DashboardView.CONSOLIDATED

    def filter_raw_preserving_resource_rateio(
        self,
        raw: TransformometroRawData,
        scope: DashboardScopeFilters,
        calculator: DashboardCalculatorService,
        *,
        familia_processo: str | None = None,
    ) -> TransformometroRawData:
        if not scope.applies_process_filter and not familia_processo:
            return raw

        filtered = calculator.filter_raw(
            raw,
            filial_id=scope.filial_id,
            setor_id=scope.setor_id,
            familia_processo=familia_processo,
        )
        if filtered is raw:
            return raw

        target_resource_ids = {
            str(v.get("recurso_compartilhado_id"))
            for v in filtered.revisao_recursos_compartilhados
            if v.get("recurso_compartilhado_id") is not None
        }
        if not target_resource_ids:
            return filtered

        return TransformometroRawData(
            processos=filtered.processos,
            processo_instancias=filtered.processo_instancias,
            revisoes=filtered.revisoes,
            medicoes=filtered.medicoes,
            investimentos=filtered.investimentos,
            recursos_compartilhados=[
                r
                for r in raw.recursos_compartilhados
                if str(r.get("recurso_compartilhado_id")) in target_resource_ids
            ],
            revisao_recursos_compartilhados=[
                v
                for v in raw.revisao_recursos_compartilhados
                if str(v.get("recurso_compartilhado_id")) in target_resource_ids
            ],
            recurso_custos=[
                c
                for c in raw.recurso_custos
                if str(c.get("recurso_compartilhado_id")) in target_resource_ids
            ],
        )

    def scope_meta(self, scope: DashboardScopeFilters) -> dict[str, Any]:
        return {
            "view": scope.view.value,
            "filial_id": scope.filial_id,
            "setor_id": scope.setor_id,
            "filial_ids": sorted(scope.filial_ids),
            "setor_ids": sorted(scope.setor_ids),
        }


def _normalize_ref(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _split_csv(value: str | None) -> frozenset[str]:
    if not value:
        return frozenset()
    return frozenset(token.strip() for token in str(value).split(",") if token.strip())


def _normalize_csv(value: str | None) -> str | None:
    """Normaliza uma lista CSV de refs: remove vazios e duplicados (case-insensitive)."""
    if value is None:
        return None
    seen: set[str] = set()
    out: list[str] = []
    for token in str(value).split(","):
        text = token.strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return ",".join(out) or None
