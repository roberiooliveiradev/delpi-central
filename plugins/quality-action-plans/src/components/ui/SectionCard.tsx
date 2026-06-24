import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export function SectionCard({ title, children, actions, className }: SectionCardProps) {
  return (
    <section className={`pac-card pac-section-card${className ? ` ${className}` : ""}`}>
      <div className="pac-section-card__header">
        <h2 className="pac-section-title">{title}</h2>
        {actions ? <div className="pac-section-card__actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}
