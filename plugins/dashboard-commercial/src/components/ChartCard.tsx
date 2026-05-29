import { useId, type ReactNode } from "react";

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
  className?: string;
};

export function ChartCard({ title, children, hint, className }: ChartCardProps) {
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
