import { RefreshCw } from "lucide-react";

import { branchUnitLabel } from "../constants/branch";
import type { InspecoesProcessoTab } from "../utils/tabs";
import { AppTabs } from "./AppTabs";

type AppHeaderProps = {
  branch: string;
  activeTab: InspecoesProcessoTab;
  loading: boolean;
  lastUpdatedAt?: Date | null;
  onTabChange: (tab: InspecoesProcessoTab) => void;
  onRefresh: () => void;
};

const DELPI_LOGO_URL =
  typeof window !== "undefined" ? `${window.location.origin}/logoDelpi.svg` : "/logoDelpi.svg";

function formatUpdatedAt(date: Date): string {
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

export function AppHeader({
  branch,
  activeTab,
  loading,
  lastUpdatedAt,
  onTabChange,
  onRefresh,
}: AppHeaderProps) {
  return (
    <header className="ip-page-header">
      <div className="ip-page-header__shell ip-card">
        <div className="ip-page-header__main">
          <div className="ip-page-header__brand">
            <img
              className="ip-page-header__logo"
              src={DELPI_LOGO_URL}
              alt="DELPI Conexões Elétricas"
            />
            <div className="ip-page-header__titles">
              <p className="ip-page-header__eyebrow">DELPI · Qualidade</p>
              <div className="ip-page-header__title-row">
                <h1>Inspeções de Processo</h1>
                <span className="ip-branch-badge">{branchUnitLabel(branch)}</span>
              </div>
              <p className="ip-page-header__subtitle">
                Painel operacional de inspeções em processo por filial
              </p>
            </div>
          </div>

          <div className="ip-page-header__meta">
            {lastUpdatedAt ? (
              <p className="ip-page-header__updated">
                Atualizado às {formatUpdatedAt(lastUpdatedAt)}
              </p>
            ) : null}
            <button
              type="button"
              className="ip-btn ip-btn--primary"
              onClick={onRefresh}
              disabled={loading}
            >
              <RefreshCw size={16} aria-hidden="true" className={loading ? "ip-spin" : undefined} />
              Atualizar
            </button>
          </div>
        </div>

        <div className="ip-page-header__nav">
          <AppTabs activeTab={activeTab} onChange={onTabChange} />
        </div>

        <div className="ip-page-header__brand-bar" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
    </header>
  );
}
