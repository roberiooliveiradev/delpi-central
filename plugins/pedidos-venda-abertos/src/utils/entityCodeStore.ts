export function formatEntityCodeStore(
  code?: string | null,
  store?: string | null,
): string | null {
  const normalizedCode = code?.trim() ?? "";
  const normalizedStore = store?.trim() ?? "";

  if (!normalizedCode && !normalizedStore) {
    return null;
  }

  if (normalizedCode && normalizedStore) {
    return `${normalizedCode}-${normalizedStore}`;
  }

  return normalizedCode || normalizedStore;
}

export function formatEntityTypeWithCodeStore(
  entityType?: string | null,
  code?: string | null,
  store?: string | null,
): string {
  const label = entityType?.trim() || "—";
  const codeStore = formatEntityCodeStore(code, store);

  if (!codeStore) {
    return label;
  }

  return `${label} ${codeStore}`;
}
