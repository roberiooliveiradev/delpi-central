/** Deep link helpers for /new (E8 cutover from guias / legado). */

export function readTypeCodeFromSearch(
  search: string = typeof window !== "undefined" ? window.location.search : "",
): string {
  try {
    const params = new URLSearchParams(search.startsWith("?") ? search : `?${search}`);
    return (params.get("type") || params.get("type_code") || "").trim();
  } catch {
    return "";
  }
}

/** Resolve preferred type from catalog — used to auto-open the form (E19). */
export function findTypeForDeepLink<T extends { code: string }>(
  types: readonly T[],
  preferredCode: string,
): T | null {
  const code = preferredCode.trim();
  if (!code) return null;
  return types.find((item) => item.code === code) || null;
}
