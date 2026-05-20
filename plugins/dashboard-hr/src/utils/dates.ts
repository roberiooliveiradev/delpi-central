/** Converte YYYY-MM-DD (input date) para DD-MM-YYYY (Portal RH / api-delpi /hr). */
export function inputDateToApi(value: string | undefined): string | undefined {
  if (!value) return undefined;

  const trimmed = value.trim();
  const isoMatch = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoMatch) {
    return `${isoMatch[3]}-${isoMatch[2]}-${isoMatch[1]}`;
  }

  return trimmed;
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
