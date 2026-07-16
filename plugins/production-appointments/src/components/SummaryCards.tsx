import {
  ClipboardList,
  Factory,
  Layers,
  Package,
  PackageX,
} from "lucide-react";
import type { ReactNode } from "react";

import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { AppointmentTotals } from "../types/appointments";
import { formatInteger, formatQuantity } from "../utils/formatters";
import { KpiCard } from "./KpiCard";

export type SummaryCardKey =
  | "appointments"
  | "qtyProduced"
  | "qtyLost"
  | "opCount"
  | "workCenterCount";

type SummaryCardsProps = {
  totals: AppointmentTotals | null;
  loading?: boolean;
  /** Oculta KPIs redundantes no contexto (ex.: OPs na página de uma OP). */
  omitKeys?: SummaryCardKey[];
};

type SummaryCardDef = {
  key: SummaryCardKey;
  title: string;
  titleHint: string;
  value: string;
  icon: ReactNode;
};

export function SummaryCards({
  totals,
  loading = false,
  omitKeys = [],
}: SummaryCardsProps) {
  const omitted = new Set(omitKeys);
  const cards: SummaryCardDef[] = [
    {
      key: "appointments",
      title: "Apontamentos",
      titleHint: PA_HELP_TOOLTIPS.kpis.appointments,
      value: formatInteger(totals?.appointment_count),
      icon: <ClipboardList size={20} />,
    },
    {
      key: "qtyProduced",
      title: "Qtd. produzida",
      titleHint: PA_HELP_TOOLTIPS.kpis.qtyProduced,
      value: formatQuantity(totals?.qty_produced),
      icon: <Package size={20} />,
    },
    {
      key: "qtyLost",
      title: "Qtd. perdida",
      titleHint: PA_HELP_TOOLTIPS.kpis.qtyLost,
      value: formatQuantity(totals?.qty_lost),
      icon: <PackageX size={20} />,
    },
    {
      key: "opCount",
      title: "OPs",
      titleHint: PA_HELP_TOOLTIPS.kpis.opCount,
      value: formatInteger(totals?.op_count),
      icon: <Layers size={20} />,
    },
    {
      key: "workCenterCount",
      title: "CTs",
      titleHint: PA_HELP_TOOLTIPS.kpis.workCenterCount,
      value: formatInteger(totals?.work_center_count),
      icon: <Factory size={20} />,
    },
  ].filter((card) => !omitted.has(card.key));

  return (
    <section className="pa-kpi-grid" aria-label="Resumo do período">
      {cards.map((card) => (
        <KpiCard
          key={card.key}
          title={card.title}
          titleHint={card.titleHint}
          value={card.value}
          icon={card.icon}
          loading={loading}
        />
      ))}
    </section>
  );
}
