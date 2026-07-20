from __future__ import annotations

from datetime import date
from typing import Any

from tm_app.application.services.dashboard_view_scope_service import count_active_filiais
from tm_app.application.services.process_revision_compare_service import (
    ProcessRevisionCompareService,
)
from tm_app.domain import calc_rules
from tm_app.domain.matrix.revisao_matriz_impacto_esforco_v1 import (
    MatrizImpactoEsforcoValidationError,
    build_persisted_matriz_payload,
)
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardDataRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import (
    RevisaoRepository,
)

CENARIO_LABELS: dict[str, str] = {
    "baseline": "Linha de base",
    "melhoria": "Melhoria de processo",
    "automacao": "Automação",
    "correcao": "Correção",
}

IMPACT_WEIGHTS: dict[str, float] = {
    "economia": 0.40,
    "horas": 0.20,
    "roi": 0.15,
    "qualidade": 0.15,
    "escopo": 0.10,
}

EFFORT_WEIGHTS: dict[str, float] = {
    "investimento": 0.45,
    "recursos": 0.25,
    "hh": 0.20,
    "complexidade": 0.10,
}

THRESHOLD_DEFAULT = 50

# Escalas absolutas (valor bruto → 1.0) quando o pool não permite percentil útil.
# Usadas com 1 revisão comparável ou componente empatado entre peers.
IMPACT_ABSOLUTE_REF: dict[str, float] = {
    "economia": 60_000.0,  # R$ líquidos / ano
    "horas": 1_200.0,  # horas economizadas / ano
    "roi": 3.0,  # razão
    "qualidade": 30.0,  # delta qualidade composto
    "escopo": 8.0,  # proxy complexidade (itens)
}

EFFORT_ABSOLUTE_REF: dict[str, float] = {
    "investimento": 80_000.0,  # R$ / ano
    "recursos": 24_000.0,  # R$ recursos / ano
    "hh": 200.0,  # proxy HH
    "complexidade": 8.0,
}


def _clamp_score(value: float) -> float:
    if not isinstance(value, (int, float)):
        return 0.0
    return max(0.0, min(100.0, float(value)))


def _percentile_rank(values: list[float], value: float) -> float:
    if not values:
        return 50.0
    if len(values) == 1:
        return 50.0
    sorted_vals = sorted(values)
    below = sum(1 for item in sorted_vals if item < value)
    equal = sum(1 for item in sorted_vals if item == value)
    rank = below + max(equal - 1, 0) / 2 if equal else below
    return (rank / (len(sorted_vals) - 1)) * 100.0


def _component_has_spread(values: list[float]) -> bool:
    if len(values) < 2:
        return False
    return (max(values) - min(values)) > 1e-9


def _absolute_unit_score(value: float, reference: float) -> float:
    """Mapeia valor bruto para 0..1 com saturação linear em ``reference``."""
    ref = max(float(reference), 1e-9)
    return max(0.0, min(1.0, max(0.0, float(value)) / ref))


def _normalize_component(
    peer_values: list[float],
    value: float,
    *,
    absolute_ref: float,
) -> float:
    """Percentil entre peers com variância; senão escala absoluta de negócio."""
    if _component_has_spread(peer_values):
        return _percentile_rank(peer_values, value) / 100.0
    return _absolute_unit_score(value, absolute_ref)


def _resolve_quadrant(impacto: float, esforco: float, threshold: float = THRESHOLD_DEFAULT) -> str:
    high_impact = impacto >= threshold
    high_effort = esforco >= threshold
    if high_impact and not high_effort:
        return "quick_win"
    if high_impact and high_effort:
        return "strategic"
    if not high_impact and not high_effort:
        return "fill_in"
    return "rethink"


def _shift_month(competencia: str, delta_months: int) -> str:
    year, month = map(int, competencia.split("-"))
    total = year * 12 + (month - 1) + delta_months
    new_year, new_month = divmod(total, 12)
    return f"{new_year:04d}-{new_month + 1:02d}"


class RevisaoImpactEffortMatrixService:
    """Matriz impacto × esforço por revisão (Playbook 21 — cálculo canônico na API)."""

    def __init__(self) -> None:
        self._compare = ProcessRevisionCompareService()
        self._calc = DashboardCalculatorService()

    def build_for_instancia(
        self,
        instancia_id: str,
        *,
        competencia: str | None = None,
        horizonte_meses: int = 12,
        incluir_rejeitadas: bool = False,
        incluir_baseline: bool = False,
        threshold: float = THRESHOLD_DEFAULT,
    ) -> dict[str, Any] | None:
        instancia = ProcessoInstanciaRepository().get(instancia_id)
        if not instancia:
            return None

        competencia = competencia or date.today().strftime("%Y-%m")
        horizonte_meses = max(1, min(int(horizonte_meses), 36))
        revisoes = RevisaoRepository().list_by_instancia(instancia_id)
        raw = DashboardDataRepository().load_raw()
        raw_filtered = self._filter_raw_for_instancia(raw, instancia_id)

        rows = self._calc.build_dashboard_rows(
            raw_filtered,
            escopo_unidades=count_active_filiais(),
        )
        rows_by_revisao = self._group_rows_by_revisao(rows)

        candidates = self._select_revisoes(
            revisoes,
            incluir_rejeitadas=incluir_rejeitadas,
            incluir_baseline=incluir_baseline,
        )
        prepared = [
            self._prepare_revision(
                revisao,
                rows_by_revisao=rows_by_revisao,
                raw=raw_filtered,
                competencia=competencia,
                horizonte_meses=horizonte_meses,
            )
            for revisao in candidates
        ]

        scoring_pool = [
            item
            for item in prepared
            if item["incluir_na_matriz"] and item["cenario_tipo"] in calc_rules.COMPARABLE_SCENARIOS
        ]
        pontos = [self._score_revision(item, scoring_pool, threshold=threshold) for item in prepared]

        ativo = next((p for p in pontos if p.get("revisao_ativa")), None)
        if ativo is None:
            ativo = next((p for p in pontos if p.get("incluir_na_matriz")), None)

        return {
            "instancia_id": instancia_id,
            "processo_id": str(instancia.get("processo_id") or ""),
            "competencia": competencia,
            "horizonte_meses": horizonte_meses,
            "threshold": threshold,
            "eixos": {
                "impacto": {"label": "Impacto", "min": 0, "max": 100},
                "esforco": {"label": "Esforço", "min": 0, "max": 100},
            },
            "quadrantes": {
                "quick_win": {"label": "Quick wins"},
                "strategic": {"label": "Estratégicos"},
                "fill_in": {"label": "Complementares"},
                "rethink": {"label": "Reavaliar"},
            },
            "pontos": pontos,
            "ativo": (
                {
                    "revisao_id": ativo["revisao_id"],
                    "impacto": ativo["impacto"],
                    "esforco": ativo["esforco"],
                    "quadrante": ativo["quadrante"],
                }
                if ativo
                else None
            ),
        }

    def build_for_processo(
        self,
        processo_id: str,
        *,
        competencia: str | None = None,
        horizonte_meses: int = 12,
        incluir_rejeitadas: bool = False,
        incluir_baseline: bool = False,
        threshold: float = THRESHOLD_DEFAULT,
    ) -> dict[str, Any] | None:
        processo = ProcessoRepository().get(processo_id)
        if not processo:
            return None

        instancias = [
            row
            for row in ProcessoInstanciaRepository().list_by_processo(processo_id)
            if not row.get("deletado")
        ]

        competencia = competencia or date.today().strftime("%Y-%m")
        horizonte_meses = max(1, min(int(horizonte_meses), 36))
        raw = DashboardDataRepository().load_raw()
        raw_filtered = self._filter_raw_for_processo(raw, processo_id)

        rows = self._calc.build_dashboard_rows(
            raw_filtered,
            escopo_unidades=count_active_filiais(),
        )
        rows_by_revisao = self._group_rows_by_revisao(rows)

        melhorias: list[dict[str, Any]] = []
        prepared: list[dict[str, Any]] = []

        for color_index, instancia in enumerate(instancias):
            instancia_id = str(instancia.get("instancia_id") or "")
            if not instancia_id:
                continue

            melhorias.append(
                {
                    "instancia_id": instancia_id,
                    "label": self._instancia_label(instancia),
                    "color_index": color_index % 8,
                }
            )

            revisoes = RevisaoRepository().list_by_instancia(instancia_id)
            candidates = self._select_revisoes(
                revisoes,
                incluir_rejeitadas=incluir_rejeitadas,
                incluir_baseline=incluir_baseline,
            )
            for revisao in candidates:
                item = self._prepare_revision(
                    revisao,
                    rows_by_revisao=rows_by_revisao,
                    raw=raw_filtered,
                    competencia=competencia,
                    horizonte_meses=horizonte_meses,
                )
                item["instancia_id"] = instancia_id
                item["instancia_label"] = self._instancia_label(instancia)
                item["instancia_color_index"] = color_index % 8
                prepared.append(item)

        scoring_pool = [
            item
            for item in prepared
            if item["incluir_na_matriz"] and item["cenario_tipo"] in calc_rules.COMPARABLE_SCENARIOS
        ]
        pontos = [
            self._score_revision(item, scoring_pool, threshold=threshold) for item in prepared
        ]

        ativos = [p for p in pontos if p.get("revisao_ativa") and p.get("incluir_na_matriz")]
        ativo = ativos[0] if len(ativos) == 1 else None

        return {
            "processo_id": processo_id,
            "competencia": competencia,
            "horizonte_meses": horizonte_meses,
            "threshold": threshold,
            "eixos": {
                "impacto": {"label": "Impacto", "min": 0, "max": 100},
                "esforco": {"label": "Esforço", "min": 0, "max": 100},
            },
            "quadrantes": {
                "quick_win": {"label": "Quick wins"},
                "strategic": {"label": "Estratégicos"},
                "fill_in": {"label": "Complementares"},
                "rethink": {"label": "Reavaliar"},
            },
            "melhorias": melhorias,
            "pontos": pontos,
            "ativo": (
                {
                    "revisao_id": ativo["revisao_id"],
                    "instancia_id": ativo.get("instancia_id"),
                    "impacto": ativo["impacto"],
                    "esforco": ativo["esforco"],
                    "quadrante": ativo["quadrante"],
                }
                if ativo
                else None
            ),
        }

    def build_for_revisao(
        self,
        revisao_id: str,
        *,
        competencia: str | None = None,
        horizonte_meses: int = 12,
        threshold: float = THRESHOLD_DEFAULT,
    ) -> dict[str, Any] | None:
        revisao = RevisaoRepository().get(revisao_id)
        if not revisao:
            return None

        instancia_id = str(revisao.get("instancia_id") or "")
        if not instancia_id:
            return None

        matrix = self.build_for_instancia(
            instancia_id,
            competencia=competencia,
            horizonte_meses=horizonte_meses,
            incluir_rejeitadas=True,
            incluir_baseline=True,
            threshold=threshold,
        )
        if not matrix:
            return None

        ponto = next((p for p in matrix["pontos"] if p["revisao_id"] == revisao_id), None)
        if not ponto:
            return None

        vizinhos = [
            {
                "revisao_id": p["revisao_id"],
                "impacto": p["impacto"],
                "esforco": p["esforco"],
                "quadrante": p["quadrante"],
            }
            for p in matrix["pontos"]
            if p["revisao_id"] != revisao_id and p.get("incluir_na_matriz")
        ]

        persisted = revisao.get("matriz_impacto_esforco")
        if persisted is not None and not isinstance(persisted, dict):
            persisted = None

        return {
            "revisao_id": revisao_id,
            "instancia_id": instancia_id,
            "competencia": matrix["competencia"],
            "horizonte_meses": matrix["horizonte_meses"],
            "threshold": matrix["threshold"],
            "ponto": ponto,
            "vizinhos": vizinhos,
            "inputs_persistidos": persisted,
        }

    def save_for_revisao(
        self,
        revisao_id: str,
        body: dict[str, Any],
        *,
        atualizado_por: str,
        competencia: str | None = None,
        horizonte_meses: int = 12,
    ) -> dict[str, Any] | None:
        revisao = RevisaoRepository().get(revisao_id)
        if not revisao:
            return None

        try:
            persisted = build_persisted_matriz_payload(body, atualizado_por=atualizado_por)
        except MatrizImpactoEsforcoValidationError as exc:
            raise ValueError(str(exc)) from exc

        updated = RevisaoRepository().update_matriz_impacto_esforco(revisao_id, persisted)
        if not updated:
            return None

        return self.build_for_revisao(
            revisao_id,
            competencia=competencia,
            horizonte_meses=horizonte_meses,
        )

    def _select_revisoes(
        self,
        revisoes: list[dict[str, Any]],
        *,
        incluir_rejeitadas: bool,
        incluir_baseline: bool,
    ) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        for revisao in revisoes:
            if revisao.get("deletado"):
                continue
            status = (revisao.get("status_aprovacao") or "").lower()
            if not incluir_rejeitadas and status == "rejeitada":
                continue
            cenario = (revisao.get("cenario_tipo") or "").lower()
            if cenario == "baseline" and not incluir_baseline:
                continue
            selected.append(revisao)
        return selected

    def _prepare_revision(
        self,
        revisao: dict[str, Any],
        *,
        rows_by_revisao: dict[str, list[dict[str, Any]]],
        raw: TransformometroRawData,
        competencia: str,
        horizonte_meses: int,
    ) -> dict[str, Any]:
        revisao_id = str(revisao.get("revisao_id") or "")
        cenario = (revisao.get("cenario_tipo") or "").lower()
        versao = str(revisao.get("versao_revisao") or revisao_id)
        cenario_label = CENARIO_LABELS.get(cenario, cenario)

        window_rows = self._rows_in_window(
            rows_by_revisao.get(revisao_id, []),
            competencia=competencia,
            horizonte_meses=horizonte_meses,
        )
        totals = self._compare._sum_revision_rows(window_rows)
        meses = max(len(window_rows), 1)

        economia_liquida_anual = totals["economia_liquida_mes"] * horizonte_meses / meses
        horas_anual = totals["horas_economizadas_mes"] * horizonte_meses / meses
        investimento_anual = totals["investimento_total_mes"] * horizonte_meses / meses
        custo_recursos_anual = totals["custo_recursos_compartilhados_mes"] * horizonte_meses / meses

        economia_mensal = totals["economia_liquida_mes"] / meses
        payback_meses = (
            round(investimento_anual / economia_mensal, 1)
            if economia_mensal > 0 and investimento_anual > 0
            else None
        )
        roi_medio = (
            round((economia_liquida_anual * 2) / investimento_anual, 2)
            if investimento_anual > 0 and economia_liquida_anual > 0
            else None
        )

        medicao = next(
            (m for m in raw.medicoes if str(m.get("revisao_id")) == revisao_id and not m.get("deletado")),
            None,
        )
        reference = RevisaoRepository().find_reference_for_revisao(revisao_id, revisao_row=revisao)
        ref_medicao = None
        if reference:
            ref_id = str(reference.get("revisao_id") or "")
            ref_medicao = next(
                (m for m in raw.medicoes if str(m.get("revisao_id")) == ref_id and not m.get("deletado")),
                None,
            )

        quality_delta = self._quality_delta(ref_medicao, medicao)
        investimentos_count = sum(
            1 for item in raw.investimentos if str(item.get("revisao_id")) == revisao_id and not item.get("deletado")
        )
        recursos_count = sum(
            1
            for item in raw.revisao_recursos_compartilhados
            if str(item.get("revisao_id")) == revisao_id
        )
        complexidade = float(investimentos_count + recursos_count)
        hh_proxy = float(investimentos_count) * 40.0

        has_medicao = medicao is not None
        has_reference = reference is not None
        has_custo = investimentos_count > 0 or recursos_count > 0

        if cenario == "baseline":
            confianca = "indisponivel"
            incluir_na_matriz = False
        elif has_medicao and has_reference and has_custo:
            confianca = "alta"
            incluir_na_matriz = cenario in calc_rules.COMPARABLE_SCENARIOS
        elif has_medicao and has_reference:
            confianca = "media"
            incluir_na_matriz = cenario in calc_rules.COMPARABLE_SCENARIOS
        else:
            confianca = "baixa"
            incluir_na_matriz = cenario in calc_rules.COMPARABLE_SCENARIOS

        persisted = revisao.get("matriz_impacto_esforco")
        modo = "auto"
        inputs_manuais: dict[str, Any] = {}
        overrides: dict[str, Any] = {}
        if isinstance(persisted, dict):
            modo = str(persisted.get("modo") or "auto")
            inputs_manuais = dict(persisted.get("inputs_manuais") or {})
            overrides = dict(persisted.get("overrides") or {})

        return {
            "revisao_id": revisao_id,
            "versao_revisao": versao,
            "cenario_tipo": cenario,
            "label": f"{versao} · {cenario_label}",
            "revisao_ativa": bool(revisao.get("revisao_ativa")),
            "incluir_na_matriz": incluir_na_matriz,
            "confianca": confianca,
            "modo": modo,
            "inputs_manuais": inputs_manuais,
            "overrides": overrides,
            "metricas": {
                "economia_liquida_anual": round(economia_liquida_anual, 2),
                "horas_economizadas_anual": round(horas_anual, 2),
                "roi_medio": roi_medio,
                "payback_meses": payback_meses,
                "investimento_total_anual": round(investimento_anual, 2),
                "custo_recursos_anual": round(custo_recursos_anual, 2),
            },
            "raw_components": {
                "impacto": {
                    "economia": max(economia_liquida_anual, 0.0),
                    "horas": max(horas_anual, 0.0),
                    "roi": max(roi_medio or 0.0, 0.0),
                    "qualidade": max(quality_delta, 0.0),
                    "escopo": complexidade,
                },
                "esforco": {
                    "investimento": max(investimento_anual, 0.0),
                    "recursos": max(custo_recursos_anual, 0.0),
                    "hh": hh_proxy,
                    "complexidade": complexidade,
                },
            },
        }

    def _score_revision(
        self,
        item: dict[str, Any],
        scoring_pool: list[dict[str, Any]],
        *,
        threshold: float,
    ) -> dict[str, Any]:
        impact_keys = list(IMPACT_WEIGHTS.keys())
        effort_keys = list(EFFORT_WEIGHTS.keys())

        impact_norm: dict[str, float] = {}
        effort_norm: dict[str, float] = {}
        used_percentile = False
        used_absolute = False
        for key in impact_keys:
            peer_values = [float(p["raw_components"]["impacto"][key]) for p in scoring_pool]
            value = float(item["raw_components"]["impacto"][key])
            if _component_has_spread(peer_values):
                used_percentile = True
            else:
                used_absolute = True
            impact_norm[key] = _normalize_component(
                peer_values,
                value,
                absolute_ref=IMPACT_ABSOLUTE_REF[key],
            )

        for key in effort_keys:
            peer_values = [float(p["raw_components"]["esforco"][key]) for p in scoring_pool]
            value = float(item["raw_components"]["esforco"][key])
            if _component_has_spread(peer_values):
                used_percentile = True
            else:
                used_absolute = True
            effort_norm[key] = _normalize_component(
                peer_values,
                value,
                absolute_ref=EFFORT_ABSOLUTE_REF[key],
            )

        if used_percentile and used_absolute:
            normalizacao = "mista"
        elif used_percentile:
            normalizacao = "percentil"
        else:
            normalizacao = "absoluta"

        impacto_auto = sum(impact_norm[key] * IMPACT_WEIGHTS[key] for key in impact_keys) * 100.0
        esforco_auto = sum(effort_norm[key] * EFFORT_WEIGHTS[key] for key in effort_keys) * 100.0

        modo = item.get("modo") or "auto"
        inputs = item.get("inputs_manuais") or {}
        manual_impacto = float(inputs.get("impacto_qualitativo") or 0) * 20.0
        manual_esforco = float(inputs.get("esforco_qualitativo") or 0) * 20.0

        if modo == "manual":
            impacto_score = manual_impacto if manual_impacto > 0 else impacto_auto
            esforco_score = manual_esforco if manual_esforco > 0 else esforco_auto
        elif modo == "hibrido":
            impacto_score = 0.7 * impacto_auto + 0.3 * manual_impacto if manual_impacto > 0 else impacto_auto
            esforco_score = 0.7 * esforco_auto + 0.3 * manual_esforco if manual_esforco > 0 else esforco_auto
        else:
            impacto_score = impacto_auto
            esforco_score = esforco_auto

        overrides = item.get("overrides") or {}
        if overrides.get("impacto") is not None:
            impacto_score = float(overrides["impacto"])
        if overrides.get("esforco") is not None:
            esforco_score = float(overrides["esforco"])

        impacto = round(_clamp_score(impacto_score), 1)
        esforco = round(_clamp_score(esforco_score), 1)
        quadrante = _resolve_quadrant(impacto, esforco, threshold)

        return {
            "revisao_id": item["revisao_id"],
            "versao_revisao": item["versao_revisao"],
            "cenario_tipo": item["cenario_tipo"],
            "label": item["label"],
            "revisao_ativa": item["revisao_ativa"],
            "impacto": impacto,
            "esforco": esforco,
            "quadrante": quadrante,
            "confianca": item["confianca"],
            "modo": modo,
            "incluir_na_matriz": item["incluir_na_matriz"],
            "normalizacao": normalizacao,
            "metricas": item["metricas"],
            "componentes": {
                "impacto": {key: round(impact_norm[key], 2) for key in impact_keys},
                "esforco": {key: round(effort_norm[key], 2) for key in effort_keys},
            },
            **(
                {
                    "instancia_id": item["instancia_id"],
                    "instancia_label": item["instancia_label"],
                    "instancia_color_index": item["instancia_color_index"],
                }
                if item.get("instancia_id")
                else {}
            ),
        }

    def _group_rows_by_revisao(self, rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            revisao_id = str(row.get("revisao_id") or "")
            if revisao_id:
                grouped.setdefault(revisao_id, []).append(row)
        return grouped

    def _rows_in_window(
        self,
        rows: list[dict[str, Any]],
        *,
        competencia: str,
        horizonte_meses: int,
    ) -> list[dict[str, Any]]:
        if not rows:
            return []
        start = _shift_month(competencia, -(horizonte_meses - 1))
        filtered = [
            row
            for row in rows
            if start <= str(row.get("competencia") or "") <= competencia
        ]
        return sorted(filtered, key=lambda row: row.get("competencia") or "")

    def _quality_delta(
        self,
        reference: dict[str, Any] | None,
        current: dict[str, Any] | None,
    ) -> float:
        if not reference or not current:
            return 0.0
        ref_retrabalho = float(reference.get("percentual_retrabalho") or 0)
        cur_retrabalho = float(current.get("percentual_retrabalho") or 0)
        ref_erros = float(reference.get("quantidade_erros_mes") or 0)
        cur_erros = float(current.get("quantidade_erros_mes") or 0)
        retrabalho_delta = max(0.0, ref_retrabalho - cur_retrabalho)
        erro_delta = max(0.0, ref_erros - cur_erros)
        return retrabalho_delta * 100.0 + erro_delta

    def _instancia_label(self, instancia: dict[str, Any]) -> str:
        rotulo = str(instancia.get("rotulo_instancia") or "").strip()
        if rotulo:
            return rotulo
        if instancia.get("todas_filiais_ativas"):
            return "Todas as unidades"
        filial = str(instancia.get("nome_filial") or instancia.get("codigo_filial") or "").strip()
        setores = instancia.get("setores") or []
        if isinstance(setores, str):
            setores = []
        setor_labels = [
            str(item.get("nome_setor") or item.get("codigo_setor") or "").strip()
            for item in setores
            if isinstance(item, dict)
        ]
        setor_labels = [label for label in setor_labels if label]
        if filial and setor_labels:
            return f"{filial} · {', '.join(setor_labels[:2])}"
        if filial:
            return filial
        if setor_labels:
            return ", ".join(setor_labels[:2])
        instancia_id = str(instancia.get("instancia_id") or "")
        return instancia_id[:8] if instancia_id else "Melhoria"

    def _filter_raw_for_processo(self, raw: TransformometroRawData, processo_id: str) -> TransformometroRawData:
        instancia_ids = {
            str(item.get("instancia_id"))
            for item in raw.processo_instancias
            if str(item.get("processo_id")) == processo_id
        }
        revisao_ids = {
            str(item.get("revisao_id"))
            for item in raw.revisoes
            if str(item.get("processo_id")) == processo_id
            or str(item.get("instancia_id")) in instancia_ids
        }

        target_resource_ids = {
            str(v.get("recurso_compartilhado_id"))
            for v in raw.revisao_recursos_compartilhados
            if str(v.get("revisao_id")) in revisao_ids and v.get("recurso_compartilhado_id") is not None
        }
        related_resource_links = [
            v
            for v in raw.revisao_recursos_compartilhados
            if str(v.get("recurso_compartilhado_id")) in target_resource_ids
        ]
        related_resources = [
            r
            for r in raw.recursos_compartilhados
            if str(r.get("recurso_compartilhado_id")) in target_resource_ids
        ]
        related_resource_costs = [
            c
            for c in raw.recurso_custos
            if str(c.get("recurso_compartilhado_id")) in target_resource_ids
        ]

        return TransformometroRawData(
            processos=[p for p in raw.processos if str(p.get("processo_id")) == processo_id],
            processo_instancias=[
                i for i in raw.processo_instancias if str(i.get("instancia_id")) in instancia_ids
            ],
            revisoes=[r for r in raw.revisoes if str(r.get("revisao_id")) in revisao_ids],
            medicoes=[m for m in raw.medicoes if str(m.get("revisao_id")) in revisao_ids],
            investimentos=[i for i in raw.investimentos if str(i.get("revisao_id")) in revisao_ids],
            recursos_compartilhados=related_resources,
            revisao_recursos_compartilhados=related_resource_links,
            recurso_custos=related_resource_costs,
        )

    def _filter_raw_for_instancia(self, raw: TransformometroRawData, instancia_id: str) -> TransformometroRawData:
        revisao_ids = {
            str(r.get("revisao_id"))
            for r in raw.revisoes
            if str(r.get("instancia_id")) == instancia_id
        }
        processo_ids = {
            str(r.get("processo_id"))
            for r in raw.revisoes
            if str(r.get("revisao_id")) in revisao_ids
        }

        target_resource_ids = {
            str(v.get("recurso_compartilhado_id"))
            for v in raw.revisao_recursos_compartilhados
            if str(v.get("revisao_id")) in revisao_ids and v.get("recurso_compartilhado_id") is not None
        }
        related_resource_links = [
            v
            for v in raw.revisao_recursos_compartilhados
            if str(v.get("recurso_compartilhado_id")) in target_resource_ids
        ]
        related_resources = [
            r
            for r in raw.recursos_compartilhados
            if str(r.get("recurso_compartilhado_id")) in target_resource_ids
        ]
        related_resource_costs = [
            c
            for c in raw.recurso_custos
            if str(c.get("recurso_compartilhado_id")) in target_resource_ids
        ]

        return TransformometroRawData(
            processos=[p for p in raw.processos if str(p.get("processo_id")) in processo_ids],
            processo_instancias=[
                i for i in raw.processo_instancias if str(i.get("instancia_id")) == instancia_id
            ],
            revisoes=[r for r in raw.revisoes if str(r.get("revisao_id")) in revisao_ids],
            medicoes=[m for m in raw.medicoes if str(m.get("revisao_id")) in revisao_ids],
            investimentos=[i for i in raw.investimentos if str(i.get("revisao_id")) in revisao_ids],
            recursos_compartilhados=related_resources,
            revisao_recursos_compartilhados=related_resource_links,
            recurso_custos=related_resource_costs,
        )
