import type { ProcessoComparativoItem } from "../data/api/transformometroApi";

export type ComparativoChartRow = {
  revisao_id: string;
  label: string;
  economiaBruta: number;
  economiaLiquida: number;
  ganhoCapacidade: number;
  investimento: number;
  recursos: number;
  horas: number;
  ativa: boolean;
};

export type ComparativoChartView = "money" | "hours";

import { cenarioLabel } from "../content/cenarioLabels";

export function revisaoComparativoLabel(item: ProcessoComparativoItem): string {
  const versao = item.versao_revisao?.trim() || "?";
  const cenario = item.cenario_tipo?.trim();
  return cenario ? `v${versao} · ${cenarioLabel(cenario)}` : `v${versao}`;
}

export function toComparativoChartRows(items: ProcessoComparativoItem[]): ComparativoChartRow[] {
  return items.map((item) => ({
    revisao_id: item.revisao_id,
    label: revisaoComparativoLabel(item),
    economiaBruta: Number(item.totais.economia_bruta ?? 0),
    economiaLiquida: Number(item.totais.economia_liquida_mes ?? 0),
    ganhoCapacidade: Number(item.totais.ganho_capacidade ?? 0),
    investimento: Number(item.totais.investimento_total_mes ?? 0),
    recursos: Number(item.totais.custo_recursos_compartilhados_mes ?? 0),
    horas: Number(item.totais.horas_economizadas_mes ?? 0),
    ativa: Boolean(item.revisao_ativa),
  }));
}

export const COMPARATIVO_MONEY_SERIES = [
  { key: "economiaBruta" as const, label: "Economia bruta", color: "#089bdb" },
  { key: "economiaLiquida" as const, label: "Economia líquida", color: "#2e7d32" },
  { key: "ganhoCapacidade" as const, label: "Ganho capacidade", color: "#0d9488" },
  { key: "investimento" as const, label: "Invest. total", color: "#be123c" },
  { key: "recursos" as const, label: "Recursos comp.", color: "#7c3aed" },
];

export const COMPARATIVO_HOURS_SERIES = [
  { key: "horas" as const, label: "Horas/mês", color: "#f59e0b" },
];

export function collectComparativoAvisos(
  items: ProcessoComparativoItem[]
): Array<{ revisaoLabel: string; message: string }> {
  const out: Array<{ revisaoLabel: string; message: string }> = [];
  for (const item of items) {
    const avisos = item.avisos ?? [];
    if (!avisos.length) continue;
    const label = revisaoComparativoLabel(item);
    for (const aviso of avisos) {
      if (!aviso.message) continue;
      out.push({ revisaoLabel: label, message: aviso.message });
    }
  }
  return out;
}

export function collectComparativoCategorias(items: ProcessoComparativoItem[]): string[] {
  const seen = new Set<string>();
  const ordered: string[] = [];
  for (const item of items) {
    if ((item.cenario_tipo ?? "").toLowerCase() === "baseline") continue;
    const cat = (item.beneficio_calculo_categoria || "automatico").trim().toLowerCase();
    if (!cat || seen.has(cat)) continue;
    seen.add(cat);
    ordered.push(cat);
  }
  return ordered;
}
