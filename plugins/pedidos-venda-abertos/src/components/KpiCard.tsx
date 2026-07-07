import type { ReactNode } from "react";

import { createSimpleKpiCard, type DashboardSimpleKpiCardProps } from "@delpi/plugin-ui";

const SimpleKpiCard = createSimpleKpiCard("pva", {
  withBody: true,
  withSubtitle: true,
  layout: "iconEnd",
});

export type KpiCardProps = DashboardSimpleKpiCardProps & {
  icon: ReactNode;
};

export function KpiCard(props: KpiCardProps) {
  return <SimpleKpiCard {...props} />;
}
