import { useMemo, useState } from "react";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
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
import { StrategicIndicatorsPageError } from "../components/StrategicIndicatorsPageError";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import {
  getFilterViewScopeLabel,
  resolveStrategicIndicatorsBranch,
} from "../shared/strategicIndicatorsFilters";
import { formatIndicatorMetaGoalLine } from "../shared/indicatorValueFormatter";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { RefreshSnapshotButton } from "../components/RefreshSnapshotButton";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import "./IndicatorsPage.css";

type IndicatorsPageProps = {
  getAccessToken?: () => string | undefined;
};

function mapClassificationToStatus(
  classification: string,
): IndicatorAnalyticsViewItem["status"] {
  const normalized = classification.toLowerCase();

  if (normalized.includes("sem dados")) return "info";
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
    requestProgress,
    error,
    reload,
  } = useStrategicIndicators({
    branch: effectiveBranch,
    competence: referenceMonth,
    startDate,
    endDate,
    getAccessToken,
  });

  const loadingProgress = useLoadingProgress(
    loading && items.length === 0,
    requestProgress
  );
  const refreshingProgress = useLoadingProgress(
    Boolean(refreshing && items.length > 0),
    requestProgress
  );

  const viewScopeLabel = useMemo(
    () => getFilterViewScopeLabel(viewMode, branch),
    [viewMode, branch],
  );

  const goalDisplayContext = useMemo(
    () => ({
      filterViewScopeLabel: viewScopeLabel,
      activeBranch: resolveStrategicIndicatorsBranch(viewMode, branch),
    }),
    [viewScopeLabel, viewMode, branch],
  );

  const analyticsItems = useMemo<IndicatorAnalyticsViewItem[]>(
    () =>
      items.map((item) => ({
        id: item.id,
        departmentId: item.departmentId,
        departmentName: item.departmentName,
        indicatorName: item.name,
        strategicDescription: `${viewScopeLabel} · ${formatMetaSource(item.source)} · ${formatIndicatorMetaGoalLine(
          {
            goalLabel: item.goalLabel,
            goalValue: item.goalValue,
            goalMode: item.goalMode,
            monthlyTargets: item.monthlyTargets,
            goals: item.goals,
            valueUnit: item.valueUnit,
            valuePrefix: item.valuePrefix,
            valueSuffix: item.valueSuffix,
            valueDecimals: item.valueDecimals,
          },
          referenceMonth,
          goalDisplayContext,
        )}`,
        scopeType: item.scopeType,
        viewScopeLabel,
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
        realized: item.realized,
        score: item.score,
        gap: item.gap,
        goals: item.goals,
        gaps: item.gaps,
        hasValue: item.hasValue,
        trend: item.trend,
        status: mapClassificationToStatus(item.classification),
        source: item.source,
        valueUnit: item.valueUnit,
        valuePrefix: item.valuePrefix,
        valueSuffix: item.valueSuffix,
        valueDecimals: item.valueDecimals,
      })),
    [items, viewScopeLabel, referenceMonth, goalDisplayContext],
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
        actions={
          <RefreshSnapshotButton
            getAccessToken={getAccessToken}
            onRefreshed={() => void reload()}
            disabled={loading || refreshing}
          />
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
          progressPercent={loadingProgress}
        />
      ) : error && items.length === 0 ? (
        <StrategicIndicatorsPageError
          error={error}
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
              progressPercent={refreshingProgress}
            />
          ) : null}

          {error && items.length > 0 ? (
            <StrategicIndicatorsPageError
              error={error}
              mode="refresh"
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
            <IndicatorPriorityList
              indicators={filteredIndicators}
              competence={referenceMonth}
              displayContext={goalDisplayContext}
            />
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
                viewMode={viewMode}
                branch={branch}
                onSelectIndicator={(indicator) =>
                  setSelectedIndicatorId(indicator.id)
                }
              />

              <IndicatorQuickDetail
                indicator={resolvedSelectedIndicator}
                competence={referenceMonth}
                viewMode={viewMode}
                branch={branch}
              />
            </div>
          </SectionBlock>
        </>
      )}
    </div>
  );
}