import type { ReactNode } from "react";

import { createMetricKpiCard, type DashboardMetricKpiCardProps } from "@delpi/plugin-ui";

const MetricKpiCardBase = createMetricKpiCard("ef");

export type KpiCardProps = DashboardMetricKpiCardProps & {
  icon?: ReactNode;
};

export function KpiCard(props: KpiCardProps) {
  return <MetricKpiCardBase {...props} />;
}
