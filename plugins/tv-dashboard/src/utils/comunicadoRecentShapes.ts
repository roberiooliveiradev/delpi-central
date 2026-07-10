import type { ComunicadoShapeKind } from "@delpi/tv-dashboard-presentation";

const STORAGE_KEY = "td-comunicado-recent-shapes";
const MAX_RECENT = 8;

export function readRecentComunicadoShapes(): ComunicadoShapeKind[] {
  if (typeof window === "undefined") return [];

  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((value): value is ComunicadoShapeKind => typeof value === "string");
  } catch {
    return [];
  }
}

export function rememberComunicadoShape(kind: ComunicadoShapeKind): ComunicadoShapeKind[] {
  const next = [kind, ...readRecentComunicadoShapes().filter((item) => item !== kind)].slice(0, MAX_RECENT);

  if (typeof window !== "undefined") {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // ignore quota errors
    }
  }

  return next;
}
