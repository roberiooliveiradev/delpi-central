const STORAGE_KEY = "td-comunicado-recent-colors";
const MAX_RECENT = 10;

function normalizeColor(value: string): string | null {
  const trimmed = value.trim().toLowerCase();
  if (!trimmed || trimmed === "transparent" || trimmed === "auto") return null;
  return trimmed;
}

export function readRecentComunicadoColors(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((value): value is string => typeof value === "string")
      .map(normalizeColor)
      .filter((value): value is string => Boolean(value));
  } catch {
    return [];
  }
}

export function rememberComunicadoColor(color: string): string[] {
  const normalized = normalizeColor(color);
  if (!normalized) return readRecentComunicadoColors();
  const next = [normalized, ...readRecentComunicadoColors().filter((item) => item !== normalized)].slice(
    0,
    MAX_RECENT,
  );
  if (typeof window !== "undefined") {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // ignore quota
    }
  }
  return next;
}
