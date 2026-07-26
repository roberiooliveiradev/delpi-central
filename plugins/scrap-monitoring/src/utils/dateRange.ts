const MAX_MONTHS = 24;

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

export function getDefaultLast12MonthsRange(referenceDate = new Date()): {
  start_date: string;
  end_date: string;
} {
  const dataFim = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const dataInicio = new Date(dataFim.getFullYear(), dataFim.getMonth() - 11, 1);

  return {
    start_date: formatIsoDate(dataInicio),
    end_date: formatIsoDate(dataFim),
  };
}

export function getDefaultLast6MonthsRange(referenceDate = new Date()): {
  start_date: string;
  end_date: string;
} {
  const dataFim = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const dataInicio = new Date(dataFim.getFullYear(), dataFim.getMonth() - 5, 1);

  return {
    start_date: formatIsoDate(dataInicio),
    end_date: formatIsoDate(dataFim),
  };
}

export function getThisMonthRange(referenceDate = new Date()): {
  start_date: string;
  end_date: string;
} {
  const dataFim = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const dataInicio = new Date(dataFim.getFullYear(), dataFim.getMonth(), 1);

  return {
    start_date: formatIsoDate(dataInicio),
    end_date: formatIsoDate(dataFim),
  };
}

export function getTodayRange(referenceDate = new Date()): {
  start_date: string;
  end_date: string;
} {
  const day = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const iso = formatIsoDate(day);
  return { start_date: iso, end_date: iso };
}

/** Semana calendário (segunda → hoje), alinhado aos dashboards departamentais. */
export function getThisWeekRange(referenceDate = new Date()): {
  start_date: string;
  end_date: string;
} {
  const dataFim = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const day = dataFim.getDay(); // 0=domingo … 6=sábado
  const daysSinceMonday = day === 0 ? 6 : day - 1;
  const dataInicio = new Date(dataFim);
  dataInicio.setDate(dataInicio.getDate() - daysSinceMonday);
  return {
    start_date: formatIsoDate(dataInicio),
    end_date: formatIsoDate(dataFim),
  };
}

function parseIsoDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

export function validatePeriodRange(start_date: string, end_date: string): string | null {
  const start = parseIsoDate(start_date);
  const end = parseIsoDate(end_date);

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
    start_date: string;
    end_date: string;
    mp?: string;
    pa?: string;
    op?: string;
    motivo?: string;
    centroTrabalho?: string;
  },
) {
  return {
    filial,
    start_date: state.start_date,
    end_date: state.end_date,
    mp: optionalFilter(state.mp),
    pa: optionalFilter(state.pa),
    op: optionalFilter(state.op),
    motivo: optionalFilter(state.motivo),
    centroTrabalho: optionalFilter(state.centroTrabalho),
  };
}
