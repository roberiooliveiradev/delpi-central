const EMPTY = "—";

/** ISO YYYY-MM-DD → dd/MM/yyyy, sem construir Date (evita salto de fuso). */
export function formatIsoDate(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (text.length < 10) return EMPTY;
  const [year, month, day] = text.slice(0, 10).split("-");
  if (!year || !month || !day) return EMPTY;
  return `${day}/${month}/${year}`;
}

/** ISO YYYY-MM-DD → dd/MM, para colunas densas. */
export function formatIsoDayMonth(value: string | null | undefined): string {
  const formatted = formatIsoDate(value);
  return formatted === EMPTY ? EMPTY : formatted.slice(0, 5);
}
