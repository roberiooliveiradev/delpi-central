import type { TableColumnVisibilityItem } from "../components/data/TableColumnVisibilityMenu";

export type TableColumnVisibilityMap = Record<string, boolean>;

export type TableColumnVisibilityPreferences = {
  visibility: TableColumnVisibilityMap;
  /** Ordem completa do catálogo (visíveis e ocultas). */
  order: string[];
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

export function createDefaultColumnOrder(
  columns: readonly TableColumnVisibilityItem[],
): string[] {
  return columns.map((column) => column.key);
}

/**
 * Reordena `fromKey` para a posição de `toKey` dentro de `keys`.
 * Usado pelo menu Colunas e pelo header da DataTable.
 */
export function reorderColumnKeys(keys: string[], fromKey: string, toKey: string): string[] {
  if (fromKey === toKey) return keys;
  const from = keys.indexOf(fromKey);
  const to = keys.indexOf(toKey);
  if (from < 0 || to < 0) return keys;
  const next = [...keys];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved!);
  return next;
}

/**
 * Aplica reordenação só entre colunas visíveis, preservando posições das ocultas
 * no `fullOrder` (resultado de arrastar headers na tabela).
 */
export function applyVisibleColumnReorder(
  fullOrder: readonly string[],
  nextVisibleKeys: readonly string[],
): string[] {
  const visibleSet = new Set(nextVisibleKeys);
  let index = 0;
  return fullOrder.map((key) => {
    if (!visibleSet.has(key)) return key;
    const next = nextVisibleKeys[index];
    index += 1;
    return next ?? key;
  });
}

export function sanitizeColumnOrder(
  raw: unknown,
  columns: readonly TableColumnVisibilityItem[],
): string[] {
  const catalog = createDefaultColumnOrder(columns);
  const known = new Set(catalog);
  const order: string[] = [];
  const seen = new Set<string>();

  const candidate = Array.isArray(raw)
    ? raw
    : isRecord(raw) && Array.isArray(raw.order)
      ? raw.order
      : [];

  for (const key of candidate) {
    if (typeof key !== "string" || !known.has(key) || seen.has(key)) continue;
    order.push(key);
    seen.add(key);
  }
  for (const key of catalog) {
    if (!seen.has(key)) order.push(key);
  }
  return order;
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

  const visibilitySource = isRecord(raw)
    ? isRecord(raw.visibility)
      ? raw.visibility
      : raw
    : null;

  if (visibilitySource) {
    for (const [key, value] of Object.entries(visibilitySource)) {
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

export function sanitizeColumnVisibilityPreferences(
  raw: unknown,
  columns: readonly TableColumnVisibilityItem[],
  options?: {
    defaultVisibility?: TableColumnVisibilityMap;
    emptyFallbackKeys?: readonly string[];
  },
): TableColumnVisibilityPreferences {
  return {
    visibility: sanitizeColumnVisibility(raw, columns, options),
    order: sanitizeColumnOrder(raw, columns),
  };
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
      order: createDefaultColumnOrder(columns),
    };
  }

  try {
    const raw = window.localStorage.getItem(storageKey);
    if (raw) {
      return sanitizeColumnVisibilityPreferences(JSON.parse(raw), columns, options);
    }

    for (const legacyKey of options?.legacyStorageKeys ?? []) {
      const legacy = window.localStorage.getItem(legacyKey);
      if (!legacy) continue;
      return sanitizeColumnVisibilityPreferences(JSON.parse(legacy), columns, options);
    }
  } catch {
    /* ignore parse / private mode */
  }

  return {
    visibility: createDefaultColumnVisibility(columns, options?.defaultVisibility),
    order: createDefaultColumnOrder(columns),
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
