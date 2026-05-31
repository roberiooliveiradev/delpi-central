import type { GuidelinesSummary, GuidelineStatusFilter } from "./guidelinesSummary";

import "../knowledge/KnowledgeSummaryStrip.css";

type GuidelinesSummaryStripProps = {
  summary: GuidelinesSummary;
  activeFilter: GuidelineStatusFilter;
  onFilterChange?: (filter: GuidelineStatusFilter) => void;
};

function formatCount(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

type KpiItem = {
  key: string;
  label: string;
  value: number;
  filter: GuidelineStatusFilter;
  hint?: string;
};

export function GuidelinesSummaryStrip({
  summary,
  activeFilter,
  onFilterChange,
}: GuidelinesSummaryStripProps) {
  const items: KpiItem[] = [
    { key: "total", label: "Total", value: summary.total, filter: "all" },
    {
      key: "active",
      label: "Ativas",
      value: summary.active,
      filter: "active",
      hint: "Publicadas e em vigor",
    },
    {
      key: "draft",
      label: "Rascunhos",
      value: summary.draft,
      filter: "draft",
    },
    {
      key: "archived",
      label: "Arquivadas",
      value: summary.archived,
      filter: "archived",
    },
  ];

  return (
    <div
      className="mdc-admin-knowledge-summary"
      role="region"
      aria-label="Resumo das diretrizes globais"
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
