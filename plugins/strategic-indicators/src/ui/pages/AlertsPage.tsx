import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useStrategicIndicatorsFilters } from "../../state/hooks/useStrategicIndicatorsFilters";
import { AlertsExecutiveAction } from "../components/AlertsExecutiveAction";
import { AlertsPriorityHighlights } from "../components/AlertsPriorityHighlights";
import { AlertsSummaryCards } from "../components/AlertsSummaryCards";
import { CriticalDepartmentList } from "../components/CriticalDepartmentList";
import { CriticalIndicatorList } from "../components/CriticalIndicatorList";
import { ExecutiveAlertsList } from "../components/ExecutiveAlertsList";
import { InfoState } from "../components/InfoState";
import { StrategicIndicatorsPageError } from "../components/StrategicIndicatorsPageError";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import { TopAlertHighlight } from "../components/TopAlertHighlight";
import { RefreshSnapshotButton } from "../components/RefreshSnapshotButton";
import { useStrategicIndicatorsAlerts } from "../../state/hooks/useStrategicIndicatorsAlerts";
import "./AlertsPage.css";

type AlertsPageProps = {
  getAccessToken?: () => string | undefined;
};

function buildPartialErrorDescription(
  errors: Array<{ departmentId: string; source: string; message: string }>,
) {
  return errors
    .map(
      (item) =>
        `Departamento: ${item.departmentId} • Fonte: ${item.source} • Erro: ${item.message}`,
    )
    .join("\n");
}

export function AlertsPage({ getAccessToken }: AlertsPageProps) {
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

  const { data, loading, refreshing, requestProgress, error, reload } =
    useStrategicIndicatorsAlerts({
      branch: effectiveBranch,
      competence: referenceMonth,
      startDate,
      endDate,
      getAccessToken,
    });

  const loadingProgress = useLoadingProgress(loading && !data, requestProgress);
  const refreshingProgress = useLoadingProgress(Boolean(refreshing && data), requestProgress);

  const refreshButton = (
    <RefreshSnapshotButton
      getAccessToken={getAccessToken}
      onRefreshed={() => void reload()}
      disabled={loading || refreshing}
    />
  );

  const filters = (
    <StrategicIndicatorsReferenceFilters
      referenceMonth={referenceMonth}
      viewMode={viewMode}
      branch={branch}
      onReferenceMonthChange={setReferenceMonth}
      onViewModeChange={setViewMode}
      onBranchChange={setBranch}
    />
  );

  if (loading && !data) {
    return (
      <div className="si-alerts-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Alertas"
          description="Carregando visão de criticidade e priorização do painel."
          badge={<LoadingActivityBadge label="Carregando" tone="neutral" />}
          actions={refreshButton}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência e a visão analítica desejada para consultar os alertas do período."
        >
          {filters}
        </SectionBlock>

        <LoadingActivityInline
          title="Carregando alertas"
          description="Aguarde enquanto os alertas reais são carregados."
          variant="panel"
          tone="info"
          progressPercent={loadingProgress}
        />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="si-alerts-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Alertas"
          description="Não foi possível carregar a visão de alertas do painel."
          badge={<StatusBadge label="Erro" variant="warning" />}
          actions={refreshButton}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência e a visão analítica desejada para consultar os alertas do período."
        >
          {filters}
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

  const topExecutiveAlert = data.executiveAlerts[0] ?? null;

  return (
    <div className="si-alerts-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Alertas"
        description={`Visão de criticidade e priorização do painel. Competência ${data.competence}.`}
        badge={
          loading || refreshing ? (
            <LoadingActivityBadge label="Atualizando" tone="info" />
          ) : (
            <StatusBadge label="API Real" variant="warning" />
          )
        }
        actions={refreshButton}
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência e a visão analítica desejada para consultar os alertas do período."
      >
        {filters}
      </SectionBlock>

      {refreshing ? (
        <LoadingActivityInline
          title="Atualizando alertas"
          description="Os dados exibidos estão sendo atualizados para o novo período."
          variant="compact"
          tone="info"
          progressPercent={refreshingProgress}
        />
      ) : null}

      {error && data ? (
        <StrategicIndicatorsPageError
          error={error}
          mode="refresh"
          onAction={() => void reload()}
        />
      ) : null}

      {data.partialSuccess && data.errors.length > 0 ? (
        <InfoState
          title="Parte das fontes falhou na coleta"
          description={buildPartialErrorDescription(data.errors)}
          actionLabel="Tentar novamente"
          onAction={() => void reload()}
        />
      ) : null}

      <SectionBlock
        title="Síntese de criticidade"
        description="Resumo da condição atual do índice e da distribuição dos alertas do painel."
      >
        <AlertsSummaryCards data={data} />
      </SectionBlock>

      <SectionBlock
        title="Direcionamento executivo"
        description="Leitura objetiva do que deve ser atacado primeiro no cenário atual."
      >
        <div className="si-alerts-executive-layout">
          <AlertsExecutiveAction data={data} />
          <TopAlertHighlight alert={topExecutiveAlert} />
        </div>
      </SectionBlock>

      <SectionBlock
        title="Destaques de priorização"
        description="Recorte direto da área e do indicador que mais exigem ação no cenário atual."
      >
        <AlertsPriorityHighlights
          data={data}
          competence={referenceMonth}
          viewMode={viewMode}
          branch={branch}
        />
      </SectionBlock>

      <SectionBlock
        title="Alertas executivos"
        description="Leitura resumida dos principais sinais executivos do painel."
      >
        <ExecutiveAlertsList alerts={data.executiveAlerts} />
      </SectionBlock>

      <SectionBlock
        title="Departamentos prioritários"
        description="Áreas que exigem acompanhamento mais próximo no cenário atual."
      >
        <CriticalDepartmentList alerts={data.departmentAlerts} />
      </SectionBlock>

      <SectionBlock
        title="Indicadores prioritários"
        description="Indicadores com maior necessidade de atenção no recorte analítico atual."
      >
        <CriticalIndicatorList
          alerts={data.indicatorAlerts}
          competence={referenceMonth}
          viewMode={viewMode}
          branch={branch}
        />
      </SectionBlock>
    </div>
  );
}