import { Boxes, PackageMinus, PackagePlus } from "lucide-react";

import type { SafetyStockSummaryData } from "../types/safetyStock";
import { formatIntegerPtBr } from "../utils/formatters";
import { KpiCard } from "./KpiCard";

type SafetyStockSummaryProps = {
  summary: SafetyStockSummaryData | null;
  loading?: boolean;
  refreshing?: boolean;
};

export function SafetyStockSummary({
  summary,
  loading = false,
  refreshing = false,
}: SafetyStockSummaryProps) {
  const busy = loading || refreshing;

  return (
    <section className="ess-kpi-grid" aria-label="Indicadores de estoque de segurança">
      <KpiCard
        title="Total de matérias-primas"
        value={formatIntegerPtBr(summary?.total_materials ?? 0)}
        icon={<Boxes size={22} />}
        loading={busy && !summary}
      />
      <KpiCard
        title="Abaixo do estoque de segurança"
        value={formatIntegerPtBr(summary?.below_safety_stock ?? 0)}
        icon={<PackageMinus size={22} />}
        loading={busy && !summary}
        valueTone={(summary?.below_safety_stock ?? 0) > 0 ? "danger" : "default"}
      />
      <KpiCard
        title="Acima do estoque de segurança"
        value={formatIntegerPtBr(summary?.above_safety_stock ?? 0)}
        icon={<PackagePlus size={22} />}
        loading={busy && !summary}
      />
    </section>
  );
}
