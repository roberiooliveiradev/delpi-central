const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const COMPETENCE_RE = /^\d{4}-\d{2}$/;

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

/** Converte competência YYYY-MM no intervalo de datas do período. */
export function competenceToDateRange(
  competence: string,
  todayIso = new Date().toISOString().slice(0, 10)
): { dataInicial: string; dataFinal: string } {
  if (!isValidCompetence(competence)) {
    return { dataInicial: "", dataFinal: "" };
  }
  const dataInicial = `${competence}-01`;
  const dataFinal =
    competence === todayIso.slice(0, 7) ? todayIso : lastDayOfMonth(competence);
  return { dataInicial, dataFinal };
}

/** Deriva competência do período; vazio quando o intervalo cruza meses. */
export function dateRangeToCompetence(dataInicial: string, dataFinal: string): string {
  if (!ISO_DATE_RE.test(dataInicial) || !ISO_DATE_RE.test(dataFinal)) {
    return "";
  }
  const startMonth = dataInicial.slice(0, 7);
  const endMonth = dataFinal.slice(0, 7);
  if (startMonth !== endMonth) return "";
  return startMonth;
}
