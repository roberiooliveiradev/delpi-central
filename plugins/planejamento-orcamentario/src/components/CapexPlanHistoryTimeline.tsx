import type { CapexPlanHistoryEntry } from "../types/budgetPlanning";
import {
  formatDateTimeBr,
  planHistoryActionLabel,
  planStatusLabel,
} from "../utils/capexPlans";
import { PlanHistoryTimeline } from "./PlanHistoryTimeline";

type CapexPlanHistoryTimelineProps = {
  items: CapexPlanHistoryEntry[];
  emptyMessage?: string;
};

export function CapexPlanHistoryTimeline({
  items,
  emptyMessage,
}: CapexPlanHistoryTimelineProps) {
  return (
    <PlanHistoryTimeline
      items={items}
      emptyMessage={emptyMessage}
      actionLabel={planHistoryActionLabel}
      statusLabel={planStatusLabel}
      formatDateTime={formatDateTimeBr}
    />
  );
}
