/** ViewModel da Visão geral — mapeia o contrato `/v1/overview` para os
 * cards. Toda formatação segue as mesmas regras do Dashboard
 * Engenharia (paridade): valores com prefixo/sufixo/decimais do owner
 * via `formatDashboardMetricValue`, ROI em `×`, metas/IDD via
 * `buildKpiGoalPresentation` do kit. Ausência oficial (`value: null`)
 * renderiza "—"; estados (empty/unavailable/forbidden) viram cards de
 * estado, nunca zero. */

import type { OverviewIndicator, OverviewResponse } from "../../types/overview";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
  formatOperationalUnitCode,
  resolveIndicatorIddScoreLabelFromSi,
  type DashboardGoalFields,
} from "@delpi/plugin-ui/index";

export type OverviewCardState = IndicatorAvailability_;

type IndicatorAvailability_ = OverviewIndicator["availability"];

export type OverviewKpiCardVm = {
  id: string;
  family: "lmp" | "transforma";
  title: string;
  titleHint?: string;
  availability: OverviewCardState;
  value: string;
  contextLabel?: string;
  goalLabel?: string | null;
  goalPrefix?: string | null;
  goalHint?: string | null;
  monthlyGoalLabel?: string | null;
  monthlyGoalPrefix?: string | null;
  monthlyGoalHint?: string | null;
  goalScopeBadge?: ReturnType<typeof buildKpiGoalPresentation>["goalScopeBadge"];
  goalScopeHint?: string | null;
  goalPerformanceBadge?: ReturnType<
    typeof buildKpiGoalPresentation
  >["goalPerformanceBadge"];
  iddScoreLabel?: string | null;
  stateMessage?: string | null;
};

const TITLE_HINTS: Record<string, string> = {
  lmp_on_time:
    "Percentual de LMPs concluídas dentro do prazo no período — fonte oficial api-delpi.",
  lmp_lead_time: "Média de dias úteis entre abertura e conclusão das LMPs.",
  lmp_total_proposals: "Quantidade oficial de propostas/LMPs no recorte.",
  transforma_gross_savings:
    "Ganhos brutos das soluções TRANSFORMA+ no período.",
  transforma_solutions:
    "Quantidade de soluções TRANSFORMA+ implementadas.",
  transforma_roi: "Razão média retorno/investimento das soluções TRANSFORMA+.",
};

const CONTEXT_FALLBACK: Record<string, string> = {
  lmp_lead_time: "Média no período",
  lmp_total_proposals: "LMPs / amostras no recorte",
  transforma_solutions: "Melhorias na planilha",
  transforma_roi: "No período filtrado",
};

function goalFieldsOf(ind: OverviewIndicator): DashboardGoalFields {
  return {
    goal_label: ind.goal_label,
    goal_value: ind.goal_value,
    comparable_goal: ind.comparable_goal,
    reference_goal: ind.reference_goal,
    target: ind.target,
    has_goal: ind.has_goal ?? undefined,
    goal_aggregation: ind.goal_aggregation,
    goal_mode: ind.goal_mode,
    goal_period_kind: ind.goal_period_kind,
    goal_period_partial: ind.goal_period_partial,
    goal_scope_branch: ind.goal_scope_branch,
    goal_scope_label: ind.goal_scope_label,
    goal_scope_hint: ind.goal_scope_hint,
    scope_type: ind.scope_type,
    performance_direction: ind.performance_direction,
    value_unit: ind.value_unit,
    value_prefix: ind.value_prefix,
    value_suffix: ind.value_suffix,
    value_decimals: ind.value_decimals,
    start_date: ind.start_date,
    end_date: ind.end_date,
  };
}

function formatRoi(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}×`;
}

function formatCount(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR");
}

function formatValue(ind: OverviewIndicator): string {
  if (ind.value == null || Number.isNaN(ind.value)) return "—";
  if (ind.id === "transforma_roi") return formatRoi(ind.value);
  if (ind.id === "transforma_solutions" || ind.id === "lmp_total_proposals") {
    return formatCount(ind.value);
  }
  return formatDashboardMetricValue(ind.value, goalFieldsOf(ind));
}

function scopeLabelOf(ind: OverviewIndicator): string {
  const scope = (ind.scope ?? "").trim();
  if (!scope || scope === "consolidado") return "Consolidado";
  return formatOperationalUnitCode(scope, scope);
}

function periodLabelOf(ind: OverviewIndicator): string {
  if (!ind.start_date || !ind.end_date) return "Período oficial";
  const fmt = (iso: string) => {
    const [y, m, d] = iso.split("-");
    return `${d}/${m}/${y}`;
  };
  return `${fmt(ind.start_date)} – ${fmt(ind.end_date)}`;
}

const STATE_MESSAGES: Record<
  Exclude<OverviewCardState, "available">,
  string
> = {
  empty: "Sem dados oficiais no recorte selecionado.",
  unavailable: "Indicador indisponível no momento — tente atualizar.",
  forbidden: "Você não tem acesso a este indicador no momento.",
};

export function buildOverviewCards(
  overview: OverviewResponse,
): OverviewKpiCardVm[] {
  return overview.indicators.map((ind) => {
    if (ind.availability !== "available") {
      return {
        id: ind.id,
        family: ind.family,
        title: ind.label,
        titleHint: TITLE_HINTS[ind.id],
        availability: ind.availability,
        value: "—",
        contextLabel: periodLabelOf(ind),
        stateMessage: ind.message ?? STATE_MESSAGES[ind.availability],
      };
    }

    const goals = goalFieldsOf(ind);
    const contextLabel = `${scopeLabelOf(ind)} · ${periodLabelOf(ind)}`;
    const presentation = buildKpiGoalPresentation(
      CONTEXT_FALLBACK[ind.id] ?? contextLabel,
      goals,
      (value) => formatDashboardMetricValue(value, goals),
      {
        realizedValue: ind.value,
        dateStart: ind.start_date,
        dateEnd: ind.end_date,
        iddScoreLabel: resolveIndicatorIddScoreLabelFromSi(ind.idd),
        showGoal: ind.has_goal === true || ind.goal_value != null,
      },
    );

    return {
      id: ind.id,
      family: ind.family,
      title: ind.label,
      titleHint: TITLE_HINTS[ind.id],
      availability: "available",
      value: formatValue(ind),
      ...presentation,
      contextLabel,
    };
  });
}
