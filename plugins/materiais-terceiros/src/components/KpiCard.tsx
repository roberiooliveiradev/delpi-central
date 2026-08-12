import { createSimpleKpiCard, type DashboardSimpleKpiCardProps } from "@delpi/plugin-ui/index";

export const KpiCard = createSimpleKpiCard("mt", { withBody: true });

export type KpiCardProps = DashboardSimpleKpiCardProps;
