import type { AgentCatalogFilter, AgentsSummary } from "./agentsSummary";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { formatMetricNumber } from "../metrics-tab/adminMetricsFormatters";

type AgentsSummaryStripProps = {
  summary: AgentsSummary;
  activeFilter: AgentCatalogFilter;
  isLoading?: boolean;
  onFilterChange?: (filter: AgentCatalogFilter) => void;
};

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
    { key: "enabled", label: "Ativos", value: summary.enabled, filter: "enabled" },
    {
      key: "specialized",
      label: "Especializados",
      value: summary.withSpecialization,
      filter: "specialized",
      hint: "Com domínio RAG e ferramentas configurados",
    },
    { key: "disabled", label: "Inativos", value: summary.disabled, filter: "disabled" },
  ];

  return (
    <AdminSummaryStrip ariaLabel="Resumo dos agentes especializados" isLoading={isLoading}>
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
