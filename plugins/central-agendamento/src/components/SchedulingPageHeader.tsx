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
        <div>
          <p className="ca-hero__eyebrow">{eyebrow}</p>
          <h1 className="ca-hero__title">{title}</h1>
          {subtitle ? <p className="ca-hero__subtitle">{subtitle}</p> : null}
        </div>
        {actions ? <div className="ca-hero__actions">{actions}</div> : null}
      </div>
    </header>
  );
}
