import { useMemo, useState } from "react";
import { PresentationAlertsBoard } from "../components/PresentationAlertsBoard";
import { PresentationClosingPanel } from "../components/PresentationClosingPanel";
import { PresentationDepartmentBoard } from "../components/PresentationDepartmentBoard";
import { PresentationExecutiveStrip } from "../components/PresentationExecutiveStrip";
import { PresentationHero } from "../components/PresentationHero";
import { PresentationNarrativeStrip } from "../components/PresentationNarrativeStrip";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { useStrategicIndicatorsAlerts } from "../../state/hooks/useStrategicIndicatorsAlerts";
import { useStrategicIndicatorsExecutiveSummary } from "../../state/hooks/useStrategicIndicatorsExecutiveSummary";
import { buildPresentationViewData } from "../../data/types/presentation";

type PresentationPageProps = {
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

export function PresentationPage({ getAccessToken }: PresentationPageProps) {
  const [referenceMonth, setReferenceMonth] = useState(getCurrentMonthValue());

  const { startDate, endDate } = useMemo(
    () => buildMonthRange(referenceMonth),
    [referenceMonth],
  );

  const executive = useStrategicIndicatorsExecutiveSummary({
    competence: referenceMonth,
    startDate,
    endDate,
    getAccessToken,
  });

  const alerts = useStrategicIndicatorsAlerts({
    competence: referenceMonth,
    startDate,
    endDate,
    getAccessToken,
  });

  const loading =
    (executive.loading && !executive.data) || (alerts.loading && !alerts.data);

  const error = executive.error ?? alerts.error;

  if (loading) {
    return (
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Apresentação Executiva"
          description="Carregando visão consolidada do período."
          badge={<StatusBadge label="Carregando" variant="neutral" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência da apresentação executiva."
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
          title="Carregando apresentação"
          description="Aguarde enquanto a síntese executiva é preparada."
        />
      </div>
    );
  }

  if (error || !executive.data || !alerts.data) {
    return (
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Apresentação Executiva"
          description="Não foi possível montar a apresentação executiva do período."
          badge={<StatusBadge label="Erro" variant="warning" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência da apresentação executiva."
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
          title="Falha ao carregar apresentação"
          description={error ?? "Não foi possível obter os dados necessários."}
          actionLabel="Tentar novamente"
          onAction={() => {
            void executive.reload();
            void alerts.reload();
          }}
        />
      </div>
    );
  }

  const data = buildPresentationViewData({
    executiveSummary: executive.data,
    executiveAlerts: alerts.data.executiveAlerts,
  });

  return (
    <div className="si-presentation-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Apresentação Executiva"
        description={`Síntese executiva do período ${data.competence}.`}
        badge={
          <StatusBadge
            label={
              executive.refreshing || alerts.refreshing
                ? "Atualizando"
                : "API Real"
            }
            variant={
              executive.refreshing || alerts.refreshing ? "neutral" : "success"
            }
          />
        }
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência da apresentação executiva."
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

      {executive.refreshing || alerts.refreshing ? (
        <InfoState
          title="Atualizando apresentação"
          description="Os dados exibidos estão sendo atualizados para o novo período."
        />
      ) : null}

      {(executive.error || alerts.error) && executive.data && alerts.data ? (
        <InfoState
          title="Falha ao atualizar apresentação"
          description={executive.error ?? alerts.error ?? ""}
          actionLabel="Tentar novamente"
          onAction={() => {
            void executive.reload();
            void alerts.reload();
          }}
        />
      ) : null}

      <PresentationHero
        igd={data.igd}
        classification={data.classification}
        trendLabel={data.trendLabel}
      />

      <PresentationNarrativeStrip
        classification={data.classification}
        trendLabel={data.trendLabel}
        topDepartment={data.topDepartment}
        topRisk={data.topRisk}
      />

      <PresentationExecutiveStrip
        currentIgd={data.currentIgd}
        previousIgd={data.previousIgd}
        topDepartment={data.topDepartment}
        topRisk={data.topRisk}
      />

      <div className="si-presentation-layout">
        <PresentationDepartmentBoard departments={data.departments} />
        <PresentationAlertsBoard alerts={data.executiveAlerts} />
      </div>

      <PresentationClosingPanel
        currentPeriod={data.currentPeriod}
        previousPeriod={data.previousPeriod}
        classification={data.classification}
        trendLabel={data.trendLabel}
        topDepartment={data.topDepartment}
        topRisk={data.topRisk}
      />
    </div>
  );
}