import type { TableColumnVisibilityItem } from "../components/data/TableColumnVisibilityMenu";

export type TableColumnVisibilityMap = Record<string, boolean>;

export type TableColumnVisibilityPreferences = {
  visibility: TableColumnVisibilityMap;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Preferência default: todas as colunas do catálogo visíveis. */
export function createDefaultColumnVisibility(
  columns: readonly TableColumnVisibilityItem[],
  defaultVisibility?: TableColumnVisibilityMap,
): TableColumnVisibilityMap {
  const visibility: TableColumnVisibilityMap = {};
  for (const column of columns) {
    visibility[column.key] =
      defaultVisibility && Object.prototype.hasOwnProperty.call(defaultVisibility, column.key)
        ? Boolean(defaultVisibility[column.key])
        : true;
  }
  return visibility;
}

export function sanitizeColumnVisibility(
  raw: unknown,
  columns: readonly TableColumnVisibilityItem[],
  options?: {
    defaultVisibility?: TableColumnVisibilityMap;
    /** Quando nenhuma coluna fica visível após sanitizar. */
    emptyFallbackKeys?: readonly string[];
  },
): TableColumnVisibilityMap {
  const knownKeys = new Set(columns.map((column) => column.key));
  const visibility = createDefaultColumnVisibility(columns, options?.defaultVisibility);

  if (isRecord(raw) && isRecord(raw.visibility)) {
    for (const [key, value] of Object.entries(raw.visibility)) {
      if (knownKeys.has(key) && typeof value === "boolean") {
        visibility[key] = value;
      }
    }
  }

  const visibleCount = columns.filter((column) => visibility[column.key]).length;
  if (visibleCount === 0 && columns.length > 0) {
    const fallback = (options?.emptyFallbackKeys ?? []).filter((key) => knownKeys.has(key));
    if (fallback.length > 0) {
      for (const key of fallback) {
        visibility[key] = true;
      }
    } else {
      visibility[columns[0].key] = true;
    }
  }

  return visibility;
}

export function loadColumnVisibilityPreferences(
  storageKey: string,
  columns: readonly TableColumnVisibilityItem[],
  options?: {
    defaultVisibility?: TableColumnVisibilityMap;
    emptyFallbackKeys?: readonly string[];
    legacyStorageKeys?: readonly string[];
  },
): TableColumnVisibilityPreferences {
  if (typeof window === "undefined") {
    return {
      visibility: createDefaultColumnVisibility(columns, options?.defaultVisibility),
    };
  }

  try {
    const raw = window.localStorage.getItem(storageKey);
    if (raw) {
      return {
        visibility: sanitizeColumnVisibility(JSON.parse(raw), columns, options),
      };
    }

    for (const legacyKey of options?.legacyStorageKeys ?? []) {
      const legacy = window.localStorage.getItem(legacyKey);
      if (!legacy) continue;
      return {
        visibility: sanitizeColumnVisibility(JSON.parse(legacy), columns, options),
      };
    }
  } catch {
    /* ignore parse / private mode */
  }

  return {
    visibility: createDefaultColumnVisibility(columns, options?.defaultVisibility),
  };
}

export function saveColumnVisibilityPreferences(
  storageKey: string,
  preferences: TableColumnVisibilityPreferences,
): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(storageKey, JSON.stringify(preferences));
  } catch {
    /* ignore quota / private mode */
  }
}
