/**
 * Datas da Pesquisa de Satisfação — o backend envia ISO UTC; a UI exibe e edita no
 * fuso do Portal (America/Sao_Paulo, UTC-03:00 fixo desde 2019).
 * Apresentação apenas: a situação (agendada/aberta/encerrada) vem pronta da API.
 */
export const SURVEY_TIME_ZONE = "America/Sao_Paulo";
const SURVEY_UTC_OFFSET = "-03:00";

const DISPLAY_FORMATTER = new Intl.DateTimeFormat("pt-BR", {
  timeZone: SURVEY_TIME_ZONE,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const PARTS_FORMATTER = new Intl.DateTimeFormat("en-CA", {
  timeZone: SURVEY_TIME_ZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

function parseIso(value: string | null | undefined): Date | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatSurveyDateTime(value: string | null | undefined): string {
  const date = parseIso(value);
  return date ? DISPLAY_FORMATTER.format(date).replace(",", "") : "—";
}

export function formatSurveyPeriod(
  startsAt: string | null | undefined,
  endsAt: string | null | undefined,
): string {
  return `${formatSurveyDateTime(startsAt)} → ${formatSurveyDateTime(endsAt)}`;
}

/** Ano (fuso do Portal) de um instante ISO — usado no filtro «Ano». */
export function surveyYearOf(value: string | null | undefined): number | null {
  const date = parseIso(value);
  if (!date) return null;
  const year = Number(
    PARTS_FORMATTER.formatToParts(date).find((part) => part.type === "year")?.value,
  );
  return Number.isFinite(year) ? year : null;
}

/** ISO → valor de `<input type="datetime-local">` (yyyy-MM-ddTHH:mm). */
export function isoToLocalInput(value: string | null | undefined): string {
  const date = parseIso(value);
  if (!date) return "";
  const parts = Object.fromEntries(
    PARTS_FORMATTER.formatToParts(date).map((part) => [part.type, part.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

/** Valor de `<input type="datetime-local">` (fuso do Portal) → ISO UTC; null se inválido. */
export function localInputToIso(value: string): string | null {
  const trimmed = value.trim();
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(trimmed)) return null;
  const date = new Date(`${trimmed}:00${SURVEY_UTC_OFFSET}`);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}
