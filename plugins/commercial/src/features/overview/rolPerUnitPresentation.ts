import type { RolTargetData } from "../../types/analytics";
import { formatOperationalUnitCode } from "../analytics/utils/analyticsBranchFilters";
import type { PeriodKindChip } from "../analytics/utils/periodPreset";
import type { GoalPerformanceBadge, KpiGoalPresentation } from "./goalDisplay";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
  resolveConsolidatedIddScoreLabel,
  resolveGoalPerformanceBadge,
} from "./goalDisplay";

export const BRANCH_GOALS_FILTER_HINT =
  "Metas cadastradas apenas por unidade (Santa Catarina e Espírito Santo). Selecione uma unidade no filtro.";

export type RolPerUnitKpiView = KpiGoalPresentation & {
  valueVariant: "default" | "per-unit";
  value: string;
  goalPerformanceBadges: GoalPerformanceBadge[];
  goalPrefix: string | null;
  periodKindBadge: string | null;
};

function resolveConsolidatedRolValue(
  filial01: RolTargetData | null,
  filial02: RolTargetData | null,
): number | null {
  const values = [filial01?.rol, filial02?.rol].filter(
    (value): value is number => value != null && !Number.isNaN(value),
  );
  if (values.length === 0) {
    return null;
  }
  return values.reduce((sum, value) => sum + value, 0);
}

function resolveBranchGoalsFilterHint(
  filial01: RolTargetData | null,
  filial02: RolTargetData | null,
): string {
  return (
    filial01?.goal_scope_hint?.trim() ||
    filial02?.goal_scope_hint?.trim() ||
    BRANCH_GOALS_FILTER_HINT
  );
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
      const badge = data ? resolveGoalPerformanceBadge(data.rol, data) : null;
      if (!badge) {
        return null;
      }
      if (branch) {
        return badge;
      }
      return {
        ...badge,
        statusLabel: `${formatOperationalUnitCode(code, code)}: ${badge.statusLabel}`,
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
  options?: {
    periodKindBadge?: PeriodKindChip | null;
    dateStart?: string | null;
    dateEnd?: string | null;
  },
): RolPerUnitKpiView {
  const branch = (activeBranch ?? "").trim();
  const periodKindBadge = options?.periodKindBadge ?? null;

  if (branch === "01" || branch === "02") {
    const data = branch === "01" ? filial01 : filial02;
    const single = buildKpiGoalPresentation(contextLabel, data, undefined, {
      realizedValue: data?.rol,
      dateStart: options?.dateStart,
      dateEnd: options?.dateEnd,
    });
    return {
      ...single,
      value: data?.rol != null ? formatDashboardMetricValue(data.rol, data) : "—",
      valueVariant: "per-unit",
      goalPerformanceBadge: null,
      goalPerformanceBadges: resolvePerUnitPerformanceBadges(
        filial01,
        filial02,
        activeBranch,
      ),
      periodKindBadge,
    };
  }

  const consolidatedRol = resolveConsolidatedRolValue(filial01, filial02);

  return {
    contextLabel,
    value: consolidatedRol != null ? formatCurrency(consolidatedRol) : "—",
    valueVariant: "default",
    goalLabel: null,
    goalPrefix: null,
    goalHint: null,
    monthlyGoalLabel: null,
    monthlyGoalPrefix: null,
    monthlyGoalHint: null,
    goalScopeBadge: null,
    goalScopeHint: resolveBranchGoalsFilterHint(filial01, filial02),
    goalPerformanceBadge: null,
    goalPerformanceBadges: [],
    iddScoreLabel: resolveConsolidatedIddScoreLabel([
      { realized: filial01?.rol, goal: filial01 },
      { realized: filial02?.rol, goal: filial02 },
    ]),
    periodKindBadge,
  };
}
