import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export function SectionCard({ title, subtitle, children, actions, className }: SectionCardProps) {
  return (
    <section className={`pac-card pac-section-card${className ? ` ${className}` : ""}`}>
      <div className="pac-section-card__header">
        <div>
          <h2 className="pac-section-title">{title}</h2>
          {subtitle ? <p className="pac-muted pac-section-subtitle">{subtitle}</p> : null}
        </div>
        {actions ? <div className="pac-section-card__actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}
