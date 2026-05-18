import type { ReactNode } from "react";

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
};

export function ChartCard({ title, children, hint }: ChartCardProps) {
  return (
    <section className="dq-card dq-chart-card">
      <div className="dq-chart-card__header">
        <h2 className="dq-chart-card__title">{title}</h2>
        {hint ? <p className="dq-chart-card__hint">{hint}</p> : null}
      </div>
      <div className="dq-chart-card__body">{children}</div>
    </section>
  );
}
