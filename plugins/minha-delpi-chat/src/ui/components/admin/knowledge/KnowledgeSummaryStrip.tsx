import type { AdminKnowledgeDocumentsSummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { formatMetricNumber } from "../metrics-tab/adminMetricsFormatters";
import type { DocumentStatusFilter } from "./knowledgeTypes";

import "./KnowledgeSummaryStrip.css";

type KnowledgeSummaryStripProps = {
  summary: AdminKnowledgeDocumentsSummary | null | undefined;
  activeFilter: DocumentStatusFilter;
  isLoading?: boolean;
  onFilterChange?: (filter: DocumentStatusFilter) => void;
};

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
    { key: "total", label: "Total", value: summary?.total, filter: "all" },
    {
      key: "active",
      label: "Indexados",
      value: summary?.active,
      filter: "active",
      hint: "Documentos ativos na base global",
    },
    { key: "inactive", label: "Inativos", value: summary?.inactive, filter: "inactive" },
    {
      key: "pending",
      label: "Sem índice",
      value: summary?.pendingIndex,
      hint: "Ativos sem chunks indexados",
    },
  ];

  return (
    <AdminSummaryStrip
      ariaLabel="Resumo da base de conhecimento"
      isLoading={isLoading}
      className="mdc-admin-knowledge-summary"
    >
      {items.map((item) => {
        const isInteractive = Boolean(onFilterChange && item.filter);

        return (
          <AdminKpiCard
            key={item.key}
            title={item.label}
            value={formatMetricNumber(item.value)}
            hint={item.hint}
            active={item.filter != null && item.filter === activeFilter}
            disabled={isLoading}
            onClick={
              isInteractive ? () => onFilterChange?.(item.filter!) : undefined
            }
          />
        );
      })}
    </AdminSummaryStrip>
  );
}
