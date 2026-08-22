import { EMPTY_VALUE } from "./formatNumbers";

const MONTH_ABBR_PT = [
  "Jan",
  "Fev",
  "Mar",
  "Abr",
  "Mai",
  "Jun",
  "Jul",
  "Ago",
  "Set",
  "Out",
  "Nov",
  "Dez",
] as const;

/** Datas do TOTVS chegam como `AAAA-MM-DD`, `AAAAMMDD` ou `DD/MM/AAAA`. */
export function formatIsoDate(value: string | null | undefined): string {
  const text = value?.trim() ?? "";
  if (!text) return EMPTY_VALUE;
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(text);
  if (iso) return `${iso[3]}/${iso[2]}/${iso[1]}`;
  const protheus = /^(\d{4})(\d{2})(\d{2})$/.exec(text);
  if (protheus) return `${protheus[3]}/${protheus[2]}/${protheus[1]}`;
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(text)) return text;
  return text;
}

/** Rótulo de emissão da API pode vir em ISO — normaliza para exibição pt-BR. */
export function formatIssueDate(
  issueDate: string | null | undefined,
  issueDateLabel?: string | null,
): string {
  return formatIsoDate(issueDateLabel || issueDate);
}

/** `2026-08` ou `202608` vira `Ago/2026` — eixo de série mensal. */
export function formatYearMonth(value: string | null | undefined): string {
  const text = value?.trim() ?? "";
  if (!text) return EMPTY_VALUE;

  const iso = /^(\d{4})-(\d{2})$/.exec(text);
  const compact = /^(\d{4})(\d{2})$/.exec(text);
  const year = Number(iso?.[1] ?? compact?.[1]);
  const month = Number(iso?.[2] ?? compact?.[2]);

  if (!Number.isFinite(year) || !Number.isFinite(month) || month < 1 || month > 12) {
    return text;
  }

  return `${MONTH_ABBR_PT[month - 1]}/${year}`;
}

export function formatPeriodRange(
  startDate: string | null | undefined,
  endDate: string | null | undefined,
): string | null {
  const start = startDate?.trim();
  const end = endDate?.trim();
  if (!start && !end) return null;
  if (start && end) return `${formatIsoDate(start)} a ${formatIsoDate(end)}`;
  return formatIsoDate(start || end);
}
