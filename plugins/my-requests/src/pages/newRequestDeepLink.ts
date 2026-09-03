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
