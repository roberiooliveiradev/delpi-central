import type { AgentCatalogFilter, AgentsSummary } from "./agentsSummary";

import "../knowledge/KnowledgeSummaryStrip.css";

type AgentsSummaryStripProps = {
  summary: AgentsSummary;
  activeFilter: AgentCatalogFilter;
  isLoading?: boolean;
  onFilterChange?: (filter: AgentCatalogFilter) => void;
};

function formatCount(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function AgentsSummaryStrip({
  summary,
  activeFilter,
  isLoading = false,
  onFilterChange,
}: AgentsSummaryStripProps) {
  const items: {
    key: string;
    label: string;
    value: number;
    filter: AgentCatalogFilter;
    hint?: string;
  }[] = [
    { key: "total", label: "Total", value: summary.total, filter: "all" },
    {
      key: "enabled",
      label: "Ativos",
      value: summary.enabled,
      filter: "enabled",
    },
    {
      key: "specialized",
      label: "Especializados",
      value: summary.withSpecialization,
      filter: "specialized",
      hint: "Com domínio RAG / tools configurados",
    },
    {
      key: "disabled",
      label: "Inativos",
      value: summary.disabled,
      filter: "disabled",
    },
  ];

  return (
    <div
      className="mdc-admin-knowledge-summary"
      role="region"
      aria-label="Resumo dos agentes especializados"
    >
      <div className="mdc-admin-knowledge-summary__grid mdc-admin-kpi-grid">
        {items.map((item) => {
          const isActive = item.filter === activeFilter;
          const isInteractive = Boolean(onFilterChange);

          return (
            <article
              key={item.key}
              className={[
                "mdc-admin-kpi-card",
                isActive ? "is-active" : "",
                isInteractive ? "is-clickable" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {isInteractive ? (
                <button
                  type="button"
                  className="mdc-admin-knowledge-summary__hit"
                  title={item.hint}
                  disabled={isLoading}
                  onClick={() => onFilterChange?.(item.filter)}
                >
                  <h3>{item.label}</h3>
                  <strong>{formatCount(item.value)}</strong>
                  {item.hint ? <p>{item.hint}</p> : null}
                </button>
              ) : (
                <>
                  <h3>{item.label}</h3>
                  <strong>{formatCount(item.value)}</strong>
                  {item.hint ? <p>{item.hint}</p> : null}
                </>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}
