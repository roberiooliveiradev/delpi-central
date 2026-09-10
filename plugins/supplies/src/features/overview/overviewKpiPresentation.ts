import {
  buildKpiGoalPresentation,
  resolveIndicatorIddScoreLabelFromSi,
  type DashboardGoalFields,
  type PerformanceDirection,
} from "@delpi/plugin-ui/index";

import type { OverviewKpiCard } from "../../api/overview";

const KPI_DIRECTION: Record<string, PerformanceDirection> = {
  "KPI-OTD": "higher_is_better",
  "KPI-STOCK-VALUE": "higher_is_better",
  "KPI-TURNOVER": "higher_is_better",
  "KPI-CPV": "lower_is_better",
  "KPI-SAVINGS": "higher_is_better",
  "KPI-SC-OPEN": "lower_is_better",
  "KPI-CRITICAL-MP": "lower_is_better",
};

function formatIsoBr(iso: string): string {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) return iso || "—";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function unitFields(unit: string | null): Pick<
  DashboardGoalFields,
  "value_unit" | "value_prefix" | "value_suffix" | "value_decimals"
> {
  if (unit === "%") {
    return {
      value_unit: "percent",
      value_prefix: "",
      value_suffix: "%",
      value_decimals: 1,
    };
  }
  if (unit === "R$") {
    return {
      value_unit: "currency",
      value_prefix: "R$",
      value_suffix: "",
      value_decimals: 2,
    };
  }
  if (unit === "×") {
    return {
      value_unit: "ratio",
      value_prefix: "",
      value_suffix: "×",
      value_decimals: 2,
    };
  }
  return {
    value_unit: "count",
    value_prefix: "",
    value_suffix: "",
    value_decimals: 0,
  };
}

export type OverviewKpiGoalContext = {
  from: string;
  to: string;
  scopeLabel: string;
  branch?: string;
  consolidated: boolean;
};

function resolveComparable(kpi: OverviewKpiCard): number | null {
  const value = kpi.comparableGoal ?? kpi.meta;
  if (value == null || !Number.isFinite(value) || value <= 0) return null;
  return value;
}

function resolveReference(kpi: OverviewKpiCard): number | null {
  const value = kpi.referenceGoal ?? kpi.goalValue ?? kpi.meta;
  if (value == null || !Number.isFinite(value) || value <= 0) return null;
  return value;
}

function resolveGoalValue(kpi: OverviewKpiCard): number | null {
  const value = kpi.goalValue ?? kpi.referenceGoal ?? kpi.meta;
  if (value == null || !Number.isFinite(value) || value <= 0) return null;
  return value;
}

/** Maps overview KPI + SI triad into kit DashboardGoalFields (Commercial parity). */
export function buildOverviewGoalFields(
  kpi: OverviewKpiCard,
  ctx: OverviewKpiGoalContext,
): DashboardGoalFields | null {
  const comparable = resolveComparable(kpi);
  const reference = resolveReference(kpi);
  const goalValue = resolveGoalValue(kpi);
  if (comparable == null && reference == null && goalValue == null) {
    return null;
  }
  const units = unitFields(kpi.unit);
  const direction =
    (kpi.performanceDirection as PerformanceDirection | null) ??
    KPI_DIRECTION[kpi.id] ??
    "higher_is_better";
  return {
    goal_value: goalValue ?? reference ?? comparable,
    reference_goal: reference ?? goalValue ?? comparable,
    comparable_goal: comparable ?? reference ?? goalValue,
    has_goal: true,
    performance_direction: direction,
    goal_mode: kpi.goalMode ?? "standard",
    goal_scope_branch: ctx.consolidated ? null : ctx.branch ?? null,
    goal_scope_label: ctx.consolidated
      ? "Meta consolidada"
      : undefined,
    scope_type: ctx.consolidated ? "consolidated" : "branch",
    start_date: ctx.from,
    end_date: ctx.to,
    ...units,
  };
}

export function buildOverviewKpiPresentation(
  kpi: OverviewKpiCard,
  ctx: OverviewKpiGoalContext,
) {
  const contextLabel = `${ctx.scopeLabel} · ${formatIsoBr(ctx.from)} - ${formatIsoBr(ctx.to)}`;
  const goal = buildOverviewGoalFields(kpi, ctx);
  const formatComparable = (value: number) => {
    if (kpi.unit === "%") {
      return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
    }
    if (kpi.unit === "R$") {
      return `R$ ${value.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    }
    if (kpi.unit === "×") {
      return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}×`;
    }
    return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
  };

  const iddScoreLabel = resolveIndicatorIddScoreLabelFromSi(kpi.iddScore);

  return buildKpiGoalPresentation(contextLabel, goal, formatComparable, {
    showGoal: goal != null && kpi.status === "available",
    realizedValue: kpi.status === "available" ? kpi.value : null,
    dateStart: ctx.from,
    dateEnd: ctx.to,
    iddScoreLabel,
  });
}
