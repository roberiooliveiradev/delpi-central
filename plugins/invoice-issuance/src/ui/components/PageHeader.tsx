import type { ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  actions?: ReactNode;
  meta?: ReactNode;
};

const DELPI_LOGO_URL =
  typeof window !== "undefined"
    ? `${window.location.origin}/logoDelpi.svg`
    : "/logoDelpi.svg";

export function PageHeader({
  title,
  subtitle,
  eyebrow = "DELPI · Faturamento",
  actions,
  meta,
}: Props) {
  return (
    <header className="ii-page-header">
      <div className="ii-page-header__shell ii-card">
        <div className="ii-page-header__main">
          <div className="ii-page-header__brand">
            <img
              className="ii-page-header__logo"
              src={DELPI_LOGO_URL}
              alt="DELPI Conexões Elétricas"
            />
            <div className="ii-page-header__titles">
              <p className="ii-page-header__eyebrow">{eyebrow}</p>
              <div className="ii-page-header__title-row">
                <h1>{title}</h1>
              </div>
              {subtitle ? (
                <p className="ii-page-header__subtitle">{subtitle}</p>
              ) : null}
            </div>
          </div>

          {(actions || meta) && (
            <div className="ii-page-header__meta">
              {meta ? <p className="ii-page-header__updated">{meta}</p> : null}
              {actions}
            </div>
          )}
        </div>

        <div className="ii-page-header__brand-bar" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
    </header>
  );
}
