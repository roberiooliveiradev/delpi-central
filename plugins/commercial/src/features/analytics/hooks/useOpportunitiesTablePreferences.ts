import { useMemo, type CSSProperties } from "react";
import { useTableColumnVisibility, useTableFontSize } from "@delpi/plugin-ui/index";

import type { OpportunityTableColumnItem } from "../utils/opportunityTableColumns";

type UseOpportunitiesTablePreferencesArgs = {
  columnsStorageKey: string;
  fontSizeStorageKey: string;
  columns: readonly OpportunityTableColumnItem[];
  emptyFallbackKeys: string[];
  defaultVisibility?: Record<string, boolean>;
};

export function useOpportunitiesTablePreferences({
  columnsStorageKey,
  fontSizeStorageKey,
  columns,
  emptyFallbackKeys,
  defaultVisibility,
}: UseOpportunitiesTablePreferencesArgs) {
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
