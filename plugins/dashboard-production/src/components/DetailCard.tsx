import type { ReactNode } from "react";

type DetailCardProps = {
  title: string;
  hint?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function DetailCard({
  title,
  hint,
  icon,
  children,
  className,
}: DetailCardProps) {
  const cardClass = ["dp-card", "dp-detail-card", className].filter(Boolean).join(" ");

  return (
    <section className={cardClass}>
      <div className="dp-detail-card__header">
        {icon ? <div className="dp-summary-card__icon">{icon}</div> : null}
        <div>
          <h2 className="dp-summary-card__title">{title}</h2>
          {hint ? <p className="dp-summary-card__description">{hint}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}
