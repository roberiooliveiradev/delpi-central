const MAX_MONTHS = 24;

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

export function getThisMonthRange(referenceDate = new Date()): {
  dateStart: string;
  dateEnd: string;
} {
  const dateEnd = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const dateStart = new Date(dateEnd.getFullYear(), dateEnd.getMonth(), 1);
  return { dateStart: formatIsoDate(dateStart), dateEnd: formatIsoDate(dateEnd) };
}

export function getDefaultLast6MonthsRange(referenceDate = new Date()): {
  dateStart: string;
  dateEnd: string;
} {
  const dateEnd = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const dateStart = new Date(dateEnd.getFullYear(), dateEnd.getMonth() - 5, 1);
  return { dateStart: formatIsoDate(dateStart), dateEnd: formatIsoDate(dateEnd) };
}

export function getDefaultLast30DaysRange(referenceDate = new Date()): {
  dateStart: string;
  dateEnd: string;
} {
  const dateEnd = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const dateStart = new Date(dateEnd);
  dateStart.setDate(dateStart.getDate() - 29);
  return { dateStart: formatIsoDate(dateStart), dateEnd: formatIsoDate(dateEnd) };
}

function parseIsoDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

export function validatePeriodRange(dateStart: string, dateEnd: string): string | null {
  const start = parseIsoDate(dateStart);
  const end = parseIsoDate(dateEnd);

  if (!start || !end) {
    return "Informe datas válidas no formato YYYY-MM-DD.";
  }
  if (start > end) {
    return "A data inicial não pode ser maior que a data final.";
  }
  const months =
    (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth()) + 1;
  if (months > MAX_MONTHS) {
    return `Período máximo permitido: ${MAX_MONTHS} meses.`;
  }
  return null;
}

export function createDefaultFilterFormState(referenceDate = new Date()) {
  const range = getThisMonthRange(referenceDate);
  return {
    ...range,
    workCenter: "",
    op: "",
    product: "",
  };
}

export function filtersFromFormState(
  branch: string,
  state: {
    dateStart: string;
    dateEnd: string;
    workCenter?: string;
    op?: string;
    product?: string;
  },
) {
  return {
    branch,
    dateStart: state.dateStart,
    dateEnd: state.dateEnd,
    workCenter: state.workCenter?.trim() || undefined,
    op: state.op?.trim() || undefined,
    product: state.product?.trim() || undefined,
  };
}
