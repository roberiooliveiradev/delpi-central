export function inputDateToApi(value: string | undefined): string | undefined {
  if (!value) return undefined;
  return value;
}

export function getTodayInputValue(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function getFirstDayOfMonthInputValue(reference = new Date()): string {
  const year = reference.getFullYear();
  const month = String(reference.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}-01`;
}

export function formatDisplayDate(value: string | null | undefined): string {
  if (!value) return "—";
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return value;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function monthKeyToLabel(monthKey: string): string {
  const match = monthKey.match(/^(\d{4})-(\d{2})$/);
  if (!match) return monthKey;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const date = new Date(year, month - 1, 1);

  if (Number.isNaN(date.getTime())) return monthKey;

  return date.toLocaleDateString("pt-BR", {
    month: "short",
    year: "2-digit",
  });
}

export function formatPeriodLabel(
  dateStart?: string,
  dateEnd?: string
): string {
  if (!dateStart && !dateEnd) return "Período não filtrado";
  if (dateStart && dateEnd) {
    return `${formatDisplayDate(dateStart)} — ${formatDisplayDate(dateEnd)}`;
  }
  if (dateStart) return `A partir de ${formatDisplayDate(dateStart)}`;
  return `Até ${formatDisplayDate(dateEnd)}`;
}

export type DateParts = {
  year: number;
  month: number;
  day: number;
};

function isValidDateParts(year: number, month: number, day: number): boolean {
  if (!Number.isFinite(year) || year < 1900 || year > 2100) return false;
  if (!Number.isFinite(month) || month < 1 || month > 12) return false;
  if (!Number.isFinite(day) || day < 1 || day > 31) return false;
  return true;
}

/** Interpreta datas da API (YYYY-MM-DD, YYYYMMDD, dd/MM/yyyy). */
export function parseDateParts(
  value: string | null | undefined
): DateParts | null {
  if (!value) return null;

  const trimmed = value.trim();
  if (!trimmed) return null;

  const brSlash = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/);
  if (brSlash) {
    const day = Number(brSlash[1]);
    const month = Number(brSlash[2]);
    let year = Number(brSlash[3]);
    if (year < 100) year += 2000;

    if (!isValidDateParts(year, month, day)) return null;
    return { year, month, day };
  }

  const digits = trimmed.replace(/\D/g, "");
  if (digits.length >= 8) {
    const year = Number(digits.slice(0, 4));
    const month = Number(digits.slice(4, 6));
    const day = Number(digits.slice(6, 8));

    if (!isValidDateParts(year, month, day)) return null;
    return { year, month, day };
  }

  if (digits.length === 6) {
    const year = Number(digits.slice(0, 4));
    const month = Number(digits.slice(4, 6));

    if (!isValidDateParts(year, month, 1)) return null;
    return { year, month, day: 1 };
  }

  return null;
}

export function dateToMonthKey(value: string | null | undefined): string | null {
  const parts = parseDateParts(value);
  if (!parts) return null;

  return `${parts.year}-${String(parts.month).padStart(2, "0")}`;
}

export function lmpDateToIso(value: string | null | undefined): string | null {
  const parts = parseDateParts(value);
  if (!parts) return null;

  return `${parts.year}-${String(parts.month).padStart(2, "0")}-${String(parts.day).padStart(2, "0")}`;
}
