import { useMemo } from "react";
import { useTableColumnVisibility } from "@delpi/plugin-ui/index";

import {
  TABLE_COLUMNS,
  type TableColumnDef,
  type TableColumnKey,
  type TableColumnPreferences,
} from "../utils/tableColumns";

const STORAGE_KEY = "pedidos-venda-abertos:table-columns:v4";
const LEGACY_STORAGE_KEY = "pedidos-venda-abertos:table-columns:v1";

const COLUMN_ITEMS = TABLE_COLUMNS.map((column) => ({
  key: column.key,
  label: column.label,
}));

export function useTableColumnPreferences() {
  const {
    visibility,
    visibleColumnCount,
    setColumnVisible: setVisible,
    reset,
    filterColumns,
  } = useTableColumnVisibility({
    storageKey: STORAGE_KEY,
    columns: COLUMN_ITEMS,
    emptyFallbackKeys: ["nome_cliente", "status"],
    legacyStorageKeys: [LEGACY_STORAGE_KEY],
  });

  const preferences: TableColumnPreferences = useMemo(
    () => ({
      visibility: visibility as Record<TableColumnKey, boolean>,
    }),
    [visibility],
  );

  const visibleColumns = useMemo(
    () => filterColumns(TABLE_COLUMNS) as TableColumnDef[],
    [filterColumns],
  );

  return {
    preferences,
    visibleColumns,
    visibleColumnCount,
    setColumnVisible: (key: TableColumnKey, visible: boolean) => {
      setVisible(key, visible);
    },
    resetPreferences: reset,
  };
}

export type UseTableColumnPreferencesResult = ReturnType<typeof useTableColumnPreferences>;

export type { TableColumnDef, TableColumnKey };
