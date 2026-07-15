import {
  createDashboardKpiCard,
  type DashboardKpiCardProps,
  type KpiCardLabels,
} from "@delpi/plugin-ui/index";

const LABELS = {
  goalPrefix: "Meta",
  iddScorePrefix: "Nota IDD",
  badgesStatus: "Indicadores do KPI",
} satisfies KpiCardLabels;

export const KpiCard = createDashboardKpiCard({ prefix: "ip", labels: LABELS });

export type KpiCardProps = DashboardKpiCardProps;
