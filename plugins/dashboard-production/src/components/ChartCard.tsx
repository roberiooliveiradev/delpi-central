import { useId, type ReactNode } from "react";

import { HelpTooltip } from "@delpi/plugin-ui";

type ChartCardProps = {
  title: string;
  titleHint?: string;
  children: ReactNode;
  hint?: string;
};

export function ChartCard({ title, titleHint, children, hint }: ChartCardProps) {
  const titleId = useId();

  return (
    <section
      className="dp-card dp-chart-card"
      aria-labelledby={titleId}
      role="region"
    >
      <div className="dp-chart-card__header">
        <h2 id={titleId} className="dp-chart-card__title">
          {title}
          {titleHint ? (
            <HelpTooltip
              content={titleHint}
              ariaLabel={`Ajuda: ${title}`}
              className="dp-chart-card__title-help"
            />
          ) : null}
        </h2>
        {hint ? (
          <p className="dp-chart-card__hint" id={`${titleId}-hint`}>
            {hint}
          </p>
        ) : null}
      </div>
      <div
        className="dp-chart-card__body"
        aria-describedby={hint ? `${titleId}-hint` : undefined}
      >
        {children}
      </div>
    </section>
  );
}
