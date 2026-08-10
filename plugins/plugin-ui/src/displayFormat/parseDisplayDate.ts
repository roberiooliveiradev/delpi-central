import type { ParsedDisplayDate } from "./types";

const MONTH_ABBREV_PT = [
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

const MONTH_FULL_PT = [
  "janeiro",
  "fevereiro",
  "março",
  "abril",
  "maio",
  "junho",
  "julho",
  "agosto",
  "setembro",
  "outubro",
  "novembro",
  "dezembro",
] as const;

const WEEKDAY_FULL_PT = [
  "domingo",
  "segunda-feira",
  "terça-feira",
  "quarta-feira",
  "quinta-feira",
  "sexta-feira",
  "sábado",
] as const;

export function monthAbbrevPt(monthIndex0: number, capitalize = true): string {
  const abbrev = MONTH_ABBREV_PT[((monthIndex0 % 12) + 12) % 12]!;
  return capitalize ? `${abbrev[0]!.toUpperCase()}${abbrev.slice(1)}` : abbrev;
}

export function monthFullPt(monthIndex0: number): string {
  return MONTH_FULL_PT[((monthIndex0 % 12) + 12) % 12]!;
}

export function weekdayFullPt(year: number, month: number, day: number): string {
  const utc = Date.UTC(year, month, day);
  const weekday = new Date(utc).getUTCDay();
  return WEEKDAY_FULL_PT[weekday] ?? "";
}

/**
 * Data-only ISO (`YYYY-MM-DD`, `YYYY-MM`) = calendário UTC (sem timezone local).
 * Datetime com hora/offset = instante real; partes de calendário ainda em UTC se só a data for formatada.
 */
export function parseDisplayDate(raw: unknown): ParsedDisplayDate | null {
  if (raw instanceof Date && Number.isFinite(raw.getTime())) {
    return fromInstant(raw);
  }
  if (typeof raw === "number" && Number.isFinite(raw)) {
    return fromInstant(new Date(raw));
  }
  if (typeof raw !== "string") return null;
  const text = raw.trim();
  if (!text) return null;

  const ym = /^(\d{4})-(\d{2})$/.exec(text);
  if (ym) {
    const year = Number(ym[1]);
    const month = Number(ym[2]);
    if (month < 1 || month > 12) return null;
    return { year, month: month - 1, day: 1, hour: 0, minute: 0, second: 0, dateOnly: true };
  }

  const ymd = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (ymd) {
    const year = Number(ymd[1]);
    const month = Number(ymd[2]);
    const day = Number(ymd[3]);
    if (month < 1 || month > 12 || day < 1 || day > 31) return null;
    return { year, month: month - 1, day, hour: 0, minute: 0, second: 0, dateOnly: true };
  }

  const ymdTime = /^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?$/.exec(
    text,
  );
  if (ymdTime) {
    const hasZone = Boolean(ymdTime[7]);
    if (hasZone) {
      const parsed = Date.parse(text);
      if (!Number.isFinite(parsed)) return null;
      return fromInstant(new Date(parsed));
    }
    return {
      year: Number(ymdTime[1]),
      month: Number(ymdTime[2]) - 1,
      day: Number(ymdTime[3]),
      hour: Number(ymdTime[4]),
      minute: Number(ymdTime[5]),
      second: Number(ymdTime[6] ?? 0),
      dateOnly: false,
    };
  }

  const parsed = Date.parse(text);
  if (!Number.isFinite(parsed)) return null;
  return fromInstant(new Date(parsed));
}

function fromInstant(date: Date): ParsedDisplayDate {
  return {
    year: date.getUTCFullYear(),
    month: date.getUTCMonth(),
    day: date.getUTCDate(),
    hour: date.getUTCHours(),
    minute: date.getUTCMinutes(),
    second: date.getUTCSeconds(),
    dateOnly: false,
  };
}
