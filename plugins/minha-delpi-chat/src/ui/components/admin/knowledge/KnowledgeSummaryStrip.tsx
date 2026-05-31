import type { AdminKnowledgeDocumentsSummary } from "../../../../data/api/adminTypes";
import type { DocumentStatusFilter } from "./knowledgeTypes";

import "./KnowledgeSummaryStrip.css";

type KnowledgeSummaryStripProps = {
  summary: AdminKnowledgeDocumentsSummary | null | undefined;
  activeFilter: DocumentStatusFilter;
  isLoading?: boolean;
  onFilterChange?: (filter: DocumentStatusFilter) => void;
};

function formatCount(value: number | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

type KpiItem = {
  key: string;
  label: string;
  value: number | undefined;
  filter?: DocumentStatusFilter;
  hint?: string;
};

export function KnowledgeSummaryStrip({
  summary,
  activeFilter,
  isLoading = false,
  onFilterChange,
}: KnowledgeSummaryStripProps) {
  const items: KpiItem[] = [
    {
      key: "total",
      label: "Total",
      value: summary?.total,
      filter: "all",
    },
    {
      key: "active",
      label: "Indexados",
      value: summary?.active,
      filter: "active",
      hint: "Documentos ativos na base global",
    },
    {
      key: "inactive",
      label: "Inativos",
      value: summary?.inactive,
      filter: "inactive",
    },
    {
      key: "pending",
      label: "Sem índice",
      value: summary?.pendingIndex,
      hint: "Ativos sem chunks indexados",
    },
  ];

  return (
    <div
      className="mdc-admin-knowledge-summary"
      role="region"
      aria-label="Resumo da base de conhecimento"
    >
      <div className="mdc-admin-knowledge-summary__grid mdc-admin-kpi-grid">
        {items.map((item) => {
          const isActive = item.filter != null && item.filter === activeFilter;
          const isInteractive = Boolean(onFilterChange && item.filter);

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
                  onClick={() => onFilterChange?.(item.filter!)}
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
