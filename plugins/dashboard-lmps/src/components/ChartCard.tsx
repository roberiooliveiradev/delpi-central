import type { ReactNode } from "react";

type ChartCardProps = {
  title: string;
  children: ReactNode;
};

export function ChartCard({ title, children }: ChartCardProps) {
  return (
    <section className="lmps-card lmps-chart-card">
      <div className="lmps-card-header">
        <h3>{title}</h3>
      </div>
      <div className="lmps-card-body">{children}</div>
    </section>
  );
}