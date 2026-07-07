import { useId, type ReactNode } from "react";

import { HelpTooltip } from "@delpi/plugin-ui";

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
      className={["dh-card", "dh-chart-card", className].filter(Boolean).join(" ")}
      aria-labelledby={titleId}
      role="region"
    >
      <div className="dh-chart-card__header">
        <div className="dh-chart-card__heading">
          <h2 id={titleId} className="dh-chart-card__title">
            {title}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${title}`}
                className="dh-chart-card__title-help"
              />
            ) : null}
          </h2>
          {hint ? (
            <p className="dh-chart-card__hint" id={`${titleId}-hint`}>
              {hint}
            </p>
          ) : null}
        </div>
        {headerActions ? (
          <div className="dh-chart-card__actions dh-no-print">{headerActions}</div>
        ) : null}
      </div>
      <div
        className="dh-chart-card__body"
        aria-describedby={hint ? `${titleId}-hint` : undefined}
      >
        {children}
      </div>
    </section>
  );
}
