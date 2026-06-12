export function toDatetimeLocalValue(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (part: number) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function toBrDateDisplay(value: string | Date): string {
  const isoDate =
    value instanceof Date
      ? toDateInputValue(value)
      : value.includes("T")
        ? value.slice(0, 10)
        : value.slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(isoDate)) return "";
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

export function parseBrDateDisplay(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return "";

  const match = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (!match) return null;

  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = Number(match[3]);
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;

  const date = new Date(year, month - 1, day);
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null;
  }

  const pad = (part: number) => String(part).padStart(2, "0");
  return `${pad(year)}-${pad(month)}-${pad(day)}`;
}

export function toBrDatetimeDisplay(value: string | Date): string {
  const localValue = value instanceof Date ? toDatetimeLocalValue(value) : value.includes("T") ? value.slice(0, 16) : toDatetimeLocalValue(value);
  if (!localValue) return "";

  const [datePart, timePart = ""] = localValue.split("T");
  const brDate = toBrDateDisplay(datePart);
  if (!brDate) return "";
  const [hour = "", minute = ""] = timePart.split(":");
  if (!hour || minute === "") return brDate;
  return `${brDate} ${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
}

export function parseBrDatetimeDisplay(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return "";

  const match = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})$/);
  if (!match) return null;

  const isoDate = parseBrDateDisplay(`${match[1]}/${match[2]}/${match[3]}`);
  if (isoDate === null || isoDate === "") return isoDate;

  const hour = Number(match[4]);
  const minute = Number(match[5]);
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return null;

  const pad = (part: number) => String(part).padStart(2, "0");
  return `${isoDate}T${pad(hour)}:${pad(minute)}`;
}

export function fromDatetimeLocalValue(value: string): string {
  if (!value) return new Date().toISOString();
  const parsedLocal = parseBrDatetimeDisplay(value);
  if (parsedLocal) {
    const date = new Date(parsedLocal);
    return Number.isNaN(date.getTime()) ? new Date().toISOString() : date.toISOString();
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? new Date().toISOString() : date.toISOString();
}

export function toDateInputValue(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (part: number) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function fromDateInputValue(value: string): string {
  if (!value) return new Date().toISOString();
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? new Date().toISOString() : date.toISOString();
}

/** Filtra reposições por intervalo inclusive (YYYY-MM-DD). */
export function matchesReposicaoDateRange(
  dataReposicao: string,
  dataInicial: string,
  dataFinal: string,
): boolean {
  if (!dataInicial && !dataFinal) return true;
  const date = new Date(dataReposicao);
  if (Number.isNaN(date.getTime())) return false;
  if (dataInicial) {
    const start = new Date(`${dataInicial}T00:00:00`);
    if (date < start) return false;
  }
  if (dataFinal) {
    const end = new Date(`${dataFinal}T23:59:59.999`);
    if (date > end) return false;
  }
  return true;
}

export function isValidDateRange(dataInicial: string, dataFinal: string): boolean {
  if (!dataInicial || !dataFinal) return true;
  return dataInicial <= dataFinal;
}
