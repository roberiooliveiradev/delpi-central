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

export function getLastDayOfMonthInputValue(competence: string): string {
  const match = competence.match(/^(\d{4})-(\d{2})$/);
  if (!match) return "";

  const year = Number(match[1]);
  const month = Number(match[2]);
  const lastDay = new Date(year, month, 0).getDate();
  return `${match[1]}-${match[2]}-${String(lastDay).padStart(2, "0")}`;
}

/** Converte competência YYYY-MM no intervalo de datas do período. */
export function competenceToDateRange(
  competence: string,
  todayIso = new Date().toISOString().slice(0, 10)
): Pick<LinkedDateFilters, "dateStart" | "dateEnd"> {
  if (!isValidCompetence(competence)) {
    return { dateStart: "", dateEnd: "" };
  }

  const dateStart = `${competence}-01`;
  const lastDay = getLastDayOfMonthInputValue(competence);
  const dateEnd = competence === todayIso.slice(0, 7) ? todayIso : lastDay;
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

export function resolveLinkedDateFilters(input: {
  dateStart?: string;
  dateEnd?: string;
  competence?: string;
  defaultDateStart: string;
  defaultDateEnd: string;
}): LinkedDateFilters {
  const dateStart =
    input.dateStart && ISO_DATE_RE.test(input.dateStart)
      ? input.dateStart
      : input.defaultDateStart;
  const dateEnd =
    input.dateEnd && ISO_DATE_RE.test(input.dateEnd)
      ? input.dateEnd
      : input.defaultDateEnd;
  const competence =
    input.competence && isValidCompetence(input.competence)
      ? input.competence
      : "";

  if (competence) {
    const range = competenceToDateRange(competence);
    return { ...range, competence };
  }

  return {
    dateStart,
    dateEnd,
    competence: dateRangeToCompetence(dateStart, dateEnd),
  };
}

export function applyCompetenceChange(competence: string): LinkedDateFilters {
  if (!competence) {
    return { dateStart: "", dateEnd: "", competence: "" };
  }

  const range = competenceToDateRange(competence);
  return { ...range, competence };
}

export function applyDateStartChange(
  dateStart: string,
  dateEnd: string
): LinkedDateFilters {
  return {
    dateStart,
    dateEnd,
    competence: dateRangeToCompetence(dateStart, dateEnd),
  };
}

export function applyDateEndChange(
  dateStart: string,
  dateEnd: string
): LinkedDateFilters {
  return {
    dateStart,
    dateEnd,
    competence: dateRangeToCompetence(dateStart, dateEnd),
  };
}
