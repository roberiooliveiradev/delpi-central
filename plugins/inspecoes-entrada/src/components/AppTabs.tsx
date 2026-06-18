import type { InspecoesEntradaTab } from "../utils/tabs";

type AppTabsProps = {
  activeTab: InspecoesEntradaTab;
  onChange: (tab: InspecoesEntradaTab) => void;
};

const TABS: Array<{ id: InspecoesEntradaTab; label: string }> = [
  { id: "overview", label: "Visão Geral" },
  { id: "historico", label: "Histórico" },
];

export function AppTabs({ activeTab, onChange }: AppTabsProps) {
  return (
    <nav className="ie-tabs" aria-label="Seções do app">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={`ie-tabs__item${activeTab === tab.id ? " ie-tabs__item--active" : ""}`}
          aria-current={activeTab === tab.id ? "page" : undefined}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
