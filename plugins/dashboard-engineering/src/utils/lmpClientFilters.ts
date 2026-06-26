/** Uma opção → valor na API; vazio ou várias → fallback (ex.: "Todos"). */
export function resolveScalarApiFilter(
  values: string[],
  fallback: string
): string {
  return values.length === 1 ? values[0] : fallback;
}

export function needsClientSideMultiFilter(values: string[]): boolean {
  return values.length > 1;
}

export function matchesMultiFilter(
  value: string | null | undefined,
  selected: string[]
): boolean {
  if (selected.length === 0) return true;
  if (!value) return false;
  return selected.includes(value);
}
