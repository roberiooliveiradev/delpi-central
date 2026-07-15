import { createSimpleKpiCard, type DashboardSimpleKpiCardProps } from "@delpi/plugin-ui/index";

export const KpiCard = createSimpleKpiCard("fi", { withBody: true, withSubtitle: true });

export type KpiCardProps = DashboardSimpleKpiCardProps;
