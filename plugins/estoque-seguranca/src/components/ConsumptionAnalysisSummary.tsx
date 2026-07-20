import { ArrowDownRight, ArrowUpRight, Scale } from "lucide-react";

import type { ConsumptionAnalysisSummaryData } from "../types/consumptionAnalysis";
import { formatIntegerPtBr } from "../utils/formatters";
import { formatIsoDatePtBr } from "../utils/safetyStockStatus";
import { KpiCard } from "./KpiCard";

type ConsumptionAnalysisSummaryProps = {
  summary: ConsumptionAnalysisSummaryData | null;
  loading?: boolean;
  refreshing?: boolean;
};

export function ConsumptionAnalysisSummary({
  summary,
  loading = false,
  refreshing = false,
}: ConsumptionAnalysisSummaryProps) {
  const busy = loading || refreshing;
  const periodLabel =
    summary != null
      ? `${formatIsoDatePtBr(summary.period_start)} a ${formatIsoDatePtBr(summary.period_end)} · ${formatIntegerPtBr(summary.period_business_days)} dias úteis`
      : "Últimos 12 meses (baixas SD3 local 99 / TM 999)";

  return (
    <section className="ess-analysis-summary" aria-label="Indicadores da análise de consumo">
      <p className="ess-analysis-summary__period">{periodLabel}</p>
      <div className="ess-kpi-grid">
        <KpiCard
          title="Itens analisados"
          titleHint="Com ESTSEG ≠ 0 e baixas elegíveis no período"
          value={formatIntegerPtBr(summary?.analyzed_items ?? 0)}
          icon={<Scale size={22} />}
          loading={busy && !summary}
        />
        <KpiCard
          title="Abaixo do sugerido"
          value={formatIntegerPtBr(summary?.below_suggested ?? 0)}
          icon={<ArrowDownRight size={22} />}
          loading={busy && !summary}
          valueTone={(summary?.below_suggested ?? 0) > 0 ? "danger" : "default"}
        />
        <KpiCard
          title="Acima do sugerido"
          value={formatIntegerPtBr(summary?.above_suggested ?? 0)}
          icon={<ArrowUpRight size={22} />}
          loading={busy && !summary}
        />
      </div>
    </section>
  );
}
