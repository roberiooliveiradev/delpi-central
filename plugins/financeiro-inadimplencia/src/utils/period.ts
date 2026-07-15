import type { PeriodFilter, PeriodFormState, PeriodPreset } from "../types/inadimplencia";
import { MAX_PERIOD_MONTHS } from "../types/inadimplencia";

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

function firstDayOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function addMonths(date: Date, months: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + months, 1);
}

export function monthsBetween(startIso: string, endExclusiveIso: string): number {
  const start = parseIsoDate(startIso);
  const end = parseIsoDate(endExclusiveIso);
  if (!start || !end) return 0;
  return (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
}

export function parseIsoDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);
  if (
    Number.isNaN(date.getTime()) ||
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null;
  }
  return date;
}

/** Últimos N meses fechados (sem o mês corrente). Mantido para casos explícitos. */
export function getLastCompleteMonthsRange(
  completeMonths: number,
  referenceDate = new Date(),
): { startDate: string; endDate: string } {
  const endExclusive = firstDayOfMonth(referenceDate);
  const start = addMonths(endExclusive, -completeMonths);
  return {
    startDate: formatIsoDate(start),
    endDate: formatIsoDate(endExclusive),
  };
}

/**
 * Mês civil corrente com fim exclusivo (dia 1 do próximo mês).
 */
export function getCurrentMonthRange(
  referenceDate = new Date(),
): { startDate: string; endDate: string } {
  const start = firstDayOfMonth(referenceDate);
  const endExclusive = addMonths(start, 1);
  return {
    startDate: formatIsoDate(start),
    endDate: formatIsoDate(endExclusive),
  };
}

/**
 * Últimos N meses incluindo o mês corrente (ainda incompleto).
 * Fim exclusivo = dia 1 do próximo mês.
 */
export function getLastMonthsRangeIncludingCurrent(
  months: number,
  referenceDate = new Date(),
): { startDate: string; endDate: string } {
  const endExclusive = addMonths(firstDayOfMonth(referenceDate), 1);
  const start = addMonths(endExclusive, -months);
  return {
    startDate: formatIsoDate(start),
    endDate: formatIsoDate(endExclusive),
  };
}

export function resolvePeriodPreset(
  preset: PeriodPreset,
  referenceDate = new Date(),
): { startDate: string; endDate: string } {
  const endOfCurrentMonthExclusive = addMonths(firstDayOfMonth(referenceDate), 1);

  switch (preset) {
    case "last_6_months":
      return getLastMonthsRangeIncludingCurrent(6, referenceDate);
    case "last_12_months":
      return getLastMonthsRangeIncludingCurrent(12, referenceDate);
    case "current_year":
      return {
        startDate: formatIsoDate(new Date(referenceDate.getFullYear(), 0, 1)),
        endDate: formatIsoDate(endOfCurrentMonthExclusive),
      };
    case "previous_year":
      return {
        startDate: formatIsoDate(new Date(referenceDate.getFullYear() - 1, 0, 1)),
        endDate: formatIsoDate(new Date(referenceDate.getFullYear(), 0, 1)),
      };
    case "custom":
    default:
      return getLastMonthsRangeIncludingCurrent(12, referenceDate);
  }
}

export function createDefaultPeriodFormState(referenceDate = new Date()): PeriodFormState {
  const range = resolvePeriodPreset("last_12_months", referenceDate);
  return {
    preset: "last_12_months",
    startDate: range.startDate,
    endDate: range.endDate,
  };
}

export function periodFilterFromForm(state: PeriodFormState): PeriodFilter {
  // Envia datas explícitas para incluir o mês corrente (o default da API exclui).
  return {
    startDate: state.startDate,
    endDate: state.endDate,
  };
}

export function validatePeriodRange(startDate: string, endDate: string): string | null {
  const start = parseIsoDate(startDate);
  const end = parseIsoDate(endDate);
  if (!start || !end) {
    return "Informe datas válidas no formato AAAA-MM-DD.";
  }
  if (start >= end) {
    return "A data inicial deve ser anterior ao limite final exclusivo.";
  }
  const span = monthsBetween(startDate, endDate);
  if (span > MAX_PERIOD_MONTHS) {
    return `O período máximo permitido é de ${MAX_PERIOD_MONTHS} meses.`;
  }
  return null;
}

export function formatPeriodLabel(state: PeriodFormState): string {
  switch (state.preset) {
    case "last_6_months":
      return "Últimos 6 meses (com mês atual)";
    case "last_12_months":
      return "Últimos 12 meses (com mês atual)";
    case "current_year":
      return "Ano atual (com mês corrente)";
    case "previous_year":
      return "Ano anterior";
    case "custom":
      return `${state.startDate} → ${state.endDate} (fim exclusivo)`;
    default:
      return "Período";
  }
}
