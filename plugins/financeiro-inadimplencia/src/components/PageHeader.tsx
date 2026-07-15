import { RefreshCw } from "lucide-react";

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  periodLabel?: string;
  updatedAt?: Date | null;
  refreshing?: boolean;
  onRefresh?: () => void;
};

const DELPI_LOGO_URL =
  typeof window !== "undefined" ? `${window.location.origin}/logoDelpi.svg` : "/logoDelpi.svg";

function formatUpdatedTime(date: Date): string {
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

export function PageHeader({
  title,
  subtitle,
  eyebrow = "DELPI · Financeiro",
  periodLabel,
  updatedAt = null,
  refreshing = false,
  onRefresh,
}: PageHeaderProps) {
  return (
    <header className="fi-page-header">
      <div className="fi-page-header__shell fi-card">
        <div className="fi-page-header__main">
          <div className="fi-page-header__brand">
            <img
              className="fi-page-header__logo"
              src={DELPI_LOGO_URL}
              alt="DELPI Conexões Elétricas"
            />
            <div className="fi-page-header__titles">
              <p className="fi-page-header__eyebrow">{eyebrow}</p>
              <div className="fi-page-header__title-row">
                <h1>{title}</h1>
                {periodLabel ? (
                  <span className="fi-period-badge" title="Período aplicado">
                    {periodLabel}
                  </span>
                ) : null}
              </div>
              {subtitle ? <p className="fi-page-header__subtitle">{subtitle}</p> : null}
            </div>
          </div>

          <div className="fi-page-header__meta">
            {updatedAt ? (
              <p className="fi-page-header__updated">
                Atualizado às {formatUpdatedTime(updatedAt)}
              </p>
            ) : null}
            {onRefresh ? (
              <button
                type="button"
                className="fi-btn fi-btn--primary"
                onClick={onRefresh}
                disabled={refreshing}
              >
                <RefreshCw
                  size={16}
                  aria-hidden="true"
                  className={refreshing ? "fi-spin" : undefined}
                />
                {refreshing ? "Atualizando…" : "Atualizar"}
              </button>
            ) : null}
          </div>
        </div>

        <div className="fi-page-header__brand-bar" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
    </header>
  );
}
