import { FilePlus2, RefreshCw } from "lucide-react";

import type { CecRoute } from "../hooks/useCecRouterPath";
import { navigateCec } from "../hooks/useCecRouterPath";
import type { ComiteEticaAccess } from "../security/cecAccess";
import { CecAppTabs, type CecAppTab } from "./CecAppTabs";

export type CecAppHeaderProps = {
  route: CecRoute;
  access: ComiteEticaAccess | null;
  loading?: boolean;
  lastUpdatedAt?: Date | null;
  onRefresh?: () => void;
  showNewMinute?: boolean;
};

const DELPI_LOGO_URL =
  typeof window !== "undefined" ? `${window.location.origin}/logoDelpi.svg` : "/logoDelpi.svg";

function formatUpdatedAt(date: Date): string {
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

export function tabFromRoute(route: CecRoute): CecAppTab {
  switch (route.kind) {
    case "pending":
      return "pending";
    case "members":
      return "members";
    case "mySignature":
      return "signature";
    default:
      return "atas";
  }
}

function pathForTab(tab: CecAppTab): string {
  switch (tab) {
    case "pending":
      return "/apps/comite-etica-conduta/atas/pending";
    case "members":
      return "/apps/comite-etica-conduta/membros";
    case "signature":
      return "/apps/comite-etica-conduta/minha-assinatura";
    case "atas":
    default:
      return "/apps/comite-etica-conduta/atas";
  }
}

export function CecAppHeader({
  route,
  access,
  loading = false,
  lastUpdatedAt = null,
  onRefresh,
  showNewMinute = false,
}: CecAppHeaderProps) {
  const activeTab = tabFromRoute(route);

  return (
    <header className="cec-page-header">
      <div className="cec-page-header__shell cec-card">
        <div className="cec-page-header__main">
          <div className="cec-page-header__brand">
            <img
              className="cec-page-header__logo"
              src={DELPI_LOGO_URL}
              alt="DELPI Conexões Elétricas"
            />
            <div className="cec-page-header__titles">
              <p className="cec-page-header__eyebrow">DELPI · Ética e Conduta</p>
              <div className="cec-page-header__title-row">
                <h1>Comitê de Ética e Conduta</h1>
                <span className="cec-scope-badge">Corporativo</span>
              </div>
              <p className="cec-page-header__subtitle">
                Registro e assinatura de atas do comitê
              </p>
            </div>
          </div>

          <div className="cec-page-header__meta">
            {lastUpdatedAt ? (
              <p className="cec-page-header__updated">
                Atualizado às {formatUpdatedAt(lastUpdatedAt)}
              </p>
            ) : null}
            <div className="cec-page-header__actions">
              {showNewMinute ? (
                <button
                  type="button"
                  className="cec-btn cec-btn--primary"
                  onClick={() => navigateCec("/apps/comite-etica-conduta/atas/new")}
                >
                  <FilePlus2 size={16} aria-hidden="true" />
                  Nova ata
                </button>
              ) : null}
              {onRefresh ? (
                <button
                  type="button"
                  className="cec-btn cec-btn--primary"
                  onClick={onRefresh}
                  disabled={loading}
                >
                  <RefreshCw
                    size={16}
                    aria-hidden="true"
                    className={loading ? "cec-spin" : undefined}
                  />
                  Atualizar
                </button>
              ) : null}
            </div>
          </div>
        </div>

        <div className="cec-page-header__nav">
          <CecAppTabs
            activeTab={activeTab}
            access={access}
            onChange={(tab) => navigateCec(pathForTab(tab))}
          />
        </div>

        <div className="cec-page-header__brand-bar" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
    </header>
  );
}
