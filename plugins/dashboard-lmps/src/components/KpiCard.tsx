import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

type KpiCardProps = {
  title: string;
  titleHint?: string;
  value: string;
  subtitle: string;
  icon: ReactNode;
};

export function KpiCard({ title, titleHint, value, subtitle, icon }: KpiCardProps) {
  return (
    <div className="lmps-card lmps-kpi-card">
      <div className="lmps-kpi-header">
        <div>
          <p className="lmps-kpi-title">
            {title}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${title}`}
                className="lmps-kpi-title__help"
              />
            ) : null}
          </p>
          <h3 className="lmps-kpi-value">{value}</h3>
          <span className="lmps-kpi-subtitle">{subtitle}</span>
        </div>
        <div className="lmps-kpi-icon">{icon}</div>
      </div>
    </div>
  );
}
