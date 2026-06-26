import { useId, type ReactNode } from "react";

import { TitleWithHelp } from "./HelpTooltip";

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
};

export function ChartCard({ title, children, hint }: ChartCardProps) {
  const titleId = useId();

  return (
    <section className="pac-card pac-chart-card" aria-labelledby={titleId} role="region">
      <div className="pac-chart-card__header">
        <h2 id={titleId} className="pac-chart-card__title">
          <TitleWithHelp title={title} hint={hint} />
        </h2>
      </div>
      <div className="pac-chart-card__body">{children}</div>
    </section>
  );
}
