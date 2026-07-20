import { BarSeriesChart } from "@delpi/plugin-ui/index";

import type { ConsumptionAnalysisSummaryData } from "../types/consumptionAnalysis";
import { ANALYSIS_STATUS_LABELS } from "../utils/safetyStockStatus";

type ConsumptionAnalysisDistributionProps = {
  summary: ConsumptionAnalysisSummaryData | null;
  loading?: boolean;
};

export function ConsumptionAnalysisDistribution({
  summary,
  loading = false,
}: ConsumptionAnalysisDistributionProps) {
  const points = (summary?.status_distribution ?? []).map((item) => ({
    label: ANALYSIS_STATUS_LABELS[item.status] ?? item.status,
    value: item.count,
  }));

  return (
    <section
      className="ess-card delpi-ui-card ess-analysis-chart"
      aria-label="Distribuição por situação"
    >
      <div className="ess-analysis-chart__header">
        <h2>Distribuição vs estoque sugerido</h2>
        <p>Quantidade de itens por situação do ESTSEG em relação ao valor sugerido.</p>
      </div>
      {loading && !summary ? (
        <p className="ess-detail__state" role="status">
          Carregando distribuição…
        </p>
      ) : null}
      {!loading && points.length === 0 ? (
        <p className="ess-detail__empty">Nenhum item para distribuir com os filtros atuais.</p>
      ) : null}
      {points.length > 0 ? (
        <div className="ess-analysis-chart__plot">
          <BarSeriesChart
            points={points}
            emptyMessage="Sem distribuição para exibir."
            options={{
              title: "Quantidade de itens",
              showTitle: false,
              showLegend: false,
              showAxes: true,
              showXAxisLabels: true,
              showYAxisLabels: true,
              showXAxisTitle: false,
              showYAxisTitle: false,
              showDataLabels: true,
              showGrid: true,
              seriesColor: "#089bdb",
              seriesName: "Itens",
            }}
          />
        </div>
      ) : null}
    </section>
  );
}
