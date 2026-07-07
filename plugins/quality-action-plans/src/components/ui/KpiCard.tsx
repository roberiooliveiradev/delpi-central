import type { ReactNode } from "react";

import {
  MetricKpiCard,
  metricKpiCardBemClasses,
  type MetricKpiCardClassNames,
  type MetricKpiCardTone,
} from "@delpi/plugin-ui";

import type { KpiTone } from "../../constants/dashboardKpis";

const PAC_KPI_CLASS_NAMES: MetricKpiCardClassNames = {
  ...metricKpiCardBemClasses("pac"),
  article: "pac-card pac-kpi-card",
  articleTone: (tone) => {
    const pacTone =
      tone === "negative"
        ? "danger"
        : tone === "positive"
          ? "success"
          : tone === "warning"
            ? "warning"
            : "";
    return pacTone
      ? `pac-card pac-kpi-card pac-kpi-card--${pacTone}`
      : "pac-card pac-kpi-card";
  },
  header: "pac-kpi-card__header",
  label: "pac-kpi-card__label",
  value: "pac-kpi-card__value",
  icon: "pac-kpi-card__icon",
};

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
    <MetricKpiCard
      label={label}
      titleHint={hint}
      value={loading ? "…" : String(value)}
      icon={icon}
      tone={toMetricTone(tone)}
      classNames={PAC_KPI_CLASS_NAMES}
    />
  );
}
