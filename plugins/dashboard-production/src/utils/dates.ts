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
  if (!value?.trim()) return "—";

  const trimmed = value.trim();

  const isoMatch = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoMatch) {
    return `${isoMatch[3]}/${isoMatch[2]}/${isoMatch[1]}`;
  }

  const compactMatch = trimmed.match(/^(\d{4})(\d{2})(\d{2})$/);
  if (compactMatch) {
    return `${compactMatch[3]}/${compactMatch[2]}/${compactMatch[1]}`;
  }

  if (/^\d{2}\/\d{2}\/\d{4}$/.test(trimmed)) {
    return trimmed;
  }

  return trimmed;
}

export function formatDisplayTime(value: string | null | undefined): string {
  if (!value?.trim()) return "—";

  const trimmed = value.trim();
  const embeddedDateMatch = trimmed.match(/^\d{8}\s+(.+)$/);
  const timePart = embeddedDateMatch ? embeddedDateMatch[1].trim() : trimmed;

  const clockMatch = timePart.match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/);
  if (clockMatch) {
    return `${clockMatch[1].padStart(2, "0")}:${clockMatch[2]}`;
  }

  const compactMatch = timePart.match(/^(\d{2})(\d{2})(\d{2})?$/);
  if (compactMatch) {
    return `${compactMatch[1]}:${compactMatch[2]}`;
  }

  return timePart;
}

export function formatAppointmentDateTime(
  date?: string | null,
  time?: string | null
): string {
  const trimmedTime = time?.trim();
  const embeddedDateMatch = trimmedTime?.match(/^(\d{8})\s+(.+)$/);

  const dateLabel = embeddedDateMatch
    ? formatDisplayDate(embeddedDateMatch[1])
    : formatDisplayDate(date);
  const timeLabel = formatDisplayTime(trimmedTime);

  if (dateLabel === "—" && timeLabel === "—") return "—";
  if (timeLabel === "—") return dateLabel;
  if (dateLabel === "—") return timeLabel;
  return `${dateLabel} ${timeLabel}`;
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
