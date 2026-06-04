import type { GuidelinesSummary, GuidelineStatusFilter } from "./guidelinesSummary";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { formatMetricNumber } from "../metrics-tab/adminMetricsFormatters";

type GuidelinesSummaryStripProps = {
  summary: GuidelinesSummary;
  activeFilter: GuidelineStatusFilter;
  onFilterChange?: (filter: GuidelineStatusFilter) => void;
};

export function GuidelinesSummaryStrip({
  summary,
  activeFilter,
  onFilterChange,
}: GuidelinesSummaryStripProps) {
  const items = [
    { key: "total", label: "Total", value: summary.total, filter: "all" as const },
    {
      key: "active",
      label: "Ativas",
      value: summary.active,
      filter: "active" as const,
      hint: "Publicadas e em vigor",
    },
    { key: "draft", label: "Rascunhos", value: summary.draft, filter: "draft" as const },
    {
      key: "archived",
      label: "Arquivadas",
      value: summary.archived,
      filter: "archived" as const,
    },
  ];

  return (
    <AdminSummaryStrip ariaLabel="Resumo das diretrizes globais">
      {items.map((item) => (
        <AdminKpiCard
          key={item.key}
          title={item.label}
          value={formatMetricNumber(item.value)}
          hint={item.hint}
          active={item.filter === activeFilter}
          onClick={onFilterChange ? () => onFilterChange(item.filter) : undefined}
        />
      ))}
    </AdminSummaryStrip>
  );
}
