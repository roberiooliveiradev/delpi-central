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
  const cardClass = ["lmps-card", "lmps-detail-card", className].filter(Boolean).join(" ");

  return (
    <section className={cardClass}>
      <header className="lmps-detail-card__header">
        {icon ? <div className="lmps-detail-card__icon">{icon}</div> : null}
        <div>
          <h2>{title}</h2>
          {hint ? <p>{hint}</p> : null}
        </div>
      </header>
      {children}
    </section>
  );
}
