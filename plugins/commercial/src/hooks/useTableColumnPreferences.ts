import { useMemo } from "react";
import { useTableColumnVisibility } from "@delpi/plugin-ui/index";

import {
  TABLE_COLUMNS,
  createDefaultColumnVisibility,
  type TableColumnDef,
  type TableColumnKey,
  type TableColumnPreferences,
} from "../utils/tableColumns";

const STORAGE_KEY = "commercial:open-orders:table-columns:v7";
const LEGACY_STORAGE_KEYS = [
  "commercial:open-orders:table-columns:v6",
  "commercial:open-orders:table-columns:v5",
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
    order,
    orderedColumns,
    visibleColumnCount,
    setColumnVisible: setVisible,
    reorderColumns,
    applyVisibleOrder,
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
      order: order as TableColumnKey[],
    }),
    [order, visibility],
  );

  const visibleColumns = useMemo(
    () => filterColumns(TABLE_COLUMNS) as TableColumnDef[],
    [filterColumns],
  );

  return {
    preferences,
    visibleColumns,
    orderedMenuColumns: orderedColumns,
    visibleColumnCount,
    setColumnVisible: (key: TableColumnKey, visible: boolean) => {
      setVisible(key, visible);
    },
    reorderColumns: (fromKey: TableColumnKey, toKey: TableColumnKey) => {
      reorderColumns(fromKey, toKey);
    },
    applyVisibleOrder: (visibleKeysInOrder: string[]) => {
      applyVisibleOrder(visibleKeysInOrder);
    },
    resetPreferences: reset,
  };
}

export type UseTableColumnPreferencesResult = ReturnType<typeof useTableColumnPreferences>;

export type { TableColumnDef, TableColumnKey };
