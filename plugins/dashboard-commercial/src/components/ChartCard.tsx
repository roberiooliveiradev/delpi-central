import { useId, type ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

type ChartCardProps = {
  title: string;
  titleHint?: string;
  children: ReactNode;
  hint?: string;
  className?: string;
};

export function ChartCard({
  title,
  titleHint,
  children,
  hint,
  className,
}: ChartCardProps) {
  const titleId = useId();

  return (
    <section
      className={["dc-card", "dc-chart-card", className].filter(Boolean).join(" ")}
      aria-labelledby={titleId}
      role="region"
    >
      <div className="dc-chart-card__header">
        <h2 id={titleId} className="dc-chart-card__title">
          {title}
          {titleHint ? (
            <HelpTooltip
              content={titleHint}
              ariaLabel={`Ajuda: ${title}`}
              className="dc-chart-card__title-help"
            />
          ) : null}
        </h2>
        {hint ? (
          <p className="dc-chart-card__hint" id={`${titleId}-hint`}>
            {hint}
          </p>
        ) : null}
      </div>
      <div
        className="dc-chart-card__body"
        aria-describedby={hint ? `${titleId}-hint` : undefined}
      >
        {children}
      </div>
    </section>
  );
}
