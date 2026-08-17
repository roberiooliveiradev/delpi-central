import { CircleDot, ClipboardList, PackageOpen, RotateCcw, Scale } from "lucide-react";

import { HELP_TOOLTIPS } from "../content/helpTooltips";
import type { SummaryData } from "../types/thirdPartyMaterials";
import { formatInteger, formatQuantity } from "../utils/formatters";
import { KpiCard } from "./KpiCard";

type SummaryCardsProps = {
  summary: SummaryData | null;
  loading?: boolean;
};

export function SummaryCards({ summary, loading = false }: SummaryCardsProps) {
  return (
    <div className="mt-kpi-grid">
      <KpiCard
        title="Remessas"
        titleHint={HELP_TOOLTIPS.kpis.total}
        value={formatInteger(summary?.total_shipments)}
        icon={<ClipboardList size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Abertas"
        titleHint={HELP_TOOLTIPS.kpis.open}
        value={formatInteger(summary?.open_shipments)}
        icon={<PackageOpen size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Parciais"
        titleHint={HELP_TOOLTIPS.kpis.partial}
        value={formatInteger(summary?.partial_shipments)}
        icon={<CircleDot size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Sem retorno"
        titleHint={HELP_TOOLTIPS.kpis.noReturn}
        value={formatInteger(summary?.no_return_shipments)}
        icon={<RotateCcw size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Saldo pendente"
        titleHint={HELP_TOOLTIPS.kpis.pending}
        value={formatQuantity(summary?.pending_balance)}
        icon={<Scale size={20} />}
        loading={loading}
      />
    </div>
  );
}
