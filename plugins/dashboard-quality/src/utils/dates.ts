/** Converte valor do input date (YYYY-MM-DD) para a API (mesmo formato aceito pelo backend). */
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

export function formatPeriodLabel(
  dateStart?: string,
  dateEnd?: string
): string {
  if (!dateStart && !dateEnd) return "Período não filtrado";
  if (dateStart && dateEnd) return `${dateStart} → ${dateEnd}`;
  if (dateStart) return `A partir de ${dateStart}`;
  return `Até ${dateEnd}`;
}

/** Exibe data Protheus (YYYYMMDD) ou ISO (YYYY-MM-DD). */
export function formatDisplayDate(value: string | null | undefined): string {
  if (!value) return "—";

  const normalized = value.replaceAll("-", "");
  if (normalized.length !== 8) return value;

  const year = normalized.slice(0, 4);
  const month = normalized.slice(4, 6);
  const day = normalized.slice(6, 8);
  return `${day}/${month}/${year}`;
}

export function protheusDateToMonthKey(value: string | null | undefined): string | null {
  if (!value) return null;

  const normalized = value.replaceAll("-", "");
  if (normalized.length < 6) return null;

  return `${normalized.slice(0, 4)}-${normalized.slice(4, 6)}`;
}

export function monthKeyToLabel(monthKey: string): string {
  const [year, month] = monthKey.split("-");
  const date = new Date(Number(year), Number(month) - 1, 1);

  return date.toLocaleDateString("pt-BR", {
    month: "short",
    year: "2-digit",
  });
}
