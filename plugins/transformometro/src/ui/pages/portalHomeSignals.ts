import type { PageHeroHighlight } from "@delpi/plugin-ui/index";

import type {
  DashboardAlertItem,
  DashboardResumo,
  DashboardVencimentos,
} from "../../data/api/transformometroApi";
import { formatCurrency, formatDecimal, formatHours } from "../../utils/format";

export type PortalHomeEventDescriptor = {
  id: string;
  title: string;
  description: string;
  tone: "warning" | "neutral";
};

export function buildPortalHomeHighlights(input: {
  loading: boolean;
  resumo: DashboardResumo | null;
  contextLabel?: string | null;
}): PageHeroHighlight[] {
  const { loading, resumo, contextLabel } = input;
  if (!resumo && !loading) return [];
  const description = contextLabel?.trim() || undefined;
  return [
    {
      id: "net-economy",
      label: "Economia líquida",
      value: formatCurrency(resumo?.economia_liquida_total),
      description,
      loading,
    },
    {
      id: "hours",
      label: "Horas economizadas",
      value: formatHours(resumo?.horas_economizadas_total),
      description,
      loading,
    },
    {
      id: "solutions",
      label: "Soluções implementadas",
      value: formatDecimal(resumo?.solucoes_implementadas, 0),
      description,
      loading,
    },
  ];
}

export function buildPortalHomeEvents(input: {
  vencimentos: DashboardVencimentos | null;
  alertas: DashboardAlertItem[];
}): PortalHomeEventDescriptor[] {
  const events: PortalHomeEventDescriptor[] = [];
  const vencendoCount = input.vencimentos?.total_vencendo ?? input.vencimentos?.vencendo.length ?? 0;
  if (vencendoCount > 0) {
    events.push({
      id: "revisions-due",
      title: "Revisões a vencer — validade de 1 ano",
      description: `${vencendoCount.toLocaleString("pt-BR")} revisão(ões) vencem nos próximos 90 dias.`,
      tone: "warning",
    });
  }
  if (input.alertas.length > 0) {
    events.push({
      id: "negative-net",
      title: "Economia líquida negativa",
      description: `${input.alertas.length.toLocaleString("pt-BR")} processo(s) com ao menos 3 meses consecutivos de líquida negativa.`,
      tone: "warning",
    });
  }
  return events;
}
