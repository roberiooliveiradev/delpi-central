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
  /** Valores do período distribuídos igualmente entre os dias do filtro em cada competência. */
  dayProrated: boolean;
};

type MonthTotals = {
  bruta: number;
  liquida: number;
  investimento: number;
  horas: number;
};

function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

function addDailyFromCompetencia(
  competencia: string,
  values: MonthTotals,
  dateStart: string,
  dateEnd: string,
  totals: Map<string, MonthTotals>
) {
  const match = competencia.match(/^(\d{4})-(\d{2})$/);
  if (!match) return;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const dim = daysInMonth(year, month);
  let daysInFilter = 0;
  for (let day = 1; day <= dim; day += 1) {
    const iso = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    if (iso >= dateStart && iso <= dateEnd) {
      daysInFilter += 1;
    }
  }
  if (daysInFilter <= 0) return;

  const perDayBruta = values.bruta / daysInFilter;
  const perDayLiquida = values.liquida / daysInFilter;
  const perDayInvestimento = values.investimento / daysInFilter;
  const perDayHoras = values.horas / daysInFilter;

  for (let day = 1; day <= dim; day += 1) {
    const iso = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    if (iso < dateStart || iso > dateEnd) continue;

    const current = totals.get(iso) ?? { bruta: 0, liquida: 0, investimento: 0, horas: 0 };
    current.bruta += perDayBruta;
    current.liquida += perDayLiquida;
    current.investimento += perDayInvestimento;
    current.horas += perDayHoras;
    totals.set(iso, current);
  }
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

export function buildEvolucaoSavingsSeries(
  items: DashboardEvolucaoItem[],
  dateStart: string | undefined,
  dateEnd: string | undefined,
  granularity: ChartGranularity
): EvolucaoChartSeriesResult {
  if (!dateStart || !dateEnd) {
    return { points: [], truncated: false, dayProrated: false };
  }

  const byMonth = new Map<string, MonthTotals>();
  for (const item of items) {
    const key = item.competencia?.trim() ?? "";
    if (!key) continue;
    const current = byMonth.get(key) ?? { bruta: 0, liquida: 0, investimento: 0, horas: 0 };
    current.bruta += Number(item.economia_bruta ?? 0);
    current.liquida += Number(item.economia_liquida_mes ?? 0);
    current.investimento += Number(
      item.investimento_total_mes ??
        Number(item.investimento_unico_mes ?? 0) +
          Number(item.custo_recorrente_mes ?? 0) +
          Number(item.custo_recursos_compartilhados_mes ?? 0)
    );
    current.horas += Number(item.horas_economizadas_mes ?? 0);
    byMonth.set(key, current);
  }

  const { buckets, truncated } = buildPeriodBuckets(dateStart, dateEnd, granularity);

  if (granularity === "day") {
    const dailyTotals = new Map<string, MonthTotals>();

    for (const [competencia, values] of byMonth) {
      addDailyFromCompetencia(competencia, values, dateStart, dateEnd, dailyTotals);
    }

    const points = buckets.map((bucket) =>
      pointFromTotals(bucket.label, bucket.key, dailyTotals.get(bucket.key))
    );

    return { points, truncated, dayProrated: true };
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
    const current = byYear.get(year) ?? { bruta: 0, liquida: 0, investimento: 0, horas: 0 };
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
