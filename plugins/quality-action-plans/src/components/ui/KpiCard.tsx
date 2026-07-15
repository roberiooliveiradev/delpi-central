import type { ReactNode } from "react";

import { createMetricKpiCard, type MetricKpiCardTone } from "@delpi/plugin-ui/index";

import type { KpiTone } from "../../constants/dashboardKpis";

const MetricKpi = createMetricKpiCard("pac");

function toMetricTone(tone: KpiTone): MetricKpiCardTone {
  if (tone === "danger") return "negative";
  if (tone === "success") return "positive";
  if (tone === "warning") return "warning";
  return "default";
}

type KpiCardProps = {
  label: string;
  value: number | string;
  tone?: KpiTone;
  icon: ReactNode;
  hint?: string;
  loading?: boolean;
};

export function KpiCard({ label, value, tone = "default", icon, hint, loading = false }: KpiCardProps) {
  return (
    <MetricKpi
      label={label}
      titleHint={hint}
      value={loading ? "…" : String(value)}
      icon={icon}
      tone={toMetricTone(tone)}
    />
  );
}
