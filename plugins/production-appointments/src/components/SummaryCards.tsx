import {
  ClipboardList,
  Factory,
  Layers,
  Package,
  PackageX,
} from "lucide-react";

import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { AppointmentTotals } from "../types/appointments";
import { formatInteger, formatQuantity } from "../utils/formatters";
import { KpiCard } from "./KpiCard";

type SummaryCardsProps = {
  totals: AppointmentTotals | null;
  loading?: boolean;
};

export function SummaryCards({ totals, loading = false }: SummaryCardsProps) {
  return (
    <section className="pa-kpi-grid" aria-label="Resumo do período">
      <KpiCard
        title="Apontamentos"
        titleHint={PA_HELP_TOOLTIPS.kpis.appointments}
        value={formatInteger(totals?.appointment_count)}
        icon={<ClipboardList size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Qtd. produzida"
        titleHint={PA_HELP_TOOLTIPS.kpis.qtyProduced}
        value={formatQuantity(totals?.qty_produced)}
        icon={<Package size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Qtd. perdida"
        titleHint={PA_HELP_TOOLTIPS.kpis.qtyLost}
        value={formatQuantity(totals?.qty_lost)}
        icon={<PackageX size={20} />}
        loading={loading}
      />
      <KpiCard
        title="OPs"
        titleHint={PA_HELP_TOOLTIPS.kpis.opCount}
        value={formatInteger(totals?.op_count)}
        icon={<Layers size={20} />}
        loading={loading}
      />
      <KpiCard
        title="CTs"
        titleHint={PA_HELP_TOOLTIPS.kpis.workCenterCount}
        value={formatInteger(totals?.work_center_count)}
        icon={<Factory size={20} />}
        loading={loading}
      />
    </section>
  );
}
