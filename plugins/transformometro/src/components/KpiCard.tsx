import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

type KpiCardProps = {
  title: string;
  value: string;
  subtitle: string;
  icon: ReactNode;
  loading?: boolean;
  titleHint?: string;
};

export function KpiCard({
  title,
  value,
  subtitle,
  icon,
  loading = false,
  titleHint,
}: KpiCardProps) {
  return (
    <article className="ds-card ds-kpi-card">
      <div className="ds-kpi-header">
        <div>
          <p className="ds-kpi-title">
            {title}
            {titleHint ? (
              <HelpTooltip content={titleHint} ariaLabel={`Ajuda: ${title}`} />
            ) : null}
          </p>
          <h3 className="ds-kpi-value">{loading ? "…" : value}</h3>
          <span className="ds-kpi-subtitle">{subtitle}</span>
        </div>
        <div className="ds-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
