import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

type KpiCardProps = {
  label: string;
  titleHint?: string;
  value: string;
  hint?: string;
  icon?: ReactNode;
  tone?: "default" | "positive" | "negative" | "warning";
};

export function KpiCard({
  label,
  titleHint,
  value,
  hint,
  icon,
  tone = "default",
}: KpiCardProps) {
  return (
    <article className={`ef-kpi-card ef-kpi-card--${tone}`}>
      <div className="ef-kpi-header">
        <div>
          <p className="ef-kpi-card__label">
            {label}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${label}`}
                className="ef-kpi-card__label-help"
              />
            ) : null}
          </p>
          <strong className="ef-kpi-card__value">{value}</strong>
          {hint ? <p className="ef-kpi-card__hint">{hint}</p> : null}
        </div>
        {icon ? (
          <div className="ef-kpi-icon" aria-hidden="true">
            {icon}
          </div>
        ) : null}
      </div>
    </article>
  );
}
