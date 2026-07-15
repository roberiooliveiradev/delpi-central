import { useCallback, useEffect, useMemo, useState } from "react";

import type { TableColumnVisibilityItem } from "../components/data/TableColumnVisibilityMenu";
import {
  createDefaultColumnVisibility,
  loadColumnVisibilityPreferences,
  saveColumnVisibilityPreferences,
  type TableColumnVisibilityMap,
  type TableColumnVisibilityPreferences,
} from "../utils/tableColumnVisibilityPreferences";

export type UseTableColumnVisibilityOptions = {
  storageKey: string;
  columns: readonly TableColumnVisibilityItem[];
  /** Quando false, não lê/grava localStorage e mantém todas visíveis. Default true. */
  enabled?: boolean;
  defaultVisibility?: TableColumnVisibilityMap;
  keepAtLeastOne?: boolean;
  emptyFallbackKeys?: readonly string[];
  legacyStorageKeys?: readonly string[];
  /** Debounce do save em localStorage (ms). Default 200. */
  saveDebounceMs?: number;
};

export type UseTableColumnVisibilityResult = {
  visibility: TableColumnVisibilityMap;
  visibleKeys: string[];
  visibleColumnCount: number;
  setColumnVisible: (key: string, visible: boolean) => void;
  reset: () => void;
  filterColumns: <T extends { key: string }>(columns: readonly T[]) => T[];
};

/**
 * Preferências de visibilidade de colunas com persistência em localStorage.
 * Usado por `DataTableSection` (`columnPreferencesKey`) e por MFEs com tabela própria.
 */
export function useTableColumnVisibility(
  options: UseTableColumnVisibilityOptions,
): UseTableColumnVisibilityResult {
  const {
    storageKey,
    columns,
    enabled = true,
    defaultVisibility,
    keepAtLeastOne = true,
    emptyFallbackKeys,
    legacyStorageKeys,
    saveDebounceMs = 200,
  } = options;

  const columnKeysSignature = columns.map((column) => column.key).join("\0");

  const [preferences, setPreferences] = useState<TableColumnVisibilityPreferences>(() =>
    enabled
      ? loadColumnVisibilityPreferences(storageKey, columns, {
          defaultVisibility,
          emptyFallbackKeys,
          legacyStorageKeys,
        })
      : { visibility: createDefaultColumnVisibility(columns, defaultVisibility) },
  );

  // Re-sincroniza quando o catálogo de colunas muda (chaves novas/removidas).
  useEffect(() => {
    setPreferences((current) => {
      if (!enabled) {
        return { visibility: createDefaultColumnVisibility(columns, defaultVisibility) };
      }
      const known = new Set(columns.map((c) => c.key));
      const next = createDefaultColumnVisibility(columns, defaultVisibility);
      for (const [key, value] of Object.entries(current.visibility)) {
        if (known.has(key)) next[key] = value;
      }
      const visibleCount = columns.filter((c) => next[c.key]).length;
      if (visibleCount === 0 && columns.length > 0) {
        const fallback = (emptyFallbackKeys ?? []).filter((key) => known.has(key));
        if (fallback.length > 0) {
          for (const key of fallback) next[key] = true;
        } else {
          next[columns[0].key] = true;
        }
      }
      return { visibility: next };
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- columnKeysSignature
  }, [columnKeysSignature, storageKey, enabled]);

  useEffect(() => {
    if (!enabled || !storageKey) return;
    const handle = window.setTimeout(() => {
      saveColumnVisibilityPreferences(storageKey, preferences);
    }, saveDebounceMs);
    return () => window.clearTimeout(handle);
  }, [enabled, preferences, saveDebounceMs, storageKey]);

  const visibleKeys = useMemo(
    () => columns.filter((column) => preferences.visibility[column.key]).map((column) => column.key),
    [columns, preferences.visibility],
  );

  const setColumnVisible = useCallback(
    (key: string, visible: boolean) => {
      setPreferences((current) => {
        if (!columns.some((column) => column.key === key)) return current;

        if (!visible && keepAtLeastOne) {
          const visibleCount = columns.filter(
            (column) => current.visibility[column.key],
          ).length;
          if (visibleCount <= 1 && current.visibility[key]) {
            return current;
          }
        }

        return {
          visibility: {
            ...current.visibility,
            [key]: visible,
          },
        };
      });
    },
    [columns, keepAtLeastOne],
  );

  const reset = useCallback(() => {
    setPreferences({
      visibility: createDefaultColumnVisibility(columns, defaultVisibility),
    });
  }, [columns, defaultVisibility]);

  const filterColumns = useCallback(
    <T extends { key: string }>(items: readonly T[]): T[] =>
      items.filter((item) => preferences.visibility[item.key]),
    [preferences.visibility],
  );

  return {
    visibility: preferences.visibility,
    visibleKeys,
    visibleColumnCount: visibleKeys.length,
    setColumnVisible,
    reset,
    filterColumns,
  };
}
