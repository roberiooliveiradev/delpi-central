import {
  createDefaultColumnPreferences,
  TABLE_COLUMN_KEYS,
  type TableColumnKey,
  type TableColumnPreferences,
} from "./tableColumns";

const STORAGE_KEY = "pedidos-venda-abertos:table-columns:v2";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isTableColumnKey(value: string): value is TableColumnKey {
  return TABLE_COLUMN_KEYS.includes(value as TableColumnKey);
}

function sanitizePreferences(raw: unknown): TableColumnPreferences {
  const defaults = createDefaultColumnPreferences();

  if (!isRecord(raw)) {
    return defaults;
  }

  const visibility = { ...defaults.visibility };

  if (isRecord(raw.visibility)) {
    for (const [key, value] of Object.entries(raw.visibility)) {
      if (isTableColumnKey(key) && typeof value === "boolean") {
        visibility[key] = value;
      }
    }
  }

  const visibleCount = TABLE_COLUMN_KEYS.filter((key) => visibility[key]).length;
  if (visibleCount === 0) {
    visibility.nome_cliente = true;
    visibility.status = true;
  }

  return { visibility };
}

export function loadTableColumnPreferences(): TableColumnPreferences {
  if (typeof window === "undefined") {
    return createDefaultColumnPreferences();
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return migrateLegacyPreferences();
    }
    return sanitizePreferences(JSON.parse(raw));
  } catch {
    return createDefaultColumnPreferences();
  }
}

function migrateLegacyPreferences(): TableColumnPreferences {
  try {
    const legacy = window.localStorage.getItem("pedidos-venda-abertos:table-columns:v1");
    if (!legacy) return createDefaultColumnPreferences();
    return sanitizePreferences(JSON.parse(legacy));
  } catch {
    return createDefaultColumnPreferences();
  }
}

export function saveTableColumnPreferences(preferences: TableColumnPreferences): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
  } catch {
    /* ignore quota / private mode */
  }
}

export function resetTableColumnPreferences(): TableColumnPreferences {
  const defaults = createDefaultColumnPreferences();
  saveTableColumnPreferences(defaults);
  return defaults;
}
