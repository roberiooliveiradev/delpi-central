import { createSimpleKpiCard, type DashboardSimpleKpiCardProps } from "@delpi/plugin-ui/index";

export const KpiCard = createSimpleKpiCard("fcc", { withBody: true });

export type KpiCardProps = DashboardSimpleKpiCardProps;
