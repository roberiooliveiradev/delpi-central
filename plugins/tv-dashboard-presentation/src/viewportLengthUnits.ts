/**
 * Unidades absolutas CSS (96 dpi) para resolução custom do canvas TV.
 * Persistência canônica permanece em px; a UI converte na edição.
 *
 * 1in = 96px = 72pt = 6pc = 2.54cm
 */
export type ViewportLengthUnit = "px" | "cm" | "mm" | "in" | "pt" | "pc";

export const VIEWPORT_LENGTH_UNITS: readonly ViewportLengthUnit[] = [
  "px",
  "cm",
  "mm",
  "in",
  "pt",
  "pc",
] as const;

export const VIEWPORT_LENGTH_UNIT_LABELS: Record<ViewportLengthUnit, string> = {
  px: "px (pixels)",
  cm: "cm",
  mm: "mm",
  in: "in (polegadas)",
  pt: "pt (pontos)",
  pc: "pc (paicas)",
};

/** Limites do canvas de design (px). */
export const VIEWPORT_DESIGN_PX_MIN = 64;
export const VIEWPORT_DESIGN_PX_MAX = 7680;

/** Fator: quantos px CSS cabem em 1 unidade. */
const PX_PER_UNIT: Record<ViewportLengthUnit, number> = {
  px: 1,
  in: 96,
  cm: 96 / 2.54,
  mm: 96 / 25.4,
  pt: 96 / 72,
  pc: 16,
};

export function isViewportLengthUnit(value: unknown): value is ViewportLengthUnit {
  return typeof value === "string" && (VIEWPORT_LENGTH_UNITS as readonly string[]).includes(value);
}

export function clampDesignPx(value: number): number {
  if (!Number.isFinite(value)) return VIEWPORT_DESIGN_PX_MIN;
  return Math.min(VIEWPORT_DESIGN_PX_MAX, Math.max(VIEWPORT_DESIGN_PX_MIN, Math.round(value)));
}

/** Converte valor na unidade informada para px (sem clamp). */
export function pxFromUnit(value: number, unit: ViewportLengthUnit): number {
  if (!Number.isFinite(value)) return NaN;
  return value * PX_PER_UNIT[unit];
}

/** Converte px para a unidade (sem clamp). */
export function unitFromPx(px: number, unit: ViewportLengthUnit): number {
  if (!Number.isFinite(px)) return NaN;
  return px / PX_PER_UNIT[unit];
}

/**
 * Valor digitado na UI → px inteiro clampado para persistir.
 * Retorna null se o input não for um número finito positivo após parse.
 */
export function parseViewportDimensionToPx(
  raw: string | number,
  unit: ViewportLengthUnit,
): number | null {
  const n = typeof raw === "number" ? raw : Number(String(raw).trim().replace(",", "."));
  if (!Number.isFinite(n) || n <= 0) return null;
  return clampDesignPx(pxFromUnit(n, unit));
}

/** Formata px para exibição na unidade (casas adaptativas). */
export function formatViewportDimensionFromPx(px: number, unit: ViewportLengthUnit): string {
  const value = unitFromPx(px, unit);
  if (!Number.isFinite(value)) return "";
  if (unit === "px") return String(Math.round(value));
  const rounded = Math.round(value * 1000) / 1000;
  return String(rounded);
}

/** px → mm (mesma base CSS 96 dpi) — páginas PDF. */
export function cssPxToMm(px: number): number {
  return (px * 25.4) / 96;
}

export const VIEWPORT_LENGTH_UNIT_STORAGE_KEY = "td.viewportLengthUnit";

export function readStoredViewportLengthUnit(
  storage: Pick<Storage, "getItem"> | null | undefined = typeof localStorage !== "undefined"
    ? localStorage
    : null,
): ViewportLengthUnit {
  if (!storage) return "px";
  try {
    const raw = storage.getItem(VIEWPORT_LENGTH_UNIT_STORAGE_KEY);
    return isViewportLengthUnit(raw) ? raw : "px";
  } catch {
    return "px";
  }
}

export function writeStoredViewportLengthUnit(
  unit: ViewportLengthUnit,
  storage: Pick<Storage, "setItem"> | null | undefined = typeof localStorage !== "undefined"
    ? localStorage
    : null,
): void {
  if (!storage) return;
  try {
    storage.setItem(VIEWPORT_LENGTH_UNIT_STORAGE_KEY, unit);
  } catch {
    /* ignore quota / private mode */
  }
}
