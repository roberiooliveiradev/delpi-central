import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createDefaultColumnPreferences,
  TABLE_COLUMNS,
  type TableColumnDef,
  type TableColumnKey,
  type TableColumnPreferences,
} from "../utils/tableColumns";
import {
  loadTableColumnPreferences,
  saveTableColumnPreferences,
} from "../utils/tableColumnPreferences";

export function useTableColumnPreferences() {
  const [preferences, setPreferences] = useState<TableColumnPreferences>(() =>
    loadTableColumnPreferences(),
  );

  useEffect(() => {
    const handle = window.setTimeout(() => {
      saveTableColumnPreferences(preferences);
    }, 200);

    return () => window.clearTimeout(handle);
  }, [preferences]);

  const visibleColumns = useMemo(
    () => TABLE_COLUMNS.filter((column) => preferences.visibility[column.key]),
    [preferences.visibility],
  );

  const visibleColumnCount = visibleColumns.length;

  const setColumnVisible = useCallback((key: TableColumnKey, visible: boolean) => {
    setPreferences((current) => {
      if (!visible) {
        const visibleCount = TABLE_COLUMNS.filter(
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
  }, []);

  const resetPreferences = useCallback(() => {
    setPreferences(createDefaultColumnPreferences());
  }, []);

  return {
    preferences,
    visibleColumns,
    visibleColumnCount,
    setColumnVisible,
    resetPreferences,
  };
}

export type UseTableColumnPreferencesResult = ReturnType<typeof useTableColumnPreferences>;

export type { TableColumnDef, TableColumnKey };
