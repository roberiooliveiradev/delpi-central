export const DEFAULT_TABLE_FONT_SIZE = 13;
export const MIN_TABLE_FONT_SIZE = 11;
export const MAX_TABLE_FONT_SIZE = 17;

export type TableFontSizePreferenceOptions = {
  storageKey: string;
  legacyStorageKeys?: readonly string[];
};

export function clampTableFontSize(value: number): number {
  return Math.min(MAX_TABLE_FONT_SIZE, Math.max(MIN_TABLE_FONT_SIZE, Math.round(value)));
}

export function loadTableFontSize(options: TableFontSizePreferenceOptions): number {
  if (typeof window === "undefined") {
    return DEFAULT_TABLE_FONT_SIZE;
  }

  try {
    const keys = [options.storageKey, ...(options.legacyStorageKeys ?? [])];
    let raw: string | null = null;
    for (const key of keys) {
      raw = window.localStorage.getItem(key);
      if (raw) break;
    }
    if (!raw) return DEFAULT_TABLE_FONT_SIZE;

    const parsed = Number.parseInt(raw, 10);
    if (!Number.isFinite(parsed)) return DEFAULT_TABLE_FONT_SIZE;

    return clampTableFontSize(parsed);
  } catch {
    return DEFAULT_TABLE_FONT_SIZE;
  }
}

export function saveTableFontSize(
  size: number,
  options: Pick<TableFontSizePreferenceOptions, "storageKey">,
): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(
      options.storageKey,
      String(clampTableFontSize(size)),
    );
  } catch {
    /* ignore */
  }
}
