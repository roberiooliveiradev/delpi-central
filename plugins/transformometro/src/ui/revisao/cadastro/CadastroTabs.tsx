import type { ReactNode } from "react";

export type CadastroTabId = "vigencia" | "medicao" | "investimentos" | "recursos";

export type CadastroTabDef = {
  id: CadastroTabId;
  label: string;
  badge?: string | number;
};

type Props = {
  tabs: CadastroTabDef[];
  activeTab: CadastroTabId;
  onTabChange: (id: CadastroTabId) => void;
  children: ReactNode;
};

export function CadastroTabs({ tabs, activeTab, onTabChange, children }: Props) {
  return (
    <div className="ds-cadastro-tabs">
      <div className="ds-cadastro-tabs__list" role="tablist" aria-label="Cadastro da revisão">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          const badge =
            tab.badge !== undefined && tab.badge !== "" ? String(tab.badge) : null;

          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              id={`tm-tab-${tab.id}`}
              aria-selected={isActive}
              aria-controls={`tm-tabpanel-${tab.id}`}
              className={["ds-cadastro-tabs__tab", isActive ? "is-active" : ""]
                .filter(Boolean)
                .join(" ")}
              onClick={() => onTabChange(tab.id)}
            >
              <span>{tab.label}</span>
              {badge ? <span className="ds-cadastro-tabs__badge">{badge}</span> : null}
            </button>
          );
        })}
      </div>
      <div
        className="ds-cadastro-tabs__panel"
        role="tabpanel"
        id={`tm-tabpanel-${activeTab}`}
        aria-labelledby={`tm-tab-${activeTab}`}
      >
        {children}
      </div>
    </div>
  );
}
