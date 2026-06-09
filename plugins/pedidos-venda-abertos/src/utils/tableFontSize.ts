export const TABLE_FONT_SIZE_STORAGE_KEY = "pedidos-venda-abertos:table-font-size:v1";

export const DEFAULT_TABLE_FONT_SIZE = 13;
export const MIN_TABLE_FONT_SIZE = 11;
export const MAX_TABLE_FONT_SIZE = 17;

export function clampTableFontSize(value: number): number {
  return Math.min(MAX_TABLE_FONT_SIZE, Math.max(MIN_TABLE_FONT_SIZE, Math.round(value)));
}

export function loadTableFontSize(): number {
  if (typeof window === "undefined") {
    return DEFAULT_TABLE_FONT_SIZE;
  }

  try {
    const raw = window.localStorage.getItem(TABLE_FONT_SIZE_STORAGE_KEY);
    if (!raw) return DEFAULT_TABLE_FONT_SIZE;

    const parsed = Number.parseInt(raw, 10);
    if (!Number.isFinite(parsed)) return DEFAULT_TABLE_FONT_SIZE;

    return clampTableFontSize(parsed);
  } catch {
    return DEFAULT_TABLE_FONT_SIZE;
  }
}

export function saveTableFontSize(size: number): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(TABLE_FONT_SIZE_STORAGE_KEY, String(clampTableFontSize(size)));
  } catch {
    /* ignore */
  }
}
