export function getOperatorFirstName(value: string): string {
  const trimmed = value.trim();
  if (!trimmed || trimmed === "—") return trimmed || "—";
  return trimmed.split(/\s+/)[0] ?? trimmed;
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

export function formatNumber(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

export function formatHoursKpi(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `${formatNumber(value, fractionDigits)} Horas`;
}

export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function formatInteger(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toLocaleString("pt-BR", {
    maximumFractionDigits: 0,
  });
}

/** Casas decimais padronizadas para qtd. apontada e meta/hora. */
export const PRODUCTION_QUANTITY_FRACTION_DIGITS = 3;

export function formatProductionQuantity(
  value: number | null | undefined,
  unit?: string | null,
  fractionDigits = PRODUCTION_QUANTITY_FRACTION_DIGITS
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }

  const qty = value.toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
  const normalizedUnit = unit?.trim();
  return normalizedUnit ? `${qty} ${normalizedUnit}` : qty;
}

/** Meta de produção por hora (mesma unidade da qtd. apontada). */
export function formatMetaPerHour(
  value: number | null | undefined,
  unit?: string | null
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  const qty = formatProductionQuantity(value, unit);
  return qty === "—" ? "—" : `${qty}/h`;
}

export function formatDecimal(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  return formatNumber(value, fractionDigits);
}

export function formatHours(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `${formatNumber(value, fractionDigits)} h`;
}
