const DATE_FMT = new Intl.DateTimeFormat("pt-BR");

const DATETIME_FMT = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
});

const AMOUNT_FMT = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const QUANTITY_FMT = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 4,
});

const SHARE_FMT = new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 1,
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

/** Data+hora ISO em pt-BR; vazio quando nulo. */
export function formatDateTime(iso: string | null): string {
  return iso ? DATETIME_FMT.format(new Date(iso)) : "";
}

export function formatAmount(raw: string): string {
  const value = Number(raw);
  return Number.isFinite(value) ? AMOUNT_FMT.format(value) : raw;
}

export function formatQuantity(raw: string): string {
  const value = Number(raw);
  return Number.isFinite(value) ? QUANTITY_FMT.format(value) : raw;
}

/** Participação `part/total` em % pt-BR; null quando o total não existe. */
export function formatSharePercent(
  part: string,
  total: string | null,
): string | null {
  const p = Number(part);
  const t = total === null ? NaN : Number(total);
  if (!Number.isFinite(p) || !Number.isFinite(t) || t <= 0) return null;
  return `${SHARE_FMT.format((p / t) * 100)}%`;
}
