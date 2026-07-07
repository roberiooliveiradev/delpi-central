import type { ReactNode } from "react";

import { createSimpleKpiCard, type DashboardSimpleKpiCardProps } from "@delpi/plugin-ui";

export type KpiCardVariant = "default" | "info" | "warning" | "success" | "danger";

const SimpleKpiCard = createSimpleKpiCard("ie", {
  withBody: true,
  withSubtitle: true,
  defaultValueTag: "p",
});

export type KpiCardProps = Omit<DashboardSimpleKpiCardProps, "variant"> & {
  variant?: KpiCardVariant;
  subtitle?: string;
  icon: ReactNode;
};

export function KpiCard({ variant = "default", ...props }: KpiCardProps) {
  return (
    <SimpleKpiCard variant={variant === "default" ? undefined : variant} {...props} />
  );
}
