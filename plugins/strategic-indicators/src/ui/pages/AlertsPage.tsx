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
import { TopAlertHighlight } from "../components/TopAlertHighlight";
import { useStrategicIndicatorsAlerts } from "../../state/hooks/useStrategicIndicatorsAlerts";

type AlertsPageProps = {
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
  const [referenceMonth, setReferenceMonth] = useState(getCurrentMonthValue());

  const { startDate, endDate } = useMemo(
    () => buildMonthRange(referenceMonth),
    [referenceMonth],
  );

  const { data, loading, refreshing, error, reload } =
    useStrategicIndicatorsAlerts({
      competence: referenceMonth,
      startDate,
      endDate,
      getAccessToken,
    });

  if (loading && !data) {
    return (
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Alertas"
          description="Carregando visão de criticidade e priorização do painel."
          badge={<StatusBadge label="Carregando" variant="neutral" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência para consultar os alertas do período."
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

        <InfoState
          title="Carregando alertas"
          description="Aguarde enquanto os alertas reais são carregados."
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
          description="Selecione o mês de referência para consultar os alertas do período."
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
          <StatusBadge
            label={loading || refreshing ? "Atualizando" : "API Real"}
            variant={loading || refreshing ? "neutral" : "warning"}
          />
        }
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência para consultar os alertas do período."
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

      {refreshing ? (
        <InfoState
          title="Atualizando alertas"
          description="Os dados exibidos estão sendo atualizados para o novo período."
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