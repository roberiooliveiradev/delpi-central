import { useCallback, useEffect, useMemo, useState } from "react";

import type { TableColumnVisibilityItem } from "../components/data/TableColumnVisibilityMenu";
import {
  applyVisibleColumnReorder,
  createDefaultColumnOrder,
  createDefaultColumnVisibility,
  loadColumnVisibilityPreferences,
  reorderColumnKeys,
  sanitizeColumnOrder,
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
  /** Ordem completa do catálogo (inclui ocultas). */
  order: string[];
  /** Colunas do catálogo na ordem atual (visíveis e ocultas). */
  orderedColumns: TableColumnVisibilityItem[];
  visibleKeys: string[];
  visibleColumnCount: number;
  setColumnVisible: (key: string, visible: boolean) => void;
  /** Define a ordem completa do catálogo. */
  setColumnOrder: (order: string[]) => void;
  /** Reordena duas chaves no catálogo completo (menu Colunas). */
  reorderColumns: (fromKey: string, toKey: string) => void;
  /**
   * Aplica ordem vinda da DataTable (só colunas visíveis).
   * Preserva a posição relativa das colunas ocultas.
   */
  applyVisibleOrder: (visibleKeysInOrder: string[]) => void;
  reset: () => void;
  filterColumns: <T extends { key: string }>(columns: readonly T[]) => T[];
};

function defaultPreferences(
  columns: readonly TableColumnVisibilityItem[],
  defaultVisibility?: TableColumnVisibilityMap,
): TableColumnVisibilityPreferences {
  return {
    visibility: createDefaultColumnVisibility(columns, defaultVisibility),
    order: createDefaultColumnOrder(columns),
  };
}

/**
 * Preferências de visibilidade + ordem de colunas com persistência em localStorage.
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
      : defaultPreferences(columns, defaultVisibility),
  );

  // Re-sincroniza quando o catálogo de colunas muda (chaves novas/removidas).
  useEffect(() => {
    setPreferences((current) => {
      if (!enabled) {
        return defaultPreferences(columns, defaultVisibility);
      }
      const known = new Set(columns.map((c) => c.key));
      const nextVisibility = createDefaultColumnVisibility(columns, defaultVisibility);
      for (const [key, value] of Object.entries(current.visibility)) {
        if (known.has(key)) nextVisibility[key] = value;
      }
      const visibleCount = columns.filter((c) => nextVisibility[c.key]).length;
      if (visibleCount === 0 && columns.length > 0) {
        const fallback = (emptyFallbackKeys ?? []).filter((key) => known.has(key));
        if (fallback.length > 0) {
          for (const key of fallback) nextVisibility[key] = true;
        } else {
          nextVisibility[columns[0].key] = true;
        }
      }
      return {
        visibility: nextVisibility,
        order: sanitizeColumnOrder({ order: current.order }, columns),
      };
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

  const order = useMemo(
    () => sanitizeColumnOrder({ order: preferences.order }, columns),
    [columns, preferences.order],
  );

  const orderedColumns = useMemo(() => {
    const byKey = new Map(columns.map((column) => [column.key, column]));
    return order
      .map((key) => byKey.get(key))
      .filter((column): column is TableColumnVisibilityItem => Boolean(column));
  }, [columns, order]);

  const visibleKeys = useMemo(
    () => order.filter((key) => preferences.visibility[key]),
    [order, preferences.visibility],
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
          ...current,
          visibility: {
            ...current.visibility,
            [key]: visible,
          },
        };
      });
    },
    [columns, keepAtLeastOne],
  );

  const setColumnOrder = useCallback(
    (nextOrder: string[]) => {
      setPreferences((current) => ({
        ...current,
        order: sanitizeColumnOrder({ order: nextOrder }, columns),
      }));
    },
    [columns],
  );

  const reorderColumns = useCallback(
    (fromKey: string, toKey: string) => {
      setPreferences((current) => {
        const currentOrder = sanitizeColumnOrder({ order: current.order }, columns);
        return {
          ...current,
          order: reorderColumnKeys(currentOrder, fromKey, toKey),
        };
      });
    },
    [columns],
  );

  const applyVisibleOrder = useCallback(
    (visibleKeysInOrder: string[]) => {
      setPreferences((current) => {
        const currentOrder = sanitizeColumnOrder({ order: current.order }, columns);
        return {
          ...current,
          order: applyVisibleColumnReorder(currentOrder, visibleKeysInOrder),
        };
      });
    },
    [columns],
  );

  const reset = useCallback(() => {
    setPreferences(defaultPreferences(columns, defaultVisibility));
  }, [columns, defaultVisibility]);

  const filterColumns = useCallback(
    <T extends { key: string }>(items: readonly T[]): T[] => {
      const byKey = new Map(items.map((item) => [item.key, item]));
      return order
        .filter((key) => preferences.visibility[key])
        .map((key) => byKey.get(key))
        .filter((item): item is T => Boolean(item));
    },
    [order, preferences.visibility],
  );

  return {
    visibility: preferences.visibility,
    order,
    orderedColumns,
    visibleKeys,
    visibleColumnCount: visibleKeys.length,
    setColumnVisible,
    setColumnOrder,
    reorderColumns,
    applyVisibleOrder,
    reset,
    filterColumns,
  };
}
