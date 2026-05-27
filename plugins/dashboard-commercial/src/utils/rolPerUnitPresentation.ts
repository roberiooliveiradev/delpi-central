import type { RolTargetData } from "../types/commercial";
import type {
  GoalPerformanceBadge,
  GoalScopeBadge,
  KpiGoalPresentation,
} from "./goalDisplay";
import {
  buildKpiGoalPresentation,
  resolveGoalLabel,
  resolveGoalPerformanceBadge,
} from "./goalDisplay";
import { formatPerUnitBranchMetric } from "./perUnitMetricDisplay";

export type RolPerUnitKpiView = KpiGoalPresentation & {
  value: string;
  goalPerformanceBadges: GoalPerformanceBadge[];
};

function pickRolByBranch(
  filial01: RolTargetData | null,
  filial02: RolTargetData | null,
  activeBranch?: string,
): RolTargetData | null {
  const branch = (activeBranch ?? "").trim();
  if (branch === "01") {
    return filial01;
  }
  if (branch === "02") {
    return filial02;
  }
  return filial01 ?? filial02;
}

function formatPerUnitGoalLabel(
  filial01: RolTargetData | null,
  filial02: RolTargetData | null,
  formatComparable: (value: number) => string,
  activeBranch?: string,
): string | null {
  const formatBranchGoal = (
    code: "01" | "02",
    data: RolTargetData | null,
  ): string | null => {
    const label = data ? resolveGoalLabel(data, formatComparable) : null;
    if (!label) {
      return null;
    }
    const branch = (activeBranch ?? "").trim();
    if (branch && branch !== code) {
      return null;
    }
    return branch ? label : `${code}: ${label}`;
  };

  const parts = [
    formatBranchGoal("01", filial01),
    formatBranchGoal("02", filial02),
  ].filter((part): part is string => part != null);

  if (parts.length >= 2) {
    return parts.join(" | ");
  }
  if (parts.length === 1) {
    return parts[0];
  }
  return null;
}

function resolvePerUnitScopeBadge(
  filial01: RolTargetData | null,
  filial02: RolTargetData | null,
  activeBranch?: string,
): GoalScopeBadge | null {
  const branch = (activeBranch ?? "").trim();
  if (branch) {
    const single = buildKpiGoalPresentation("", pickRolByBranch(filial01, filial02, branch));
    return single.goalScopeBadge;
  }

  const hasGoal =
    Boolean(resolveGoalLabel(filial01)) || Boolean(resolveGoalLabel(filial02));
  if (!hasGoal) {
    return null;
  }

  const scopeType = filial01?.scope_type ?? filial02?.scope_type;
  if (scopeType === "per_unit") {
    return { tone: "scope", label: "Meta por unidade" };
  }

  return { tone: "scope", label: "Meta por unidade" };
}

function resolvePerUnitPerformanceBadges(
  filial01: RolTargetData | null,
  filial02: RolTargetData | null,
  activeBranch?: string,
): GoalPerformanceBadge[] {
  const branch = (activeBranch ?? "").trim();
  const entries: Array<{ code: "01" | "02"; data: RolTargetData | null }> = [
    { code: "01", data: filial01 },
    { code: "02", data: filial02 },
  ];

  return entries
    .filter(({ code }) => !branch || branch === code)
    .map(({ code, data }) => {
      const badge = data
        ? resolveGoalPerformanceBadge(data.rol, data)
        : null;
      if (!badge) {
        return null;
      }
      if (branch) {
        return badge;
      }
      return {
        ...badge,
        statusLabel: `${code}: ${badge.statusLabel}`,
      };
    })
    .filter((badge): badge is GoalPerformanceBadge => badge != null);
}

export function buildRolPerUnitKpiView(
  filial01: RolTargetData | null,
  filial02: RolTargetData | null,
  contextLabel: string,
  formatCurrency: (value: number) => string,
  activeBranch?: string,
): RolPerUnitKpiView {
  const branch = (activeBranch ?? "").trim();

  if (branch === "01" || branch === "02") {
    const data = branch === "01" ? filial01 : filial02;
    const single = buildKpiGoalPresentation(contextLabel, data, formatCurrency, {
      realizedValue: data?.rol,
    });
    return {
      ...single,
      value: data?.rol != null ? formatCurrency(data.rol) : "—",
      goalPerformanceBadge: null,
      goalPerformanceBadges: resolvePerUnitPerformanceBadges(
        filial01,
        filial02,
        activeBranch,
      ),
    };
  }

  const goalLabel = formatPerUnitGoalLabel(
    filial01,
    filial02,
    formatCurrency,
    activeBranch,
  );
  const scopeBadge = resolvePerUnitScopeBadge(filial01, filial02, activeBranch);
  const hint =
    scopeBadge?.tone === "info"
      ? scopeBadge.label
      : filial01?.goal_scope_hint?.trim() ||
        filial02?.goal_scope_hint?.trim() ||
        null;

  return {
    contextLabel,
    value: formatPerUnitBranchMetric(
      { "01": filial01?.rol, "02": filial02?.rol },
      formatCurrency,
      activeBranch,
    ),
    goalLabel,
    goalScopeBadge: scopeBadge?.tone === "scope" ? scopeBadge : null,
    goalScopeHint: scopeBadge?.tone === "info" ? scopeBadge.label : hint,
    goalPerformanceBadge: null,
    goalPerformanceBadges: resolvePerUnitPerformanceBadges(
      filial01,
      filial02,
      activeBranch,
    ),
  };
}
