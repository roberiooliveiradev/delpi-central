const YEAR_MONTH = /^(\d{4})-(0[1-9]|1[0-2])$/;
/** A série de despesas chega do TOTVS como `AAAAMM` (`LEFT(data_emissao, 6)`). */
const YEAR_MONTH_COMPACT = /^(\d{4})(0[1-9]|1[0-2])$/;

export type MonthPeriod = {
  startDate: string;
  endDate: string;
};

export function isYearMonth(value: string | null | undefined): boolean {
  return YEAR_MONTH.test(value?.trim() ?? "");
}

function parts(value: string | null | undefined): { year: number; month: number } | null {
  const text = value?.trim() ?? "";
  const match = YEAR_MONTH.exec(text) ?? YEAR_MONTH_COMPACT.exec(text);
  if (!match) return null;
  return { year: Number(match[1]), month: Number(match[2]) };
}

/** Converte `AAAAMM` ou `AAAA-MM` na forma canônica da URL (`AAAA-MM`). */
export function normalizeYearMonth(value: string | null | undefined): string | null {
  const parsed = parts(value);
  if (!parsed) return null;
  return `${parsed.year}-${pad(parsed.month)}`;
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/** Intervalo calendário fechado do mês — `Date.UTC(y, m, 0)` entrega o último dia. */
export function monthPeriodRange(value: string | null | undefined): MonthPeriod | null {
  const parsed = parts(value);
  if (!parsed) return null;
  const lastDay = new Date(Date.UTC(parsed.year, parsed.month, 0)).getUTCDate();
  const prefix = `${parsed.year}-${pad(parsed.month)}`;
  return { startDate: `${prefix}-01`, endDate: `${prefix}-${pad(lastDay)}` };
}

export function previousYearMonth(value: string | null | undefined): string | null {
  const parsed = parts(value);
  if (!parsed) return null;
  const year = parsed.month === 1 ? parsed.year - 1 : parsed.year;
  const month = parsed.month === 1 ? 12 : parsed.month - 1;
  return `${year}-${pad(month)}`;
}
