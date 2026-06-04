import type { SkillStatusFilter, SkillsSummary } from "./skillsSummary";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { formatMetricNumber } from "../metrics-tab/adminMetricsFormatters";

type SkillsSummaryStripProps = {
  summary: SkillsSummary;
  activeFilter: SkillStatusFilter;
  isLoading?: boolean;
  onFilterChange?: (filter: SkillStatusFilter) => void;
};

export function SkillsSummaryStrip({
  summary,
  activeFilter,
  isLoading = false,
  onFilterChange,
}: SkillsSummaryStripProps) {
  const items = [
    { key: "total", label: "Total", value: summary.total, filter: "all" as const },
    {
      key: "active",
      label: "Ativas",
      value: summary.active,
      filter: "active" as const,
      hint: "Visíveis no catálogo dos agentes",
    },
    { key: "inactive", label: "Inativas", value: summary.inactive, filter: "inactive" as const },
  ];

  return (
    <AdminSummaryStrip ariaLabel="Resumo das habilidades do chat" isLoading={isLoading}>
      {items.map((item) => (
        <AdminKpiCard
          key={item.key}
          title={item.label}
          value={formatMetricNumber(item.value)}
          hint={item.hint}
          active={item.filter === activeFilter}
          disabled={isLoading}
          onClick={onFilterChange ? () => onFilterChange(item.filter) : undefined}
        />
      ))}
    </AdminSummaryStrip>
  );
}
