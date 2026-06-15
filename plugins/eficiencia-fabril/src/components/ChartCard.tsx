import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

type ChartCardProps = {
  title: string;
  titleHint?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function ChartCard({ title, titleHint, subtitle, actions, children }: ChartCardProps) {
  return (
    <article className="ef-chart-card">
      <header className="ef-chart-card__header">
        <div className="ef-chart-card__header-row">
          <h2>
            {title}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${title}`}
                className="ef-chart-card__title-help"
              />
            ) : null}
          </h2>
          {actions ? <div className="ef-chart-card__actions">{actions}</div> : null}
        </div>
        {subtitle ? <p className="ef-chart-card__subtitle">{subtitle}</p> : null}
      </header>
      <div className="ef-chart-card__body">{children}</div>
    </article>
  );
}
