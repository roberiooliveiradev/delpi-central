const DATE_FMT = new Intl.DateTimeFormat("pt-BR");

const AMOUNT_FMT = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const QUANTITY_FMT = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 4,
});

/**
 * Formata data civil `YYYY-MM-DD` sem deslocamento de fuso — interpreta
 * os componentes no calendário local (`new Date(y, m, d)`), não em UTC.
 */
export function formatCivilDate(iso: string | null): string {
  if (!iso) return "—";
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  if (!y || !m || !d) return iso;
  return DATE_FMT.format(new Date(y, m - 1, d));
}

export function formatAmount(raw: string): string {
  const value = Number(raw);
  return Number.isFinite(value) ? AMOUNT_FMT.format(value) : raw;
}

export function formatQuantity(raw: string): string {
  const value = Number(raw);
  return Number.isFinite(value) ? QUANTITY_FMT.format(value) : raw;
}
