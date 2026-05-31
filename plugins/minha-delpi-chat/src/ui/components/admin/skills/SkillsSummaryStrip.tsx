import type { SkillStatusFilter, SkillsSummary } from "./skillsSummary";

import "../knowledge/KnowledgeSummaryStrip.css";

type SkillsSummaryStripProps = {
  summary: SkillsSummary;
  activeFilter: SkillStatusFilter;
  isLoading?: boolean;
  onFilterChange?: (filter: SkillStatusFilter) => void;
};

function formatCount(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function SkillsSummaryStrip({
  summary,
  activeFilter,
  isLoading = false,
  onFilterChange,
}: SkillsSummaryStripProps) {
  const items: {
    key: string;
    label: string;
    value: number;
    filter: SkillStatusFilter;
    hint?: string;
  }[] = [
    { key: "total", label: "Total", value: summary.total, filter: "all" },
    {
      key: "active",
      label: "Ativas",
      value: summary.active,
      filter: "active",
      hint: "Visíveis no catálogo dos agentes",
    },
    {
      key: "inactive",
      label: "Inativas",
      value: summary.inactive,
      filter: "inactive",
    },
  ];

  return (
    <div
      className="mdc-admin-knowledge-summary"
      role="region"
      aria-label="Resumo das habilidades do chat"
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
