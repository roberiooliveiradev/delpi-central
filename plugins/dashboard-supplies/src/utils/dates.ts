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

/** Ex.: 31 de maio de 2026 */
export function formatDisplayDateLong(value: string | null | undefined): string {
  const parts = parseDateParts(value);
  if (!parts) {
    const short = formatDisplayDate(value);
    return short === "—" ? "—" : short;
  }
  const date = new Date(parts.year, parts.month - 1, parts.day);
  if (Number.isNaN(date.getTime())) return formatDisplayDate(value);
  return date.toLocaleDateString("pt-BR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

/** Ex.: 1 a 31 de maio de 2026 (mesmo mês) ou 1 de abr. — 15 de mai. de 2026 */
export function formatPeriodLabelLong(
  dateStart?: string,
  dateEnd?: string
): string {
  if (!dateStart && !dateEnd) return "Período não filtrado";
  const startParts = parseDateParts(dateStart);
  const endParts = parseDateParts(dateEnd);
  if (startParts && endParts) {
    if (
      startParts.year === endParts.year &&
      startParts.month === endParts.month
    ) {
      const monthDate = new Date(startParts.year, startParts.month - 1, 1);
      const monthLabel = monthDate.toLocaleDateString("pt-BR", {
        month: "long",
        year: "numeric",
      });
      return `${startParts.day} a ${endParts.day} de ${monthLabel}`;
    }
    return `${formatDisplayDateLong(dateStart)} — ${formatDisplayDateLong(dateEnd)}`;
  }
  if (dateStart) return `A partir de ${formatDisplayDateLong(dateStart)}`;
  return `Até ${formatDisplayDateLong(dateEnd)}`;
}

/** Protheus YYYYMMDD ou ISO → data por extenso em pt-BR */
export function formatProtheusDateHuman(value?: string | null): string {
  const raw = (value ?? "").trim();
  if (!raw) return "—";
  if (/^\d{8}$/.test(raw)) {
    return formatDisplayDateLong(
      `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)}`
    );
  }
  return formatDisplayDateLong(raw);
}

/** Substitui tokens YYYYMMDD em textos da API por data por extenso */
export function humanizeProtheusDatesInText(text: string): string {
  return text.replace(/\b(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b/g, (match) =>
    formatProtheusDateHuman(match)
  );
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
