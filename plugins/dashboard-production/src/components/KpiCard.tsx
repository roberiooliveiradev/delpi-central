import {
  createDashboardKpiCard,
  type DashboardKpiCardProps,
  type KpiCardLabels,
} from "@delpi/plugin-ui/index";

export type { GoalPerformanceBadge, GoalScopeBadge } from "../utils/goalDisplay";

const LABELS = {
  goalPrefix: "Meta",
  iddScorePrefix: "Nota IDD",
  badgesStatus: "Escopo e desempenho em relação à meta",
} satisfies KpiCardLabels;

export const KpiCard = createDashboardKpiCard({ prefix: "dp", labels: LABELS });

export type KpiCardProps = DashboardKpiCardProps;
