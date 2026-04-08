import { useState } from "react";
import { DepartmentTrendGrid } from "../components/DepartmentTrendGrid";
import { IgdTrendTimeline } from "../components/IgdTrendTimeline";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { TrendHeroCard } from "../components/TrendHeroCard";
import { TrendHighlights } from "../components/TrendHighlights";
import { TrendMonthComparison } from "../components/TrendMonthComparison";
import { TrendPriorityList } from "../components/TrendPriorityList";
import { TrendSummaryCards } from "../components/TrendSummaryCards";
import { useStrategicIndicatorsTrends } from "../../state/hooks/useStrategicIndicatorsTrends";

type TrendsPageProps = {
  getAccessToken?: () => string | undefined;
};

function getCurrentMonthValue() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

export function TrendsPage({ getAccessToken }: TrendsPageProps) {
  const [referenceMonth, setReferenceMonth] = useState(getCurrentMonthValue());
  const [monthsToCompare, setMonthsToCompare] = useState(3);

  const { data, loading, refreshing, error, reload } =
    useStrategicIndicatorsTrends({
      competence: referenceMonth,
      months: monthsToCompare,
      getAccessToken,
    });

  if (loading && !data) {
    return (
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Tendências"
          description="Carregando visão temporal do IGD e dos departamentos."
          badge={<StatusBadge label="Carregando" variant="neutral" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência e a quantidade de meses para analisar a tendência histórica."
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

            <label className="si-field">
              <span className="si-field__label">Meses de comparação</span>
              <select
                className="si-input"
                value={monthsToCompare}
                onChange={(event) => setMonthsToCompare(Number(event.target.value))}
              >
                <option value={2}>2 meses</option>
                <option value={3}>3 meses</option>
                <option value={4}>4 meses</option>
                <option value={6}>6 meses</option>
                <option value={12}>12 meses</option>
              </select>
            </label>
          </div>
        </SectionBlock>

        <InfoState
          title="Carregando tendências"
          description="Aguarde enquanto a série temporal é preparada."
        />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Tendências"
          description="Não foi possível carregar a visão temporal do painel."
          badge={<StatusBadge label="Erro" variant="warning" />}
        />

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência e a quantidade de meses para analisar a tendência histórica."
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

            <label className="si-field">
              <span className="si-field__label">Meses de comparação</span>
              <select
                className="si-input"
                value={monthsToCompare}
                onChange={(event) => setMonthsToCompare(Number(event.target.value))}
              >
                <option value={2}>2 meses</option>
                <option value={3}>3 meses</option>
                <option value={4}>4 meses</option>
                <option value={6}>6 meses</option>
                <option value={12}>12 meses</option>
              </select>
            </label>
          </div>
        </SectionBlock>

        <InfoState
          title="Falha ao carregar tendências"
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

  const currentPeriod =
    data.igdSeries[data.igdSeries.length - 1]?.period ?? data.competence;
  const previousPeriod =
    data.igdSeries[data.igdSeries.length - 2]?.period ?? "Anterior";

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Tendências"
        description={`Visão temporal do IGD e dos departamentos. Competência ${data.competence}.`}
        badge={
          <StatusBadge
            label={refreshing ? "Atualizando" : "API Real"}
            variant={refreshing ? "neutral" : "info"}
          />
        }
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência e a quantidade de meses para analisar a tendência histórica."
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

          <label className="si-field">
            <span className="si-field__label">Meses de comparação</span>
            <select
              className="si-input"
              value={monthsToCompare}
              onChange={(event) => setMonthsToCompare(Number(event.target.value))}
            >
              <option value={2}>2 meses</option>
              <option value={3}>3 meses</option>
              <option value={4}>4 meses</option>
              <option value={6}>6 meses</option>
              <option value={12}>12 meses</option>
            </select>
          </label>
        </div>
      </SectionBlock>

      {refreshing ? (
        <InfoState
          title="Atualizando tendências"
          description="Os dados exibidos estão sendo atualizados para o novo período."
        />
      ) : null}

      {error ? (
        <InfoState
          title="Falha parcial ao atualizar tendências"
          description={error}
          actionLabel="Tentar novamente"
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
        <TrendHeroCard
          current={data.currentIgd}
          previous={data.previousIgd}
          classification={data.currentClassification}
        />
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
        title="Evolução mensal"
        description="Série histórica real do IGD no intervalo solicitado."
      >
        <IgdTrendTimeline series={data.igdSeries} />
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