const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const integerFormatter = new Intl.NumberFormat("pt-BR");

const decimalFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 4,
});

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

export function formatCurrencyBrl(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return currencyFormatter.format(0);
  return currencyFormatter.format(value);
}

export function formatInteger(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return integerFormatter.format(0);
  return integerFormatter.format(value);
}

/** Quantidade já convertida pela API (MI → UN). Apenas formatação de exibição. */
export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return decimalFormatter.format(0);
  return decimalFormatter.format(value);
}

export function formatDatePtBr(value: string | null | undefined): string {
  if (!value) return "—";
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(value.trim());
  if (iso) {
    const date = new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]));
    if (!Number.isNaN(date.getTime())) return dateFormatter.format(date);
  }
  return value;
}

/** Data Protheus AAAAMMDD → DD/MM/AAAA. */
export function formatProtheusDate(value: string | null | undefined): string {
  if (!value) return "—";
  const raw = value.trim();
  const match = /^(\d{4})(\d{2})(\d{2})$/.exec(raw);
  if (match) {
    const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
    if (!Number.isNaN(date.getTime())) return dateFormatter.format(date);
  }
  return formatDatePtBr(raw);
}

/** Hora Protheus (HHMM, HHMMSS ou HH:MM[:SS]) → HH:MM. */
export function formatProtheusTime(value: string | null | undefined): string {
  if (!value) return "";
  const raw = value.trim();
  if (!raw) return "";
  const colon = /^(\d{1,2}):(\d{2})(?::\d{2})?$/.exec(raw);
  if (colon) {
    return `${colon[1].padStart(2, "0")}:${colon[2]}`;
  }
  const digits = raw.replace(/\D/g, "");
  if (digits.length >= 4) {
    return `${digits.slice(0, 2)}:${digits.slice(2, 4)}`;
  }
  return raw;
}

/** Data do apontamento + intervalo de horário (início–fim) quando existir. */
export function formatAppointmentDateTime(row: {
  appointment_date?: string | null;
  start_time?: string | null;
  end_time?: string | null;
}): string {
  const date = formatProtheusDate(row.appointment_date);
  const start = formatProtheusTime(row.start_time);
  const end = formatProtheusTime(row.end_time);
  if (!start && !end) return date;
  if (start && end && start !== end) return `${date} ${start}–${end}`;
  return `${date} ${start || end}`;
}

/** Chave de ordenação data+hora (AAAAMMDDHHMM). */
export function appointmentDateTimeSortKey(row: {
  appointment_date?: string | null;
  start_time?: string | null;
}): string {
  const date = (row.appointment_date ?? "").trim().replace(/\D/g, "").padEnd(8, "0").slice(0, 8);
  const hhmm = formatProtheusTime(row.start_time).replace(":", "");
  return `${date}${(hhmm || "0000").padStart(4, "0").slice(0, 4)}`;
}

export function formatOperatorLabel(row: {
  operator_name?: string | null;
  operator_code?: string | null;
}): string {
  const name = (row.operator_name ?? "").trim();
  const code = (row.operator_code ?? "").trim();
  if (name && code) return `${name} (${code})`;
  return name || code || "—";
}

export function formatResourceLabel(row: {
  resource?: string | null;
  resource_name?: string | null;
}): string {
  const code = (row.resource ?? "").trim();
  const name = (row.resource_name ?? "").trim();
  if (code && name) return `${code} — ${name}`;
  return code || name || "—";
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${decimalFormatter.format(value)}%`;
}

export function formatShortLabel(value: string | null | undefined, maxLength = 18): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}…`;
}
