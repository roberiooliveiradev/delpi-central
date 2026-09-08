import {
  createDashboardKpiCard,
  type DashboardKpiCardProps,
  type KpiCardLabels,
} from "@delpi/plugin-ui/index";

const LABELS = {
  goalPrefix: "Meta",
  iddScorePrefix: "Nota IDD",
  badgesStatus: "Escopo e desempenho em relação à meta",
} satisfies KpiCardLabels;

export const SuppliesKpiCard = createDashboardKpiCard({ prefix: "sp", labels: LABELS });

export type SuppliesKpiCardProps = DashboardKpiCardProps;
