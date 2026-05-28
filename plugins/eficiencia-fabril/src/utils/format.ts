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
