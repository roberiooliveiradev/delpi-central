import { useId, type ReactNode } from "react";

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
  className?: string;
  headerActions?: ReactNode;
};

export function ChartCard({
  title,
  children,
  hint,
  className,
  headerActions,
}: ChartCardProps) {
  const titleId = useId();

  return (
    <section
      className={["fcc-card", "fcc-chart-card", className].filter(Boolean).join(" ")}
      aria-labelledby={titleId}
    >
      <header className="fcc-chart-card__header">
        <div className="fcc-chart-card__heading">
          <h2 id={titleId} className="fcc-chart-card__title">
            {title}
          </h2>
          {hint ? <p className="fcc-chart-card__hint">{hint}</p> : null}
        </div>
        {headerActions ? <div className="fcc-chart-card__actions">{headerActions}</div> : null}
      </header>
      <div className="fcc-chart-card__body">{children}</div>
    </section>
  );
}
