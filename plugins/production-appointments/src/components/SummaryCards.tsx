import {
  ClipboardList,
  Factory,
  Layers,
  Package,
  PackageX,
} from "lucide-react";

import type { AppointmentTotals } from "../types/appointments";
import {
  formatInteger,
  formatQuantity,
  QUANTITY_UNIT_LABEL,
} from "../utils/formatters";
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
        value={formatInteger(totals?.appointment_count)}
        icon={<ClipboardList size={20} />}
        loading={loading}
      />
      <KpiCard
        title={`Qtd. produzida (${QUANTITY_UNIT_LABEL})`}
        value={formatQuantity(totals?.qty_produced)}
        icon={<Package size={20} />}
        loading={loading}
      />
      <KpiCard
        title={`Qtd. perdida (${QUANTITY_UNIT_LABEL})`}
        value={formatQuantity(totals?.qty_lost)}
        icon={<PackageX size={20} />}
        loading={loading}
      />
      <KpiCard
        title="OPs"
        value={formatInteger(totals?.op_count)}
        icon={<Layers size={20} />}
        loading={loading}
      />
      <KpiCard
        title="CTs"
        value={formatInteger(totals?.work_center_count)}
        icon={<Factory size={20} />}
        loading={loading}
      />
    </section>
  );
}
