const MAX_MONTHS = 24;

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

export function getDefaultLast12MonthsRange(referenceDate = new Date()): {
  dataInicio: string;
  dataFim: string;
} {
  const dataFim = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const dataInicio = new Date(dataFim.getFullYear(), dataFim.getMonth() - 11, 1);

  return {
    dataInicio: formatIsoDate(dataInicio),
    dataFim: formatIsoDate(dataFim),
  };
}

export function getDefaultLast6MonthsRange(referenceDate = new Date()): {
  dataInicio: string;
  dataFim: string;
} {
  const dataFim = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const dataInicio = new Date(dataFim.getFullYear(), dataFim.getMonth() - 5, 1);

  return {
    dataInicio: formatIsoDate(dataInicio),
    dataFim: formatIsoDate(dataFim),
  };
}

export function getThisMonthRange(referenceDate = new Date()): {
  dataInicio: string;
  dataFim: string;
} {
  const dataFim = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const dataInicio = new Date(dataFim.getFullYear(), dataFim.getMonth(), 1);

  return {
    dataInicio: formatIsoDate(dataInicio),
    dataFim: formatIsoDate(dataFim),
  };
}

function parseIsoDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

export function validatePeriodRange(dataInicio: string, dataFim: string): string | null {
  const start = parseIsoDate(dataInicio);
  const end = parseIsoDate(dataFim);

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

const EMPTY_OPTIONAL_FILTERS = {
  mp: "",
  pa: "",
  op: "",
  motivo: "",
  centroTrabalho: "",
} as const;

export function createDefaultFilterFormState(referenceDate = new Date()) {
  return {
    ...getThisMonthRange(referenceDate),
    ...EMPTY_OPTIONAL_FILTERS,
  };
}

function optionalFilter(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

export function filtersFromFormState(
  filial: string,
  state: {
    dataInicio: string;
    dataFim: string;
    mp?: string;
    pa?: string;
    op?: string;
    motivo?: string;
    centroTrabalho?: string;
  },
) {
  return {
    filial,
    dataInicio: state.dataInicio,
    dataFim: state.dataFim,
    mp: optionalFilter(state.mp),
    pa: optionalFilter(state.pa),
    op: optionalFilter(state.op),
    motivo: optionalFilter(state.motivo),
    centroTrabalho: optionalFilter(state.centroTrabalho),
  };
}
