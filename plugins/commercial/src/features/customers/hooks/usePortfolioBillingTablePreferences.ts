import { useMemo, type CSSProperties } from "react";
import { useTableColumnVisibility, useTableFontSize } from "@delpi/plugin-ui/index";

import type { PortfolioBillingColumnItem } from "../utils/portfolioBillingTableColumns";

type UsePortfolioBillingTablePreferencesArgs = {
  columnsStorageKey: string;
  fontSizeStorageKey: string;
  columns: readonly PortfolioBillingColumnItem[];
  emptyFallbackKeys: string[];
  defaultVisibility?: Record<string, boolean>;
};

export function usePortfolioBillingTablePreferences({
  columnsStorageKey,
  fontSizeStorageKey,
  columns,
  emptyFallbackKeys,
  defaultVisibility,
}: UsePortfolioBillingTablePreferencesArgs) {
  const columnItems = useMemo(
    () => columns.map((column) => ({ key: column.key, label: column.label })),
    [columns],
  );

  const {
    visibility,
    orderedColumns,
    visibleColumnCount,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    reset: resetColumns,
    filterColumns,
  } = useTableColumnVisibility({
    storageKey: columnsStorageKey,
    columns: columnItems,
    defaultVisibility,
    emptyFallbackKeys,
  });

  const font = useTableFontSize({ storageKey: fontSizeStorageKey });

  const tableStyle = useMemo(
    (): CSSProperties =>
      ({
        "--delpi-ui-table-font-size": `${font.fontSize}px`,
      }) as CSSProperties,
    [font.fontSize],
  );

  return {
    visibility,
    orderedColumns,
    visibleColumnCount,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    resetColumns,
    filterColumns,
    tableStyle,
    fontSize: font.fontSize,
    increaseFont: font.increase,
    decreaseFont: font.decrease,
    resetFont: font.reset,
    canIncreaseFont: font.canIncrease,
    canDecreaseFont: font.canDecrease,
    isDefaultFont: font.isDefault,
  };
}
