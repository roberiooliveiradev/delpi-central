import { useId, type ReactNode } from "react";

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
  variant?: "default" | "featured";
  actions?: ReactNode;
};

export function ChartCard({
  title,
  children,
  hint,
  variant = "default",
  actions,
}: ChartCardProps) {
  const titleId = useId();
  const className = [
    "cr-card",
    "cr-chart-card",
    variant === "featured" ? "cr-chart-card--featured" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={className} aria-labelledby={titleId}>
      <header className="cr-chart-card__header">
        <div className="cr-chart-card__header-row">
          <h2 id={titleId} className="cr-chart-card__title">
            {title}
          </h2>
          {actions ? <div className="cr-chart-card__actions">{actions}</div> : null}
        </div>
        {hint ? <p className="cr-chart-card__hint">{hint}</p> : null}
      </header>
      <div className="cr-chart-card__body">{children}</div>
    </section>
  );
}
