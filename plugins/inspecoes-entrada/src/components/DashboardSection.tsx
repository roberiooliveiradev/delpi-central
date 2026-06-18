import type { ReactNode } from "react";

type DashboardSectionVariant = "default" | "analytics" | "attention" | "preview";

type DashboardSectionProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
  variant?: DashboardSectionVariant;
};

export function DashboardSection({
  title,
  subtitle,
  children,
  action,
  variant = "default",
}: DashboardSectionProps) {
  return (
    <section className={`ie-card ie-dashboard-section ie-dashboard-section--${variant}`}>
      <header className="ie-dashboard-section__header">
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {action ? <div className="ie-dashboard-section__action">{action}</div> : null}
      </header>
      <div className="ie-dashboard-section__body">{children}</div>
    </section>
  );
}
