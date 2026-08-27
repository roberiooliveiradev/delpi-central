/** Detecta conteúdo HTML vazio (só tags vazias ou &nbsp;). */
export function isHtmlEmpty(html: string | null | undefined): boolean {
  const raw = (html || "")
    .replace(/<br\s*\/?>/gi, "")
    .replace(/<p>\s*<\/p>/gi, "")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/gi, " ")
    .trim();
  return raw.length === 0;
}

const NBSP_RUN_RE = /[ \t]*(?:(?:&nbsp;|&#0*160;|\u00a0)[ \t]*){2,}/gi;

/** Colapsa runs de `&nbsp;` (artefato de colagem do Word) em um espaço comum. */
export function collapseNbspRuns(html: string | null | undefined): string {
  return (html || "").replace(NBSP_RUN_RE, " ");
}

export function formatDateBr(isoDate: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(isoDate);
  if (!match) return isoDate;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

const MONTHS = [
  "",
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
];

export function formatMeetingDateLong(value: unknown): string {
  const raw = String(value || "").slice(0, 10);
  const [year, month, day] = raw.split("-").map(Number);
  if (!year || !month || !day || !MONTHS[month]) return "data não informada";
  return `${day} de ${MONTHS[month]} de ${year}`;
}

export function unitCityLabel(unitCode: string): string {
  if (unitCode === "01") return "Jaraguá do Sul - SC";
  return unitCode || "—";
}
