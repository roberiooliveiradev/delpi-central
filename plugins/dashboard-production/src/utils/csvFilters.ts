export function formatCsvFilterValues(values: string[]): string | undefined {
  const normalized = values.map((value) => value.trim()).filter(Boolean);
  return normalized.length > 0 ? normalized.join(",") : undefined;
}
