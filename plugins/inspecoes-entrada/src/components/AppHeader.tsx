import { RefreshCw } from "lucide-react";

import { formatBranchUnitLabel } from "../utils/certificateFormat";
import type { InspecoesEntradaTab } from "../utils/tabs";
import { AppTabs } from "./AppTabs";

type AppHeaderProps = {
  branch: string;
  activeTab: InspecoesEntradaTab;
  loading: boolean;
  lastUpdatedAt?: Date | null;
  onTabChange: (tab: InspecoesEntradaTab) => void;
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
    <header className="ie-page-header">
      <div className="ie-page-header__shell ie-card">
        <div className="ie-page-header__main">
          <div className="ie-page-header__brand">
            <img
              className="ie-page-header__logo"
              src={DELPI_LOGO_URL}
              alt="DELPI Conexões Elétricas"
            />
            <div className="ie-page-header__titles">
              <p className="ie-page-header__eyebrow">DELPI · Qualidade</p>
              <div className="ie-page-header__title-row">
                <h1>Inspeções de Entrada</h1>
                <span className="ie-branch-badge">{formatBranchUnitLabel(branch)}</span>
              </div>
              <p className="ie-page-header__subtitle">
                Controle de qualidade no recebimento de materiais
              </p>
            </div>
          </div>

          <div className="ie-page-header__meta">
            {lastUpdatedAt ? (
              <p className="ie-page-header__updated">
                Atualizado às {formatUpdatedAt(lastUpdatedAt)}
              </p>
            ) : null}
            <button
              type="button"
              className="ie-btn ie-btn--primary"
              onClick={onRefresh}
              disabled={loading}
            >
              <RefreshCw size={16} aria-hidden="true" className={loading ? "ie-spin" : undefined} />
              Atualizar
            </button>
          </div>
        </div>

        <div className="ie-page-header__nav">
          <AppTabs activeTab={activeTab} onChange={onTabChange} />
        </div>

        <div className="ie-page-header__brand-bar" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
    </header>
  );
}
