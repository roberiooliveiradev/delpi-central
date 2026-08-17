import { useCallback, useMemo, useState } from "react";
import { useTableColumnVisibility } from "@delpi/plugin-ui/index";

import type { DataTableColumnWidths } from "../../../app/commercialUi";
import {
  CUSTOMER_COLUMN_CATALOG,
  createCustomerDefaultColumnVisibility,
  type CustomerColumnDef,
  type CustomerColumnKey,
} from "../utils/customerTableColumns";

const STORAGE_KEY = "commercial:customers:table-columns:v2";
const WIDTHS_STORAGE_KEY = `${STORAGE_KEY}:widths`;
const LEGACY_STORAGE_KEYS = ["commercial:customers:table-columns:v1"];

function sanitizeWidths(value: unknown): DataTableColumnWidths {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  const known = new Set<string>(CUSTOMER_COLUMN_CATALOG.map((column) => column.key));
  return Object.fromEntries(
    Object.entries(value).filter(
      ([key, width]) => known.has(key) && typeof width === "number" && Number.isFinite(width),
    ),
  );
}

function loadWidths(): DataTableColumnWidths {
  if (typeof window === "undefined") return {};
  try {
    const current = window.localStorage.getItem(WIDTHS_STORAGE_KEY);
    if (current) return sanitizeWidths(JSON.parse(current));
    for (const legacyKey of LEGACY_STORAGE_KEYS) {
      const legacy = window.localStorage.getItem(legacyKey);
      if (!legacy) continue;
      const parsed = JSON.parse(legacy) as { widths?: unknown };
      return sanitizeWidths(parsed.widths);
    }
  } catch {
    // Preferência local é progressiva; a tabela continua funcional sem storage.
  }
  return {};
}

function saveWidths(widths: DataTableColumnWidths): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(WIDTHS_STORAGE_KEY, JSON.stringify(widths));
  } catch {
    // Preferência local é progressiva; a tabela continua funcional sem storage.
  }
}

export function useCustomerTablePreferences(canUseTeamScope: boolean) {
  const defaultVisibility = useMemo(
    () => createCustomerDefaultColumnVisibility(canUseTeamScope),
    [canUseTeamScope],
  );
  const {
    visibility,
    order,
    orderedColumns,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    reset: resetColumns,
    filterColumns,
  } = useTableColumnVisibility({
    storageKey: STORAGE_KEY,
    columns: CUSTOMER_COLUMN_CATALOG,
    defaultVisibility,
    emptyFallbackKeys: ["nome", "status"],
    legacyStorageKeys: LEGACY_STORAGE_KEYS,
  });
  const [widths, setWidthsState] = useState<DataTableColumnWidths>(loadWidths);

  const setWidths = useCallback((next: DataTableColumnWidths) => {
    setWidthsState(next);
    saveWidths(next);
  }, []);
  const reset = useCallback(() => {
    resetColumns();
    setWidths({});
  }, [resetColumns, setWidths]);

  return {
    visibility: visibility as Record<CustomerColumnKey, boolean>,
    order: order as CustomerColumnKey[],
    orderedColumns: orderedColumns as CustomerColumnDef[],
    filterColumns,
    widths,
    setWidths,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    reset,
  };
}

export {
  LEGACY_STORAGE_KEYS as CUSTOMER_TABLE_LEGACY_STORAGE_KEYS,
  STORAGE_KEY as CUSTOMER_TABLE_PREFERENCES_KEY,
  WIDTHS_STORAGE_KEY as CUSTOMER_TABLE_WIDTHS_KEY,
};
