import type { InspecoesProcessoTab } from "../utils/tabs";

type AppTabsProps = {
  activeTab: InspecoesProcessoTab;
  onChange: (tab: InspecoesProcessoTab) => void;
};

const TABS: Array<{ id: InspecoesProcessoTab; label: string }> = [
  { id: "overview", label: "Visão Geral" },
  { id: "historico", label: "Histórico" },
  { id: "auditoria", label: "Auditoria" },
];

export function AppTabs({ activeTab, onChange }: AppTabsProps) {
  return (
    <nav className="ip-tabs" aria-label="Seções do app">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={`ip-tabs__item${activeTab === tab.id ? " ip-tabs__item--active" : ""}`}
          aria-current={activeTab === tab.id ? "page" : undefined}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
