import type { PersonnelPlanHistoryEntry } from "../types/budgetPlanning";
import {
  formatPersonnelDateTimeBr,
  personnelPlanHistoryActionLabel,
  personnelPlanStatusLabel,
} from "../utils/personnelPlans";
import { PlanHistoryTimeline } from "./PlanHistoryTimeline";

type PersonnelPlanHistoryTimelineProps = {
  items: PersonnelPlanHistoryEntry[];
  emptyMessage?: string;
};

export function PersonnelPlanHistoryTimeline({
  items,
  emptyMessage,
}: PersonnelPlanHistoryTimelineProps) {
  return (
    <PlanHistoryTimeline
      items={items}
      emptyMessage={emptyMessage}
      actionLabel={personnelPlanHistoryActionLabel}
      statusLabel={personnelPlanStatusLabel}
      formatDateTime={formatPersonnelDateTimeBr}
    />
  );
}
