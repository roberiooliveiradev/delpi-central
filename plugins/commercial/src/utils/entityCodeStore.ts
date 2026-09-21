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

/** Código-loja com centro quando preenchido (`000001-01 · 1100`). */
export function formatEntityCodeStoreCenter(
  code?: string | null,
  store?: string | null,
  center?: string | null,
): string | null {
  const codeStore = formatEntityCodeStore(code, store);
  const normalizedCenter = center?.trim() ?? "";
  if (!codeStore && !normalizedCenter) return null;
  if (!codeStore) return normalizedCenter || null;
  if (!normalizedCenter) return codeStore;
  return `${codeStore} · ${normalizedCenter}`;
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

/** Tipo + código-loja + centro (`CLIENTE 000001-09 · 1106`). */
export function formatEntityTypeWithCodeStoreCenter(
  entityType?: string | null,
  code?: string | null,
  store?: string | null,
  center?: string | null,
): string {
  const label = entityType?.trim() || "—";
  const codeStoreCenter = formatEntityCodeStoreCenter(code, store, center);
  if (!codeStoreCenter) return label;
  return `${label} ${codeStoreCenter}`;
}
