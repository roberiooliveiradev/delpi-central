import type { DashboardEvolucaoItem } from "../data/api/transformometroApi";
import type { ChartGranularity } from "../types/chart";
import { buildPeriodBuckets } from "./periodBuckets";

export type SavingsChartPoint = {
  name: string;
  bruta: number;
  liquida: number;
  investimento: number;
  horas: number;
  sortKey: string;
};

export type EvolucaoChartSeriesResult = {
  points: SavingsChartPoint[];
  truncated: boolean;
  /**
   * true quando a API devolveu média diária plana (legado).
   * Com `granularity=day` a série já vem atribuída por vigência no backend.
   */
  dayProrated: boolean;
};

type MonthTotals = {
  bruta: number;
  liquida: number;
  investimento: number;
  horas: number;
};

function emptyTotals(): MonthTotals {
  return { bruta: 0, liquida: 0, investimento: 0, horas: 0 };
}

function pointFromTotals(
  name: string,
  sortKey: string,
  row: MonthTotals | undefined
): SavingsChartPoint {
  return {
    name,
    sortKey,
    bruta: Number((row?.bruta ?? 0).toFixed(2)),
    liquida: Number((row?.liquida ?? 0).toFixed(2)),
    investimento: Number((row?.investimento ?? 0).toFixed(2)),
    horas: Number((row?.horas ?? 0).toFixed(2)),
  };
}

function totalsFromItem(item: DashboardEvolucaoItem): MonthTotals {
  return {
    bruta: Number(item.economia_bruta ?? 0),
    liquida: Number(item.economia_liquida_mes ?? 0),
    investimento: Number(
      item.investimento_total_mes ??
        Number(item.investimento_unico_mes ?? 0) +
          Number(item.custo_recorrente_mes ?? 0) +
          Number(item.custo_recursos_compartilhados_mes ?? 0)
    ),
    horas: Number(item.horas_economizadas_mes ?? 0),
  };
}

/**
 * Monta pontos do gráfico a partir da série já calculada pela API.
 * Visão dia: items com `competencia` YYYY-MM-DD (backend).
 * Visão mês/ano: agrega competências YYYY-MM no client só para buckets do eixo.
 */
export function buildEvolucaoSavingsSeries(
  items: DashboardEvolucaoItem[],
  dateStart: string | undefined,
  dateEnd: string | undefined,
  granularity: ChartGranularity
): EvolucaoChartSeriesResult {
  if (!dateStart || !dateEnd) {
    return { points: [], truncated: false, dayProrated: false };
  }

  const { buckets, truncated } = buildPeriodBuckets(dateStart, dateEnd, granularity);

  if (granularity === "day") {
    const byDay = new Map<string, MonthTotals>();
    for (const item of items) {
      const key = item.competencia?.trim() ?? "";
      if (!/^\d{4}-\d{2}-\d{2}$/.test(key)) continue;
      const current = byDay.get(key) ?? emptyTotals();
      const next = totalsFromItem(item);
      current.bruta += next.bruta;
      current.liquida += next.liquida;
      current.investimento += next.investimento;
      current.horas += next.horas;
      byDay.set(key, current);
    }

    const points = buckets.map((bucket) =>
      pointFromTotals(bucket.label, bucket.key, byDay.get(bucket.key))
    );
    return { points, truncated, dayProrated: false };
  }

  const byMonth = new Map<string, MonthTotals>();
  for (const item of items) {
    const key = item.competencia?.trim() ?? "";
    const monthKey = /^\d{4}-\d{2}-\d{2}$/.test(key) ? key.slice(0, 7) : key;
    if (!/^\d{4}-\d{2}$/.test(monthKey)) continue;
    const current = byMonth.get(monthKey) ?? emptyTotals();
    const next = totalsFromItem(item);
    current.bruta += next.bruta;
    current.liquida += next.liquida;
    current.investimento += next.investimento;
    current.horas += next.horas;
    byMonth.set(monthKey, current);
  }

  if (granularity === "month") {
    const points = buckets.map((bucket) =>
      pointFromTotals(bucket.label, bucket.key, byMonth.get(bucket.key))
    );
    return { points, truncated, dayProrated: false };
  }

  const byYear = new Map<string, MonthTotals>();
  for (const [monthKey, values] of byMonth) {
    const year = monthKey.slice(0, 4);
    const current = byYear.get(year) ?? emptyTotals();
    current.bruta += values.bruta;
    current.liquida += values.liquida;
    current.investimento += values.investimento;
    current.horas += values.horas;
    byYear.set(year, current);
  }

  const points = buckets.map((bucket) =>
    pointFromTotals(bucket.label, bucket.key, byYear.get(bucket.key))
  );

  return { points, truncated, dayProrated: false };
}
