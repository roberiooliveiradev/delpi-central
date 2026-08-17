import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  TableColumnVisibilityMenu,
} from "@delpi/plugin-ui/index";

import type { TableColumnKey } from "../utils/tableColumns";

type MenuColumn = { key: string; label: string };

type TableColumnSettingsProps = {
  columns: readonly MenuColumn[];
  visibility: Record<TableColumnKey, boolean>;
  onToggleColumn: (key: TableColumnKey, visible: boolean) => void;
  onReorderColumns: (fromKey: TableColumnKey, toKey: TableColumnKey) => void;
  onReset: () => void;
};

export function TableColumnSettings({
  columns,
  visibility,
  onToggleColumn,
  onReorderColumns,
  onReset,
}: TableColumnSettingsProps) {
  return (
    <TableColumnVisibilityMenu
      columns={columns}
      visibility={visibility}
      onToggleColumn={(key, visible) => onToggleColumn(key as TableColumnKey, visible)}
      onReorderColumns={(fromKey, toKey) =>
        onReorderColumns(fromKey as TableColumnKey, toKey as TableColumnKey)
      }
      onReset={onReset}
      labels={DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS}
    />
  );
}
