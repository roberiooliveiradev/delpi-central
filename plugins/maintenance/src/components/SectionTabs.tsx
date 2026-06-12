type SectionTabItem = {
  id: string;
  label: string;
  count?: number;
};

type SectionTabsProps = {
  tabs: SectionTabItem[];
  activeId: string;
  onChange: (id: string) => void;
  ariaLabel?: string;
};

export function SectionTabs({ tabs, activeId, onChange, ariaLabel }: SectionTabsProps) {
  return (
    <div className="dm-section-tabs" role="tablist" aria-label={ariaLabel ?? "Seções"}>
      {tabs.map((tab) => {
        const active = tab.id === activeId;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active}
            className={`dm-section-tabs__tab${active ? " is-active" : ""}`}
            onClick={() => onChange(tab.id)}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined ? (
              <span className="dm-section-tabs__count">{tab.count}</span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
