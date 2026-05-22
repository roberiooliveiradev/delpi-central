import { useId, type ReactNode } from "react";

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
  toolbar?: ReactNode;
};

export function ChartCard({ title, children, hint, toolbar }: ChartCardProps) {
  const titleId = useId();

  return (
    <section className="ds-card ds-chart-card" aria-labelledby={titleId} role="region">
      <div className="ds-chart-card__header">
        <div className="ds-chart-card__header-main">
          <h2 id={titleId} className="ds-chart-card__title">
            {title}
          </h2>
          {hint ? (
            <p className="ds-chart-card__hint" id={`${titleId}-hint`}>
              {hint}
            </p>
          ) : null}
        </div>
        {toolbar ? <div className="ds-chart-card__toolbar">{toolbar}</div> : null}
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
