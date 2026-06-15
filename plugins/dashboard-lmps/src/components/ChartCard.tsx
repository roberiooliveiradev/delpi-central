import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

type ChartCardProps = {
  title: string;
  titleHint?: string;
  children: ReactNode;
};

export function ChartCard({ title, titleHint, children }: ChartCardProps) {
  return (
    <section className="lmps-card lmps-chart-card">
      <div className="lmps-card-header">
        <h3>
          {title}
          {titleHint ? (
            <HelpTooltip
              content={titleHint}
              ariaLabel={`Ajuda: ${title}`}
              className="lmps-chart-card__title-help"
            />
          ) : null}
        </h3>
      </div>
      <div className="lmps-card-body">{children}</div>
    </section>
  );
}
