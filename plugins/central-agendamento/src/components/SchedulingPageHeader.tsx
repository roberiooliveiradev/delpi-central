import { CalendarDays } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  eyebrow: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
};

export function SchedulingPageHeader({ eyebrow, title, subtitle, actions }: Props) {
  return (
    <header className="ca-hero">
      <div className="ca-hero__glow" aria-hidden />
      <div className="ca-hero__inner">
        <div className="ca-hero__brand">
          <div className="ca-header__icon" aria-hidden="true">
            <CalendarDays size={28} strokeWidth={1.75} />
          </div>
          <div>
            <p className="ca-hero__eyebrow">{eyebrow}</p>
            <h1 className="ca-hero__title">{title}</h1>
            {subtitle ? <p className="ca-hero__subtitle">{subtitle}</p> : null}
          </div>
        </div>
        {actions ? <div className="ca-hero__actions">{actions}</div> : null}
      </div>
    </header>
  );
}
