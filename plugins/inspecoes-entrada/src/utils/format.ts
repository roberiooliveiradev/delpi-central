export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toLocaleString("pt-BR");
}

export function formatText(value: string | null | undefined): string {
  const normalized = value?.trim();
  return normalized ? normalized : "—";
}

export function formatBoolean(value: boolean): string {
  return value ? "Sim" : "Não";
}

export function formatPercent(value: number): string {
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

export function formatAverageTime(days: number, hours: number): string {
  const daysLabel = days.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const hoursLabel = hours.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
  return `${daysLabel} d (${hoursLabel} h)`;
}

export function formatDatePt(date: string | null | undefined): string {
  const normalizedDate = date?.trim();
  if (!normalizedDate) return "—";

  const [year, month, day] = normalizedDate.split("-");
  if (year && month && day) {
    return `${day.padStart(2, "0")}/${month.padStart(2, "0")}/${year}`;
  }

  return normalizedDate;
}

export function formatDateTimePt(date: string | null | undefined, time?: string | null): string {
  const dateLabel = formatDatePt(date);
  if (dateLabel === "—") return dateLabel;

  const normalizedTime = time?.trim();
  return normalizedTime ? `${dateLabel} às ${normalizedTime}` : dateLabel;
}
