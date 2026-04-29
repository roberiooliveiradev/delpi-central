import { useMemo, useState } from "react";
import { AlertsExecutiveAction } from "../components/AlertsExecutiveAction";
import { AlertsPriorityHighlights } from "../components/AlertsPriorityHighlights";
import { AlertsSummaryCards } from "../components/AlertsSummaryCards";
import { CriticalDepartmentList } from "../components/CriticalDepartmentList";
import { CriticalIndicatorList } from "../components/CriticalIndicatorList";
import { ExecutiveAlertsList } from "../components/ExecutiveAlertsList";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { LoadingActivityBadge } from "../components/LoadingActivityBadge";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { StrategicIndicatorsReferenceFilters } from "../components/StrategicIndicatorsReferenceFilters";
import { TopAlertHighlight } from "../components/TopAlertHighlight";
import { useStrategicIndicatorsAlerts } from "../../state/hooks/useStrategicIndicatorsAlerts";
import {
  buildStrategicIndicatorsMonthRange,
  getCurrentStrategicIndicatorsMonthValue,
  resolveStrategicIndicatorsBranch,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
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
  const [referenceMonth, setReferenceMonth] = useState(
    getCurrentStrategicIndicatorsMonthValue(),
  );
  const [viewMode, setViewMode] =
    useState<StrategicIndicatorsViewMode>("consolidated");
  const [branch, setBranch] = useState("01");

  const { startDate, endDate } = useMemo(
    () => buildStrategicIndicatorsMonthRange(referenceMonth),
    [referenceMonth],
  );

  const effectiveBranch = useMemo(
    () => resolveStrategicIndicatorsBranch(viewMode, branch),
    [viewMode, branch],
  );

  const { data, loading, refreshing, error, reload } =
    useStrategicIndicatorsAlerts({
      branch: effectiveBranch,
      competence: referenceMonth,
      startDate,
      endDate,
      getAccessToken,
    });

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
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Alertas"
          description="Carregando visão de criticidade e priorização do painel."
          badge={<LoadingActivityBadge label="Carregando" tone="neutral" />}
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
        />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Alertas"
          description="Não foi possível carregar a visão de alertas do painel."
          badge={<StatusBadge label="Erro" variant="warning" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência e a visão analítica desejada para consultar os alertas do período."
        >
          {filters}
        </SectionBlock>

        <InfoState
          title="Falha ao carregar alertas"
          description={error}
          actionLabel="Tentar novamente"
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
    <div className="si-page">
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
        />
      ) : null}

      {error && data ? (
        <InfoState
          title="Falha ao atualizar alertas"
          description={error}
          actionLabel="Tentar novamente"
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
        <AlertsPriorityHighlights data={data} />
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
        <CriticalIndicatorList alerts={data.indicatorAlerts} />
      </SectionBlock>
    </div>
  );
}