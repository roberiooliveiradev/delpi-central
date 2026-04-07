import { useMemo, useState } from "react";
import type { IndicatorAnalyticsViewItem } from "../../data/types/indicatorAnalyticsView";
import { useStrategicIndicators } from "../../state/hooks/useStrategicIndicators";
import { IndicatorAnalyticsSummary } from "../components/IndicatorAnalyticsSummary";
import { IndicatorAnalyticsTable } from "../components/IndicatorAnalyticsTable";
import { IndicatorDepartmentOverview } from "../components/IndicatorDepartmentOverview";
import { IndicatorFiltersBar } from "../components/IndicatorFiltersBar";
import { IndicatorPriorityList } from "../components/IndicatorPriorityList";
import { IndicatorQuickDetail } from "../components/IndicatorQuickDetail";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";

type IndicatorsPageProps = {
  getAccessToken?: () => string | undefined;
};

function getCurrentMonthValue() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function buildMonthRange(monthValue: string) {
  if (!monthValue) {
    return {
      startDate: undefined,
      endDate: undefined,
    };
  }

  const [yearStr, monthStr] = monthValue.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);

  if (!year || !month) {
    return {
      startDate: undefined,
      endDate: undefined,
    };
  }

  const firstDay = `01-${String(month).padStart(2, "0")}-${year}`;
  const lastDayDate = new Date(year, month, 0);
  const lastDay = `${String(lastDayDate.getDate()).padStart(2, "0")}-${String(
    month,
  ).padStart(2, "0")}-${year}`;

  return {
    startDate: firstDay,
    endDate: lastDay,
  };
}

function mapClassificationToStatus(
  classification: string,
): IndicatorAnalyticsViewItem["status"] {
  const normalized = classification.toLowerCase();

  if (normalized.includes("excel")) return "success";
  if (normalized.includes("alto")) return "success";
  if (normalized.includes("satisfatório")) return "info";
  if (normalized.includes("regular")) return "warning";
  return "danger";
}

function buildDepartmentOptions(items: IndicatorAnalyticsViewItem[]) {
  const unique = new Map<string, string>();

  items.forEach((item) => {
    unique.set(item.departmentId, item.departmentName);
  });

  return [
    { value: "all", label: "Todos os departamentos" },
    ...Array.from(unique.entries()).map(([value, label]) => ({
      value,
      label,
    })),
  ];
}

const indicatorStatuses = [
  { value: "all", label: "Todos os status" },
  { value: "success", label: "Alto desempenho" },
  { value: "info", label: "Satisfatório" },
  { value: "warning", label: "Atenção" },
  { value: "danger", label: "Crítico" },
];

export function IndicatorsPage({ getAccessToken }: IndicatorsPageProps) {
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("all");
  const [status, setStatus] = useState("all");
  const [referenceMonth, setReferenceMonth] = useState(getCurrentMonthValue());

  const { startDate, endDate } = useMemo(
    () => buildMonthRange(referenceMonth),
    [referenceMonth],
  );

  const departmentIdForApi = department === "all" ? undefined : department;

  const { items, loading, refreshing, error, reload } = useStrategicIndicators({
    departmentId: departmentIdForApi,
    startDate,
    endDate,
    getAccessToken,
  });

  const analyticsItems = useMemo<IndicatorAnalyticsViewItem[]>(
    () =>
      items.map((item) => ({
        id: item.id,
        departmentId: item.departmentId,
        departmentName: item.departmentName,
        indicatorName: item.name,
        strategicDescription: `${item.source} • Meta ${item.goal2026}`,
        weightPct: item.weightPct,
        goal2026: item.goal2026,
        currentValue: item.value,
        score: item.score,
        gap: item.gap,
        trend: item.trend,
        status: mapClassificationToStatus(item.classification),
        source: item.source,
      })),
    [items],
  );

  const departmentOptions = useMemo(
    () => buildDepartmentOptions(analyticsItems),
    [analyticsItems],
  );

  const filteredIndicators = useMemo(() => {
    return analyticsItems.filter((indicator) => {
      const matchesSearch =
        !search.trim() ||
        indicator.indicatorName.toLowerCase().includes(search.toLowerCase()) ||
        indicator.strategicDescription
          .toLowerCase()
          .includes(search.toLowerCase());

      const matchesStatus = status === "all" || indicator.status === status;

      return matchesSearch && matchesStatus;
    });
  }, [analyticsItems, search, status]);

  const [selectedIndicatorId, setSelectedIndicatorId] = useState<string | null>(
    null,
  );

  const resolvedSelectedIndicator = useMemo(() => {
    if (!filteredIndicators.length) return null;

    if (
      selectedIndicatorId &&
      filteredIndicators.some((item) => item.id === selectedIndicatorId)
    ) {
      return (
        filteredIndicators.find((item) => item.id === selectedIndicatorId) ??
        null
      );
    }

    return filteredIndicators[0];
  }, [filteredIndicators, selectedIndicatorId]);

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Indicadores"
        description="Visão analítica inicial dos indicadores que compõem os IDDs departamentais, com filtros, busca, período de referência e leitura cruzada entre áreas."
        badge={
          <StatusBadge
            label={loading || refreshing ? "Carregando" : "API Real"}
            variant={loading || refreshing ? "neutral" : "success"}
          />
        }
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência para consultar os indicadores do período correto."
      >
        <div className="si-form-grid">
          <label className="si-field">
            <span className="si-field__label">Mês de referência</span>
            <input
              type="month"
              className="si-input"
              value={referenceMonth}
              onChange={(event) => setReferenceMonth(event.target.value)}
            />
          </label>
        </div>
      </SectionBlock>

      {loading && items.length === 0 ? (
        <InfoState
          title="Carregando indicadores"
          description="Aguarde enquanto os indicadores reais são carregados."
        />
      ) : error && items.length === 0 ? (
        <InfoState
          title="Falha ao carregar indicadores"
          description={error}
          actionLabel="Tentar novamente"
          onAction={() => void reload()}
        />
      ) : (
        <>
          {refreshing ? (
            <InfoState
              title="Atualizando indicadores"
              description="Os dados exibidos estão sendo atualizados com o novo filtro."
            />
          ) : null}

          {error && items.length > 0 ? (
            <InfoState
              title="Falha ao atualizar indicadores"
              description={error}
              actionLabel="Tentar novamente"
              onAction={() => void reload()}
            />
          ) : null}

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
              departments={departmentOptions}
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
                onSelectIndicator={(indicator) =>
                  setSelectedIndicatorId(indicator.id)
                }
              />

              <IndicatorQuickDetail indicator={resolvedSelectedIndicator} />
            </div>
          </SectionBlock>
        </>
      )}
    </div>
  );
}