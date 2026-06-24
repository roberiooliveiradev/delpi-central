import { useId, type ReactNode } from "react";

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
          {title}
        </h2>
        {hint ? <p className="pac-chart-card__hint">{hint}</p> : null}
      </div>
      <div className="pac-chart-card__body">{children}</div>
    </section>
  );
}
