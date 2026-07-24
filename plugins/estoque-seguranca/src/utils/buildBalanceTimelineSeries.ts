import type {
  SafetyStockProjectionLedgerEntry,
  SafetyStockProjectionSummary,
} from "../types/safetyStock";

/** Horizonte corrido da linha do tempo (12 meses). */
export const BALANCE_TIMELINE_CALENDAR_DAYS = 365;

const MONTH_SHORT_PT = [
  "jan",
  "fev",
  "mar",
  "abr",
  "mai",
  "jun",
  "jul",
  "ago",
  "set",
  "out",
  "nov",
  "dez",
] as const;

export type BalanceTimelinePoint = {
  date: string;
  /** Rótulo curto do eixo (ex.: ago de 26) — preenchido só no 1º dia do mês. */
  monthTick: string | null;
  balance: number;
  balancePositive: number;
  balanceNegative: number;
  isShortage: boolean;
  isBusinessDay: boolean;
};

export type BalanceTimelineSeries = {
  points: BalanceTimelinePoint[];
  periodStart: string;
  periodEnd: string;
  averageDailyConsumption: number;
  firstShortageDate: string | null;
};

function parseIsoDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(Date.UTC(year, month - 1, day));
  if (
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) {
    return null;
  }
  return date;
}

export function formatIsoDateUtc(date: Date): string {
  const y = date.getUTCFullYear();
  const m = String(date.getUTCMonth() + 1).padStart(2, "0");
  const d = String(date.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function isBusinessDayUtc(date: Date): boolean {
  return date.getUTCDay() >= 1 && date.getUTCDay() <= 5;
}

export function countBusinessDaysInclusive(start: Date, end: Date): number {
  if (end.getTime() < start.getTime()) return 0;
  let count = 0;
  const cursor = new Date(start.getTime());
  while (cursor.getTime() <= end.getTime()) {
    if (isBusinessDayUtc(cursor)) count += 1;
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return count;
}

export function formatMonthTickPt(date: Date): string {
  const month = MONTH_SHORT_PT[date.getUTCMonth()] ?? "";
  const year = String(date.getUTCFullYear()).slice(-2);
  return `${month} de ${year}`;
}

/**
 * Consumo médio diário (dias úteis) a partir do período histórico.
 * Se não houver datas de período, assume ~252 dias úteis/ano.
 */
export function resolveAverageDailyConsumption(
  periodConsumption: number,
  periodStart?: string | null,
  periodEnd?: string | null,
): number {
  const consumption = Math.max(Number(periodConsumption) || 0, 0);
  if (consumption <= 0) return 0;

  const start = periodStart ? parseIsoDate(periodStart) : null;
  const end = periodEnd ? parseIsoDate(periodEnd) : null;
  if (start && end) {
    const days = countBusinessDaysInclusive(start, end);
    if (days > 0) return consumption / days;
  }
  return consumption / 252;
}

/**
 * Entradas futuras de pedidos (SC7) por data.
 * Overdue aplica no as_of; unscheduled fica de fora.
 */
export function collectPurchaseInflowsByDate(
  items: SafetyStockProjectionLedgerEntry[],
  asOfDate: string,
): Map<string, number> {
  const byDate = new Map<string, number>();
  for (const entry of items) {
    if (entry.origin !== "purchase_order") continue;
    if (entry.date_status === "unscheduled" || (!entry.event_date && entry.date_status !== "overdue")) {
      continue;
    }
    const key =
      entry.date_status === "overdue" || !entry.event_date ? asOfDate : entry.event_date;
    if (!parseIsoDate(key)) continue;
    byDate.set(key, (byDate.get(key) ?? 0) + Math.max(Number(entry.inflow) || 0, 0));
  }
  return byDate;
}

export function buildBalanceTimelineSeries(
  items: SafetyStockProjectionLedgerEntry[],
  summary: Pick<SafetyStockProjectionSummary, "as_of_date" | "initial_balance">,
  options: {
    periodConsumption?: number;
    periodStart?: string | null;
    periodEnd?: string | null;
    averageDailyConsumption?: number | null;
    calendarDays?: number;
    /** Quando false, ignora entradas SC7 (visão de ruptura sem pedidos). Default: true. */
    includePurchaseOrders?: boolean;
  } = {},
): BalanceTimelineSeries | null {
  const start = parseIsoDate(summary.as_of_date);
  if (!start) return null;

  const calendarDays = Math.max(
    1,
    Math.floor(options.calendarDays ?? BALANCE_TIMELINE_CALENDAR_DAYS),
  );
  const end = new Date(start.getTime());
  end.setUTCDate(end.getUTCDate() + calendarDays);

  const averageDaily =
    typeof options.averageDailyConsumption === "number" &&
    Number.isFinite(options.averageDailyConsumption) &&
    options.averageDailyConsumption > 0
      ? options.averageDailyConsumption
      : resolveAverageDailyConsumption(
          options.periodConsumption ?? 0,
          options.periodStart,
          options.periodEnd,
        );

  const includePurchases = options.includePurchaseOrders !== false;
  const inflows = includePurchases
    ? collectPurchaseInflowsByDate(items, summary.as_of_date)
    : new Map<string, number>();
  const points: BalanceTimelinePoint[] = [];
  let balance = Number(summary.initial_balance) || 0;
  let firstShortageDate: string | null = null;

  const cursor = new Date(start.getTime());
  while (cursor.getTime() <= end.getTime()) {
    const iso = formatIsoDateUtc(cursor);
    const business = isBusinessDayUtc(cursor);
    if (business && averageDaily > 0) {
      balance -= averageDaily;
    }
    const inflow = inflows.get(iso) ?? 0;
    if (inflow > 0) {
      balance += inflow;
    }

    const isShortage = balance < 0;
    if (isShortage && !firstShortageDate) {
      firstShortageDate = iso;
    }

    points.push({
      date: iso,
      monthTick: cursor.getUTCDate() === 1 ? formatMonthTickPt(cursor) : null,
      balance,
      balancePositive: balance >= 0 ? balance : 0,
      balanceNegative: balance < 0 ? balance : 0,
      isShortage,
      isBusinessDay: business,
    });

    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }

  // Garante tick no primeiro ponto se não for dia 1.
  if (points[0] && !points[0].monthTick) {
    points[0] = { ...points[0], monthTick: formatMonthTickPt(start) };
  }

  return {
    points,
    periodStart: formatIsoDateUtc(start),
    periodEnd: formatIsoDateUtc(end),
    averageDailyConsumption: averageDaily,
    firstShortageDate,
  };
}
