import type { ReactNode } from "react";
import { MapPin } from "lucide-react";

import {
  centrosHref,
  readCostCenterTab,
  type CostCenterTab,
} from "../utils/routing";

export type CostCenterCockpitProps = {
  title: string;
  locationLabel: string;
  cycleYear: string;
  costCenterId: string;
  unitId?: string | null;
  showInvestimentos: boolean;
  showEquipe: boolean;
  investimentosCount?: number | null;
  equipeHint?: string | null;
  investimentos: ReactNode;
  equipe: ReactNode;
};

function resolveInitialTab(
  showInvestimentos: boolean,
  showEquipe: boolean,
): CostCenterTab {
  const fromUrl = readCostCenterTab("investimentos");
  if (fromUrl === "investimentos" && showInvestimentos) return "investimentos";
  if (fromUrl === "equipe" && showEquipe) return "equipe";
  if (showInvestimentos) return "investimentos";
  if (showEquipe) return "equipe";
  return "investimentos";
}

export function CostCenterCockpit({
  title,
  locationLabel,
  cycleYear,
  costCenterId,
  unitId,
  showInvestimentos,
  showEquipe,
  investimentosCount,
  equipeHint,
  investimentos,
  equipe,
}: CostCenterCockpitProps) {
  const activeTab = resolveInitialTab(showInvestimentos, showEquipe);
  const showTabs = showInvestimentos && showEquipe;
  /** Na aba Investimentos o banner unificado vive no painel CAPEX. */
  const showStandaloneHero = activeTab !== "investimentos" || !showInvestimentos;

  const tabHref = (tab: CostCenterTab) =>
    centrosHref({
      costCenterId,
      unitId: unitId || undefined,
      tab,
    });

  return (
    <div className="po-cockpit" data-testid="cost-center-cockpit">
      {showStandaloneHero ? (
        <header className="po-centros__hero">
          <div className="po-centros__hero-copy">
            <p className="po-centros__eyebrow">Elaboração · {cycleYear}</p>
            <h2 className="po-centros__title">{title}</h2>
            <p className="po-centros__lead">
              Cadastre headcount e projeções da equipe para este centro no ciclo.
            </p>
          </div>
          <aside className="po-centros__hero-panel" aria-label="Resumo do centro">
            <dl className="po-centros__meta">
              <div>
                <dt>Ciclo</dt>
                <dd>{cycleYear}</dd>
              </div>
              <div>
                <dt>Local</dt>
                <dd className="po-cockpit__meta-local">
                  <MapPin size={13} aria-hidden="true" />
                  {locationLabel}
                </dd>
              </div>
            </dl>
          </aside>
        </header>
      ) : null}

      {showTabs ? (
        <nav className="po-cockpit__tabs" aria-label="Áreas do orçamento">
          <a
            className={`po-cockpit__tab${activeTab === "investimentos" ? " is-active" : ""}`}
            href={tabHref("investimentos")}
            aria-current={activeTab === "investimentos" ? "page" : undefined}
          >
            Investimentos
            {typeof investimentosCount === "number" ? (
              <span className="po-cockpit__tab-count">{investimentosCount}</span>
            ) : null}
          </a>
          <a
            className={`po-cockpit__tab${activeTab === "equipe" ? " is-active" : ""}`}
            href={tabHref("equipe")}
            aria-current={activeTab === "equipe" ? "page" : undefined}
          >
            Equipe
            {equipeHint ? <span className="po-cockpit__tab-hint">{equipeHint}</span> : null}
          </a>
        </nav>
      ) : null}

      <div className="po-cockpit__panel">
        {activeTab === "investimentos" && showInvestimentos ? investimentos : null}
        {activeTab === "equipe" && showEquipe ? equipe : null}
      </div>
    </div>
  );
}
