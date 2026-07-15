import { createSimpleKpiCard, type DashboardSimpleKpiCardProps } from "@delpi/plugin-ui/index";

export const KpiCard = createSimpleKpiCard("sm", {
  withBody: true,
  defaultValueTag: "p",
});

export type KpiCardProps = DashboardSimpleKpiCardProps;
