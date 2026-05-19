import { useMemo, useState } from "react";
import type { IndicatorAnalyticsViewItem } from "../../data/types/indicatorAnalyticsView";
import { useStrategicIndicators } from "../../state/hooks/useStrategicIndicators";
import { useStrategicIndicatorsFilters } from "../../state/hooks/useStrategicIndicatorsFilters";
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
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import "./IndicatorsPage.css";

type IndicatorsPageProps = {
  getAccessToken?: () => string | undefined;
};

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

function buildPartialErrorDescription(
  errors: Array<{ departmentId: string; source: string; message: string }>,
) {
  return errors
    .map(
      (item) =>
        `Departamento: ${item.departmentId} • Fonte: ${formatMetaSource(item.source)} • Erro: ${item.message}`,
    )
    .join("\n");
}

function formatGoalMode(goalMode?: string) {
  if (goalMode === "monthly_curve") return "curva mensal";
  return "meta padrão";
}

function formatGoalPeriodicity(goalPeriodicity?: string) {
  if (goalPeriodicity === "daily") return "diária";
  if (goalPeriodicity === "weekly") return "semanal";
  if (goalPeriodicity === "monthly") return "mensal";
  if (goalPeriodicity === "quarterly") return "trimestral";
  if (goalPeriodicity === "semiannual") return "semestral";
  if (goalPeriodicity === "yearly") return "anual";
  return goalPeriodicity || "não informada";
}

function formatMetaSource(source?: string) {
  if (!source) return "fonte não informada";

  const normalized = source.toLowerCase();

  if (normalized.includes("manual")) return "manual";
  if (normalized.includes("sheet")) return "planilha";
  if (normalized.includes("totvs")) return "TOTVS";
  if (normalized.includes("portal_rh")) return "Portal RH";
  if (normalized.includes("lmp")) return "LMP";
  if (normalized.includes("transforma")) return "Transforma Mais";
  if (normalized.includes("financial")) return "Financeiro";
  if (normalized.includes("commercial")) return "Comercial";
  if (normalized.includes("production")) return "Produção";
  if (normalized.includes("quality")) return "Qualidade";
  if (normalized.includes("engineering")) return "Engenharia";
  if (normalized.includes("hr")) return "RH";

  return source;
}

function formatPerformanceDirection(performanceDirection?: string) {
  if (performanceDirection === "lower_is_better") return "quanto menor, melhor";
  return "quanto maior, melhor";
}

function buildIndicatorNarrative(item: {
  source: string;
  goalLabel: string;
  goalPeriodicity: string;
  goalMode?: string;
  performanceDirection?: string;
  monthlyTargets?: Array<{ month_number: number; target_value: number }>;
}) {
  const goalModeLabel = formatGoalMode(item.goalMode);
  const directionLabel = formatPerformanceDirection(item.performanceDirection);
  const periodicityLabel = formatGoalPeriodicity(item.goalPeriodicity);
  const sourceLabel = formatMetaSource(item.source);

  const monthlyCurveHint =
    item.goalMode === "monthly_curve" && (item.monthlyTargets?.length ?? 0) > 0
      ? ` • ${item.monthlyTargets?.length ?? 0} metas mensais`
      : "";

  return `${sourceLabel} • Meta ${item.goalLabel} • Periodicidade ${periodicityLabel} • ${goalModeLabel} • ${directionLabel}${monthlyCurveHint}`;
}

export function IndicatorsPage({ getAccessToken }: IndicatorsPageProps) {
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("all");
  const [status, setStatus] = useState("all");
  const {
    referenceMonth,
    viewMode,
    branch,
    setReferenceMonth,
    setViewMode,
    setBranch,
    startDate,
    endDate,
    effectiveBranch,
  } = useStrategicIndicatorsFilters();
  const [selectedIndicatorId, setSelectedIndicatorId] = useState<string | null>(
    null,
  );

  const {
    items,
    fetchErrors,
    partialSuccess,
    loading,
    refreshing,
    error,
    reload,
  } = useStrategicIndicators({
    branch: effectiveBranch,
    competence: referenceMonth,
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
        strategicDescription: buildIndicatorNarrative({
          source: item.source,
          goalLabel: item.goalLabel,
          goalPeriodicity: item.goalPeriodicity,
          goalMode: item.goalMode,
          performanceDirection: item.performanceDirection,
          monthlyTargets: item.monthlyTargets.map((target) => ({
            month_number: target.month_number,
            target_value: target.target_value,
          })),
        }),
        weightPct: item.weightPct,
        goalLabel: item.goalLabel,
        goalValue: item.goalValue,
        goalPeriodicity: item.goalPeriodicity,
        goalMode: item.goalMode,
        monthlyTargets: item.monthlyTargets.map((target) => ({
          monthNumber: target.month_number,
          targetValue: target.target_value,
        })),
        performanceDirection: item.performanceDirection,
        currentValue: item.value,
        score: item.score,
        gap: item.gap,
        trend: item.trend,
        status: mapClassificationToStatus(item.classification),
        source: item.source,
        valueUnit: item.valueUnit,
        valuePrefix: item.valuePrefix,
        valueSuffix: item.valueSuffix,
        valueDecimals: item.valueDecimals,
      })),
    [items],
  );

  const departmentOptions = useMemo(
    () => buildDepartmentOptions(analyticsItems),
    [analyticsItems],
  );

  const filteredIndicators = useMemo(() => {
    return analyticsItems.filter((indicator) => {
      const matchesDepartment =
        department === "all" || indicator.departmentId === department;

      const matchesSearch =
        !search.trim() ||
        indicator.indicatorName.toLowerCase().includes(search.toLowerCase()) ||
        indicator.strategicDescription
          .toLowerCase()
          .includes(search.toLowerCase());

      const matchesStatus = status === "all" || indicator.status === status;

      return matchesDepartment && matchesSearch && matchesStatus;
    });
  }, [analyticsItems, department, search, status]);

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

  const referenceFilters = (
    <StrategicIndicatorsReferenceFilters
      referenceMonth={referenceMonth}
      viewMode={viewMode}
      branch={branch}
      onReferenceMonthChange={setReferenceMonth}
      onViewModeChange={setViewMode}
      onBranchChange={setBranch}
    />
  );

  return (
    <div className="si-indicators-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Indicadores"
        description="Visão analítica dos indicadores que compõem os IDDs departamentais, com leitura de meta estruturada, direção de performance e filtros por área."
        badge={
          loading || refreshing ? (
            <LoadingActivityBadge label="Atualizando" tone="info" />
          ) : (
            <StatusBadge label="API Real" variant="success" />
          )
        }
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência e a visão analítica desejada para consultar os indicadores do período correto."
      >
        {referenceFilters}
      </SectionBlock>

      {loading && items.length === 0 ? (
        <LoadingActivityInline
          title="Carregando indicadores"
          description="Aguarde enquanto os indicadores reais são carregados."
          variant="panel"
          tone="info"
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
            <LoadingActivityInline
              title="Atualizando indicadores"
              description="Os dados exibidos estão sendo atualizados com o novo filtro."
              variant="compact"
              tone="info"
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

          {partialSuccess && fetchErrors.length > 0 ? (
            <InfoState
              title="Alguns indicadores não puderam ser carregados"
              description={buildPartialErrorDescription(fetchErrors)}
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
                competence={referenceMonth}
                onSelectIndicator={(indicator) =>
                  setSelectedIndicatorId(indicator.id)
                }
              />

              <IndicatorQuickDetail
                indicator={resolvedSelectedIndicator}
                competence={referenceMonth}
              />
            </div>
          </SectionBlock>
        </>
      )}
    </div>
  );
}