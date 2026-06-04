import type { ReactNode } from "react";

type AdminKpiCardProps = {
  title: string;
  value: ReactNode;
  hint?: string;
  wide?: boolean;
  children?: ReactNode;
};

export function AdminKpiCard({ title, value, hint, wide = false, children }: AdminKpiCardProps) {
  return (
    <article className={wide ? "mdc-admin-kpi-card mdc-admin-kpi-card--wide" : "mdc-admin-kpi-card"}>
      <h3>{title}</h3>
      <strong>{value}</strong>
      {hint ? <p>{hint}</p> : null}
      {children}
    </article>
  );
}

export function AdminKpiGrid({ children }: { children: ReactNode }) {
  return <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">{children}</div>;
}
