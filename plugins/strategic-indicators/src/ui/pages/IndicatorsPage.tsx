import { useMemo, useState } from "react";
import type { IndicatorAnalyticsItem } from "../../data/mocks/indicatorsMock";
import {
  indicatorDepartments,
  indicatorsMock,
  indicatorStatuses,
} from "../../data/mocks/indicatorsMock";
import { IndicatorAnalyticsSummary } from "../components/IndicatorAnalyticsSummary";
import { IndicatorAnalyticsTable } from "../components/IndicatorAnalyticsTable";
import { IndicatorDepartmentOverview } from "../components/IndicatorDepartmentOverview";
import { IndicatorFiltersBar } from "../components/IndicatorFiltersBar";
import { IndicatorPriorityList } from "../components/IndicatorPriorityList";
import { IndicatorQuickDetail } from "../components/IndicatorQuickDetail";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";

export function IndicatorsPage() {
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("all");
  const [status, setStatus] = useState("all");
  const [selectedIndicator, setSelectedIndicator] =
    useState<IndicatorAnalyticsItem | null>(indicatorsMock[0] ?? null);

  const filteredIndicators = useMemo(() => {
    return indicatorsMock.filter((indicator) => {
      const matchesSearch =
        !search.trim() ||
        indicator.indicatorName.toLowerCase().includes(search.toLowerCase()) ||
        indicator.strategicDescription
          .toLowerCase()
          .includes(search.toLowerCase());

      const matchesDepartment =
        department === "all" || indicator.departmentId === department;

      const matchesStatus =
        status === "all" || indicator.status === status;

      return matchesSearch && matchesDepartment && matchesStatus;
    });
  }, [search, department, status]);

  const resolvedSelectedIndicator = useMemo(() => {
    if (!filteredIndicators.length) return null;

    if (
      selectedIndicator &&
      filteredIndicators.some((item) => item.id === selectedIndicator.id)
    ) {
      return selectedIndicator;
    }

    return filteredIndicators[0];
  }, [filteredIndicators, selectedIndicator]);

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Indicadores"
        description="Visão analítica inicial dos indicadores que compõem os IDDs departamentais, com filtros, busca e leitura cruzada entre áreas."
        badge={<StatusBadge label="MVP Analítico" variant="info" />}
      />

      <SectionBlock
        title="Síntese analítica"
        description="Leitura rápida da cobertura e da distribuição dos indicadores no cenário atual."
      >
        <IndicatorAnalyticsSummary indicators={filteredIndicators} />
      </SectionBlock>

      <SectionBlock
        title="Filtros analíticos"
        description="Use os filtros abaixo para buscar e comparar indicadores entre departamentos."
      >
        <IndicatorFiltersBar
          search={search}
          department={department}
          status={status}
          departments={indicatorDepartments}
          statuses={indicatorStatuses}
          onSearchChange={setSearch}
          onDepartmentChange={setDepartment}
          onStatusChange={setStatus}
        />
      </SectionBlock>

      <SectionBlock
        title="Leitura por departamento"
        description="Resumo analítico por área para leitura rápida dos focos departamentais."
      >
        <IndicatorDepartmentOverview indicators={filteredIndicators} />
      </SectionBlock>

      <SectionBlock
        title="Prioridades imediatas"
        description="Indicadores em faixa de atenção para leitura operacional rápida."
      >
        <IndicatorPriorityList indicators={filteredIndicators} />
      </SectionBlock>

      <SectionBlock
        title="Tabela e detalhe rápido"
        description="Selecione um indicador para visualizar seu contexto analítico resumido."
      >
        <div className="si-indicator-analytics-layout">
          <IndicatorAnalyticsTable
            indicators={filteredIndicators}
            selectedIndicatorId={resolvedSelectedIndicator?.id}
            onSelectIndicator={setSelectedIndicator}
          />

          <IndicatorQuickDetail indicator={resolvedSelectedIndicator} />
        </div>
      </SectionBlock>
    </div>
  );
}