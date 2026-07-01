import type { ActionPlanSummary } from "../types/actionPlan";
import { PLAN_STATUSES } from "../constants/actionPlans";

export type RevisionDiffRow = {
  label: string;
  current: string;
  revision: string;
  changed: boolean;
};

type RevisionDiffPlan = Pick<
  ActionPlanSummary,
  "title" | "status" | "severity" | "product_code" | "customer_name"
> & {
  reported_problem?: string | null;
};

const SNAPSHOT_DIFF_FIELDS: Array<{ key: keyof RevisionDiffPlan; label: string }> = [
  { key: "title", label: "Título" },
  { key: "status", label: "Status" },
  { key: "severity", label: "Severidade" },
  { key: "product_code", label: "Produto" },
  { key: "customer_name", label: "Cliente" },
  { key: "reported_problem", label: "Problema relatado" },
];

function formatSnapshotValue(key: string, value: unknown): string {
  if (value == null || value === "") {
    return "—";
  }
  if (key === "status") {
    const match = PLAN_STATUSES.find((item) => item.value === value);
    return match?.label ?? String(value);
  }
  return String(value);
}

export function buildRevisionPlanDiff(
  current: RevisionDiffPlan,
  snapshotPlan: Record<string, unknown> | null | undefined,
): RevisionDiffRow[] {
  const snapshot = snapshotPlan ?? {};
  return SNAPSHOT_DIFF_FIELDS.map(({ key, label }) => {
    const currentValue = formatSnapshotValue(key, current[key]);
    const revisionValue = formatSnapshotValue(key, snapshot[key as string]);
    return {
      label,
      current: currentValue,
      revision: revisionValue,
      changed: currentValue !== revisionValue,
    };
  }).filter((row) => row.changed);
}
