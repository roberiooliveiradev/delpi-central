import { RefreshCw } from "lucide-react";

import { branchLabel } from "../utils/safetyStockStatus";

type PageHeaderProps = {
  branch: string;
  onRefresh: () => void;
  refreshing?: boolean;
};

const DELPI_LOGO_URL =
  typeof window !== "undefined" ? `${window.location.origin}/logoDelpi.svg` : "/logoDelpi.svg";

export function PageHeader({ branch, onRefresh, refreshing = false }: PageHeaderProps) {
  return (
    <header className="ess-page-header">
      <div className="ess-page-header__shell ess-card delpi-ui-card">
        <div className="ess-page-header__main">
          <div className="ess-page-header__brand">
            <img
              className="ess-page-header__logo"
              src={DELPI_LOGO_URL}
              alt="DELPI Conexões Elétricas"
            />
            <div className="ess-page-header__titles">
              <p className="ess-page-header__eyebrow">DELPI · Suprimentos</p>
              <div className="ess-page-header__title-row">
                <h1>Estoque de Segurança</h1>
                {branch ? <span className="ess-branch-badge">{branchLabel(branch)}</span> : null}
              </div>
              <p className="ess-page-header__subtitle">
                Acompanhe matérias-primas abaixo do estoque de segurança e o saldo disponível.
              </p>
            </div>
          </div>

          <button
            type="button"
            className="ess-btn ess-btn--primary ess-page-header__refresh"
            onClick={onRefresh}
            disabled={refreshing}
          >
            <RefreshCw
              size={16}
              aria-hidden="true"
              className={refreshing ? "ess-spin" : undefined}
            />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </button>
        </div>

        <div className="ess-page-header__brand-bar" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
    </header>
  );
}
