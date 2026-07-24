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

/**
 * Header no estilo AppHeader de inspeções-entrada:
 * logo + eyebrow + título + subtítulo + ações + barra de marca.
 */
export function LnfPageHeader({
  title,
  subtitle,
  eyebrow = "DELPI · Lançamento Fiscal",
  actions,
  meta,
}: Props) {
  return (
    <header className="lnf-page-header">
      <div className="lnf-page-header__shell lnf-card">
        <div className="lnf-page-header__main">
          <div className="lnf-page-header__brand">
            <img
              className="lnf-page-header__logo"
              src={DELPI_LOGO_URL}
              alt="DELPI Conexões Elétricas"
            />
            <div className="lnf-page-header__titles">
              <p className="lnf-page-header__eyebrow">{eyebrow}</p>
              <div className="lnf-page-header__title-row">
                <h1>{title}</h1>
              </div>
              {subtitle ? (
                <p className="lnf-page-header__subtitle">{subtitle}</p>
              ) : null}
            </div>
          </div>

          {(actions || meta) && (
            <div className="lnf-page-header__meta">
              {meta ? <p className="lnf-page-header__updated">{meta}</p> : null}
              {actions}
            </div>
          )}
        </div>

        <div className="lnf-page-header__brand-bar" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
    </header>
  );
}
