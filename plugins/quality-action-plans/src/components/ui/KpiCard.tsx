import type { ReactNode } from "react";

import type { KpiTone } from "../../constants/dashboardKpis";
import { TitleWithHelp } from "./HelpTooltip";

type KpiCardProps = {
  label: string;
  value: number | string;
  tone?: KpiTone;
  icon: ReactNode;
  hint?: string;
  loading?: boolean;
};

export function KpiCard({ label, value, tone = "default", icon, hint, loading = false }: KpiCardProps) {
  const toneClass = tone === "default" ? "" : ` pac-kpi-card--${tone}`;

  return (
    <article className={`pac-card pac-kpi-card${toneClass}`}>
      <div className="pac-kpi-card__header">
        <div className="pac-kpi-card__content">
          <p className="pac-kpi-card__label">
            <TitleWithHelp title={label} hint={hint} />
          </p>
          <p className="pac-kpi-card__value">{loading ? "…" : value}</p>
        </div>
        <div className="pac-kpi-card__icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
