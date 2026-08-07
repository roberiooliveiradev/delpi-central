import { useMemo } from "react";
import { useTableColumnVisibility } from "@delpi/plugin-ui/index";

import {
  TABLE_COLUMNS,
  createDefaultColumnVisibility,
  type TableColumnDef,
  type TableColumnKey,
  type TableColumnPreferences,
} from "../utils/tableColumns";

const STORAGE_KEY = "commercial:open-orders:table-columns:v5";
const LEGACY_STORAGE_KEYS = [
  "pedidos-venda-abertos:table-columns:v4",
  "pedidos-venda-abertos:table-columns:v1",
];

const COLUMN_ITEMS = TABLE_COLUMNS.map((column) => ({
  key: column.key,
  label: column.label,
}));

export function useTableColumnPreferences() {
  const defaultVisibility = useMemo(() => createDefaultColumnVisibility(), []);

  const {
    visibility,
    visibleColumnCount,
    setColumnVisible: setVisible,
    reset,
    filterColumns,
  } = useTableColumnVisibility({
    storageKey: STORAGE_KEY,
    columns: COLUMN_ITEMS,
    defaultVisibility,
    emptyFallbackKeys: ["nome_cliente", "status"],
    legacyStorageKeys: LEGACY_STORAGE_KEYS,
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
