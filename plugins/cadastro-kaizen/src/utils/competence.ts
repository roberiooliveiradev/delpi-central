const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const COMPETENCE_RE = /^\d{4}-\d{2}$/;

export type LinkedDateFilters = {
  dateStart: string;
  dateEnd: string;
  competence: string;
};

export function isValidCompetence(value: string): boolean {
  return COMPETENCE_RE.test(value);
}

function lastDayOfMonth(competence: string): string {
  const match = competence.match(/^(\d{4})-(\d{2})$/);
  if (!match) return "";
  const year = Number(match[1]);
  const month = Number(match[2]);
  const lastDay = new Date(year, month, 0).getDate();
  return `${match[1]}-${match[2]}-${String(lastDay).padStart(2, "0")}`;
}

/** Converte competência YYYY-MM no intervalo de datas do período (mês corrente encerra hoje). */
export function competenceToDateRange(
  competence: string,
  todayIso = new Date().toISOString().slice(0, 10),
): Pick<LinkedDateFilters, "dateStart" | "dateEnd"> {
  if (!isValidCompetence(competence)) {
    return { dateStart: "", dateEnd: "" };
  }
  const dateStart = `${competence}-01`;
  const dateEnd = competence === todayIso.slice(0, 7) ? todayIso : lastDayOfMonth(competence);
  return { dateStart, dateEnd };
}

/** Deriva competência do período; vazio quando o intervalo cruza meses. */
export function dateRangeToCompetence(dateStart: string, dateEnd: string): string {
  if (!ISO_DATE_RE.test(dateStart) || !ISO_DATE_RE.test(dateEnd)) {
    return "";
  }
  const startMonth = dateStart.slice(0, 7);
  const endMonth = dateEnd.slice(0, 7);
  if (startMonth !== endMonth) return "";
  return startMonth;
}

export function applyCompetenceChange(competence: string): LinkedDateFilters {
  if (!competence) {
    return { dateStart: "", dateEnd: "", competence: "" };
  }
  const range = competenceToDateRange(competence);
  return { ...range, competence };
}

export function applyDateRangeChange(dateStart: string, dateEnd: string): LinkedDateFilters {
  return {
    dateStart,
    dateEnd,
    competence: dateRangeToCompetence(dateStart, dateEnd),
  };
}

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

/** Hoje em YYYY-MM-DD (horário local). */
export function todayInputValue(reference = new Date()): string {
  return `${reference.getFullYear()}-${pad2(reference.getMonth() + 1)}-${pad2(reference.getDate())}`;
}

/** Primeiro dia do mês corrente em YYYY-MM-DD (horário local). */
export function firstDayOfMonthInputValue(reference = new Date()): string {
  return `${reference.getFullYear()}-${pad2(reference.getMonth() + 1)}-01`;
}

/**
 * Resolve o estado inicial dos filtros de data. Prioriza competência salva, depois
 * intervalo salvo e, na ausência de ambos, usa o mês vigente como padrão — igual ao
 * dashboard-quality.
 */
export function resolveLinkedDateFilters(input: {
  dateStart?: string;
  dateEnd?: string;
  competence?: string;
  defaultDateStart?: string;
  defaultDateEnd?: string;
}): LinkedDateFilters {
  if (input.competence && isValidCompetence(input.competence)) {
    return applyCompetenceChange(input.competence);
  }

  const defaultStart = input.defaultDateStart ?? firstDayOfMonthInputValue();
  const defaultEnd = input.defaultDateEnd ?? todayInputValue();

  const dateStart =
    input.dateStart && ISO_DATE_RE.test(input.dateStart) ? input.dateStart : defaultStart;
  const dateEnd = input.dateEnd && ISO_DATE_RE.test(input.dateEnd) ? input.dateEnd : defaultEnd;

  return { dateStart, dateEnd, competence: dateRangeToCompetence(dateStart, dateEnd) };
}
