import { useId, type ReactNode } from "react";

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
};

export function ChartCard({ title, children, hint }: ChartCardProps) {
  const titleId = useId();

  return (
    <section
      className="dq-card dq-chart-card"
      aria-labelledby={titleId}
      role="region"
    >
      <div className="dq-chart-card__header">
        <h2 id={titleId} className="dq-chart-card__title">
          {title}
        </h2>
        {hint ? (
          <p className="dq-chart-card__hint" id={`${titleId}-hint`}>
            {hint}
          </p>
        ) : null}
      </div>
      <div
        className="dq-chart-card__body"
        aria-describedby={hint ? `${titleId}-hint` : undefined}
      >
        {children}
      </div>
    </section>
  );
}
