import type { RolTargetData } from "../types/commercial";
import type { GoalPerformanceBadge, KpiGoalPresentation } from "./goalDisplay";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
  resolveGoalPerformanceBadge,
} from "./goalDisplay";
import { formatOperationalUnitCode } from "./operationalUnitLabels";

export type RolPerUnitKpiView = KpiGoalPresentation & {
  valueVariant: "default" | "per-unit";
  value: string;
  goalPerformanceBadges: GoalPerformanceBadge[];
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
    dateStart?: string | null;
    dateEnd?: string | null;
    /** Nota IDD canônica do SI (`indicators[].score`). */
    iddScoreLabel?: string | null;
    /**
     * Payload consolidado (branch vazio) com meta SI já agregada via
     * `branch_value_aggregation` — não somar metas no MFE.
     */
    consolidatedMetric?: RolTargetData | null;
  },
): RolPerUnitKpiView {
  const branch = (activeBranch ?? "").trim();
  const siIddScoreLabel = options?.iddScoreLabel;

  if (branch === "01" || branch === "02") {
    const data = branch === "01" ? filial01 : filial02;
    const single = buildKpiGoalPresentation(contextLabel, data, undefined, {
      realizedValue: data?.rol,
      dateStart: options?.dateStart,
      dateEnd: options?.dateEnd,
      iddScoreLabel: siIddScoreLabel,
    });
    return {
      ...single,
      value:
        data?.rol != null ? formatDashboardMetricValue(data.rol, data) : "—",
      valueVariant: "per-unit",
      goalPerformanceBadge: null,
      goalPerformanceBadges: resolvePerUnitPerformanceBadges(
        filial01,
        filial02,
        activeBranch,
      ),
    };
  }

  const consolidatedMetric = options?.consolidatedMetric ?? null;
  const consolidatedRol =
    consolidatedMetric?.rol != null && !Number.isNaN(consolidatedMetric.rol)
      ? consolidatedMetric.rol
      : resolveConsolidatedRolValue(filial01, filial02);

  // Visão consolidada: a meta vem só do payload SI (branch vazio), já agregado.
  // Não inventar «selecione unidade» a partir das filiais 01/02.
  if (consolidatedMetric != null) {
    const presentation = buildKpiGoalPresentation(
      contextLabel,
      consolidatedMetric,
      undefined,
      {
        realizedValue: consolidatedRol,
        dateStart: options?.dateStart,
        dateEnd: options?.dateEnd,
        iddScoreLabel: siIddScoreLabel,
      },
    );
    return {
      ...presentation,
      value: consolidatedRol != null ? formatCurrency(consolidatedRol) : "—",
      valueVariant: "default",
      goalPerformanceBadges: [],
    };
  }

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
    goalScopeHint: null,
    goalPerformanceBadge: null,
    goalPerformanceBadges: [],
    iddScoreLabel: siIddScoreLabel ?? null,
  };
}
