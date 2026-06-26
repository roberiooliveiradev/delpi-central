export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}%`;
}

export function formatDecimal(
  value: number | null | undefined,
  digits = 1
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function averageNullable(values: Array<number | null | undefined>): number | null {
  const valid = values.filter(
    (item): item is number =>
      item !== null && item !== undefined && !Number.isNaN(item)
  );

  if (valid.length === 0) return null;
  return valid.reduce((sum, item) => sum + item, 0) / valid.length;
}

export function sumNullable(values: Array<number | null | undefined>): number | null {
  const valid = values.filter(
    (item): item is number =>
      item !== null && item !== undefined && !Number.isNaN(item)
  );

  if (valid.length === 0) return null;
  return valid.reduce((sum, item) => sum + item, 0);
}
