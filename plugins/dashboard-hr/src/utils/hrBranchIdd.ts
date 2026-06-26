import type { HrBranchMetrics, HrSnapshot } from "../types/hr";
import type { DashboardGoalFields, PerBranchMetricSlices } from "./goalDisplay";

type HrGoalMetricKey = keyof NonNullable<HrSnapshot["goals_by_metric"]>;

export type HrBranchGoalSnapshots = {
  filial01: HrSnapshot | null;
  filial02: HrSnapshot | null;
};

export function buildHrMetricIddSlices(
  snapshot: HrSnapshot | null,
  goalSnapshots: HrBranchGoalSnapshots | null,
  goalMetricKey: HrGoalMetricKey,
  branchField: keyof Pick<
    HrBranchMetrics,
    | "absenteeism_pct"
    | "turnover_pct"
    | "training_hours_per_collaborator"
    | "active_pdi_count"
    | "performance_reviews_completion_pct"
  >,
): PerBranchMetricSlices | null {
  if (!goalSnapshots) {
    return null;
  }

  const branchMetrics = snapshot?.branches ?? [];
  const realizedFor = (code: "01" | "02") => {
    const value = branchMetrics.find((item) => item.branch_code === code)?.[
      branchField
    ];
    return typeof value === "number" ? value : null;
  };

  return {
    filial01: {
      realized: realizedFor("01"),
      goal: goalSnapshots.filial01?.goals_by_metric?.[goalMetricKey] ?? null,
    },
    filial02: {
      realized: realizedFor("02"),
      goal: goalSnapshots.filial02?.goals_by_metric?.[goalMetricKey] ?? null,
    },
  };
}

export function buildHrSatisfactionIddSlices(
  snapshot: HrSnapshot | null,
  goalSnapshots: HrBranchGoalSnapshots | null,
): PerBranchMetricSlices | null {
  if (!goalSnapshots) {
    return null;
  }

  return {
    filial01: {
      realized: snapshot?.internal_satisfaction_pct ?? null,
      goal:
        goalSnapshots.filial01?.goals_by_metric?.internal_satisfaction_pct ??
        null,
    },
    filial02: {
      realized: snapshot?.internal_satisfaction_pct ?? null,
      goal:
        goalSnapshots.filial02?.goals_by_metric?.internal_satisfaction_pct ??
        null,
    },
  };
}

export function pickHrGoalBlock(
  goal: DashboardGoalFields | null | undefined,
): DashboardGoalFields | null | undefined {
  return goal ?? null;
}
