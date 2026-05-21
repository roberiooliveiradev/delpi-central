import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useStrategicIndicatorsFilters } from "../../state/hooks/useStrategicIndicatorsFilters";
import { DepartmentTrendGrid } from "../components/DepartmentTrendGrid";
import { IgdTrendTimeline } from "../components/IgdTrendTimeline";
import { InfoState } from "../components/InfoState";
import { StrategicIndicatorsPageError } from "../components/StrategicIndicatorsPageError";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import { TrendHeroCard } from "../components/TrendHeroCard";
import { TrendHighlights } from "../components/TrendHighlights";
import { TrendMonthComparison } from "../components/TrendMonthComparison";
import { TrendPriorityList } from "../components/TrendPriorityList";
import { TrendSummaryCards } from "../components/TrendSummaryCards";
import { useStrategicIndicatorsTrends } from "../../state/hooks/useStrategicIndicatorsTrends";
import "./TrendsPage.css";

type TrendsPageProps = {
  getAccessToken?: () => string | undefined;
};

export function TrendsPage({ getAccessToken }: TrendsPageProps) {
  const {
    referenceMonth,
    viewMode,
    branch,
    monthsToCompare,
    setReferenceMonth,
    setViewMode,
    setBranch,
    setMonthsToCompare,
    effectiveBranch,
  } = useStrategicIndicatorsFilters();

  const { data, loading, refreshing, requestProgress, error, reload } =
    useStrategicIndicatorsTrends({
      branch: effectiveBranch,
      competence: referenceMonth,
      months: monthsToCompare,
      getAccessToken,
    });

  const loadingProgress = useLoadingProgress(loading && !data, requestProgress);
  const refreshingProgress = useLoadingProgress(Boolean(refreshing && data), requestProgress);

  const referenceFilters = (
    <StrategicIndicatorsReferenceFilters
      referenceMonth={referenceMonth}
      viewMode={viewMode}
      branch={branch}
      monthsToCompare={monthsToCompare}
      showMonthsToCompare
      onReferenceMonthChange={setReferenceMonth}
      onViewModeChange={setViewMode}
      onBranchChange={setBranch}
      onMonthsToCompareChange={setMonthsToCompare}
    />
  );

  if (loading && !data) {
    return (
      <div className="si-trends-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Tendências"
          description="Carregando visão temporal do IGD e dos departamentos."
          badge={<LoadingActivityBadge label="Carregando" tone="neutral" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência, a visão analítica e a quantidade de meses para analisar a tendência histórica."
        >
          {referenceFilters}
        </SectionBlock>

        <LoadingActivityInline
          title="Carregando tendências"
          description="Aguarde enquanto a visão temporal do IGD e dos departamentos é preparada."
          variant="panel"
          tone="info"
          progressPercent={loadingProgress}
        />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="si-trends-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Tendências"
          description="Não foi possível carregar a visão temporal do painel."
          badge={<StatusBadge label="Erro" variant="warning" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência, a visão analítica e a quantidade de meses para analisar a tendência histórica."
        >
          {referenceFilters}
        </SectionBlock>

        <StrategicIndicatorsPageError
          error={error}
          onAction={() => void reload()}
        />
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const currentPeriod =
    data.igdSeries[data.igdSeries.length - 1]?.period ?? data.competence;
  const previousPeriod =
    data.igdSeries[data.igdSeries.length - 2]?.period ?? "Anterior";

  return (
    <div className="si-trends-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Tendências"
        description={`Visão temporal do IGD e dos departamentos. Competência ${data.competence}.`}
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
        description="Selecione o mês de referência, a visão analítica e a quantidade de meses para analisar a tendência histórica."
      >
        {referenceFilters}
      </SectionBlock>

      {refreshing ? (
        <LoadingActivityInline
          title="Atualizando tendências"
          description="Os dados exibidos estão sendo atualizados para o novo período."
          variant="compact"
          tone="info"
          progressPercent={refreshingProgress}
        />
      ) : null}

      {error ? (
        <StrategicIndicatorsPageError
          error={error}
          mode="refresh"
          onAction={() => void reload()}
        />
      ) : null}

      {data.partialSuccess && data.errors.length > 0 ? (
        <InfoState
          title="Parte das fontes falhou na coleta"
          description="A série foi montada com sucesso parcial. Revise as integrações com erro antes de usar a leitura como fechamento definitivo."
          actionLabel="Tentar novamente"
          onAction={() => void reload()}
        />
      ) : null}

      <SectionBlock
        title="Tendência consolidada do IGD"
        description="Leitura executiva da evolução mais recente do índice global."
      >
        <div className="si-trends-executive-grid">
          <TrendHeroCard
            current={data.currentIgd}
            previous={data.previousIgd}
            classification={data.currentClassification}
            currentPeriod={currentPeriod}
            previousPeriod={previousPeriod}
          />

          <IgdTrendTimeline series={data.igdSeries} />
        </div>
      </SectionBlock>

      <SectionBlock
        title="Síntese temporal"
        description="Resumo quantitativo da variação do índice e do comportamento agregado das áreas."
      >
        <TrendSummaryCards
          currentIgd={data.currentIgd}
          previousIgd={data.previousIgd}
          departments={data.departments}
        />
      </SectionBlock>

      <SectionBlock
        title="Comparação do último fechamento"
        description="Comparação direta entre o mês atual e o mês anterior."
      >
        <TrendMonthComparison
          currentPeriod={currentPeriod}
          previousPeriod={previousPeriod}
          currentIgd={data.currentIgd}
          previousIgd={data.previousIgd}
        />
      </SectionBlock>

      <SectionBlock
        title="Destaques do período"
        description="Melhor movimento e maior queda entre os departamentos no recorte atual."
      >
        <TrendHighlights departments={data.departments} />
      </SectionBlock>

      <SectionBlock
        title="Pontos de atenção"
        description="Áreas em queda no período, para leitura gerencial rápida."
      >
        <TrendPriorityList departments={data.departments} />
      </SectionBlock>

      <SectionBlock
        title="Comportamento dos departamentos"
        description="Comparação rápida entre nota atual, período anterior e direção da tendência por área."
      >
        <DepartmentTrendGrid departments={data.departments} />
      </SectionBlock>
    </div>
  );
}