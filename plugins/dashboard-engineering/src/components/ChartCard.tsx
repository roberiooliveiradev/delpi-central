import { useId, type ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

type ChartCardProps = {
  title: string;
  titleHint?: string;
  children: ReactNode;
  hint?: string;
  className?: string;
  headerActions?: ReactNode;
};

export function ChartCard({
  title,
  titleHint,
  children,
  hint,
  className,
  headerActions,
}: ChartCardProps) {
  const titleId = useId();

  return (
    <section
      className={["ds-card", "ds-chart-card", className].filter(Boolean).join(" ")}
      aria-labelledby={titleId}
      role="region"
    >
      <div className="ds-chart-card__header">
        <div className="ds-chart-card__heading">
          <h2 id={titleId} className="ds-chart-card__title">
            {title}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${title}`}
                className="ds-chart-card__title-help"
              />
            ) : null}
          </h2>
          {hint ? (
            <p className="ds-chart-card__hint" id={`${titleId}-hint`}>
              {hint}
            </p>
          ) : null}
        </div>
        {headerActions ? (
          <div className="ds-chart-card__actions ds-no-print">{headerActions}</div>
        ) : null}
      </div>
      <div
        className="ds-chart-card__body"
        aria-describedby={hint ? `${titleId}-hint` : undefined}
      >
        {children}
      </div>
    </section>
  );
}
