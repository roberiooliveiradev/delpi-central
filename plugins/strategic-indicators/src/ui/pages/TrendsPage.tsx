import { trendsMock } from "../../data/mocks/trendsMock";
import { DepartmentTrendGrid } from "../components/DepartmentTrendGrid";
import { IgdTrendTimeline } from "../components/IgdTrendTimeline";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { TrendHeroCard } from "../components/TrendHeroCard";
import { TrendHighlights } from "../components/TrendHighlights";
import { TrendMonthComparison } from "../components/TrendMonthComparison";
import { TrendPriorityList } from "../components/TrendPriorityList";
import { TrendSummaryCards } from "../components/TrendSummaryCards";

export function TrendsPage() {
  const data = trendsMock;

  const currentPeriod =
    data.igdSeries[data.igdSeries.length - 1]?.period ?? "Atual";
  const previousPeriod =
    data.igdSeries[data.igdSeries.length - 2]?.period ?? "Anterior";

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Tendências"
        description="Visão temporal inicial do IGD e dos departamentos, permitindo entender o comportamento recente do índice e das áreas."
        badge={<StatusBadge label="MVP Temporal" variant="info" />}
      />

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
        description="Série temporal mock do IGD para leitura de comportamento ao longo dos últimos meses."
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