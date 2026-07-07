import type { ReactNode } from "react";

import { TitleWithHelp } from "./TitleWithHelp";

type SectionCardProps = {
  title: string;
  subtitle?: string;
  hint?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export function SectionCard({ title, subtitle, hint, children, actions, className }: SectionCardProps) {
  return (
    <section className={`pac-card pac-section-card${className ? ` ${className}` : ""}`}>
      <div className="pac-section-card__header">
        <div>
          <h2 className="pac-section-title">
            <TitleWithHelp title={title} hint={hint} />
          </h2>
          {subtitle ? <p className="pac-muted pac-section-subtitle">{subtitle}</p> : null}
        </div>
        {actions ? <div className="pac-section-card__actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}
