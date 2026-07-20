import { createSimpleKpiCard, type DashboardSimpleKpiCardProps } from "@delpi/plugin-ui/index";

export const KpiCard = createSimpleKpiCard("ess", {
  withBody: true,
  withSubtitle: true,
});

export type KpiCardProps = DashboardSimpleKpiCardProps;
