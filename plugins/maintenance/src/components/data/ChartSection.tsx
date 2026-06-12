import type { ReactNode } from "react";

type ChartSectionProps = {
  title: string;
  children: ReactNode;
  actions?: ReactNode;
};

export function ChartSection({ title, children, actions }: ChartSectionProps) {
  return (
    <section className="dm-card dm-chart-section">
      <div className="dm-section-header">
        <div className="dm-section-header__title-group">
          <h3 className="dm-section-header__title">{title}</h3>
        </div>
        {actions ? <div className="dm-section-header__meta">{actions}</div> : null}
      </div>
      <div className="dm-chart-wrap">{children}</div>
    </section>
  );
}
