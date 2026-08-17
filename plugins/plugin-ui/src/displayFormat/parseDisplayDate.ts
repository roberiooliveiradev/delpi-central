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

  /* dd/mm/yyyy ou d/m/yyyy (pt-BR) — sem Date.parse (evita ambiguidade US). */
  const br = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(text);
  if (br) {
    const day = Number(br[1]);
    const month = Number(br[2]);
    const year = Number(br[3]);
    if (month < 1 || month > 12 || day < 1 || day > 31) return null;
    return { year, month: month - 1, day, hour: 0, minute: 0, second: 0, dateOnly: true };
  }

  /*
   * Rótulo de bucket mensal da API («Jan. de 26», «Fev. de 2026»).
   * Nunca cair em Date.parse: «Jan. de 26» vira 26/01/2001 no motor ECMA.
   */
  const monthDe = parseLocalizedMonthYearLabel(text);
  if (monthDe) return monthDe;

  /*
   * Sem Date.parse em texto livre: abreviações EN ambíguas («Jan», «Mar», «Jun»)
   * e rótulos PT («Fev») produzem NaN ou datas fantasmas (ano 2001).
   */
  return null;
}

const MONTH_ABBREV_PARSE: Record<string, number> = {
  jan: 0,
  fev: 1,
  feb: 1,
  mar: 2,
  abr: 3,
  apr: 3,
  mai: 4,
  may: 4,
  jun: 5,
  jul: 6,
  ago: 7,
  aug: 7,
  set: 8,
  sep: 8,
  sept: 8,
  out: 9,
  oct: 9,
  nov: 10,
  dez: 11,
  dec: 11,
};

/** True para rótulos já humanizados pela API (série mensal / legado EN). */
export function isLocalizedChartPeriodLabel(raw: string): boolean {
  return Boolean(parseLocalizedMonthYearLabel(raw.trim()));
}

const EN_MONTH_TO_PT_LABEL: Record<string, string> = {
  jan: "Jan",
  feb: "Fev",
  mar: "Mar",
  apr: "Abr",
  may: "Mai",
  jun: "Jun",
  jul: "Jul",
  aug: "Ago",
  sep: "Set",
  sept: "Set",
  oct: "Out",
  nov: "Nov",
  dec: "Dez",
};

/** Troca abreviações EN remanescentes (ex.: cache antigo «Feb. de 26»). */
export function localizeEnglishMonthTokensInLabel(raw: string): string {
  return raw.replace(
    /\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b(\.)?/gi,
    (_match, month: string, dot: string | undefined) => {
      const key = String(month).toLowerCase();
      const pt = EN_MONTH_TO_PT_LABEL[key] ?? month;
      return `${pt}${dot ?? ""}`;
    },
  );
}

function parseLocalizedMonthYearLabel(text: string): ParsedDisplayDate | null {
  const match =
    /^(jan|fev|feb|mar|abr|apr|mai|may|jun|jul|ago|aug|set|sep|sept|out|oct|nov|dez|dec)\.?\s+de\s+(\d{2}|\d{4})$/i.exec(
      text,
    );
  if (!match) return null;
  const month = MONTH_ABBREV_PARSE[match[1]!.toLowerCase()];
  if (month == null) return null;
  let year = Number(match[2]);
  if (!Number.isFinite(year)) return null;
  if (year < 100) year += 2000;
  return { year, month, day: 1, hour: 0, minute: 0, second: 0, dateOnly: true };
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
