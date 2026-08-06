import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  TableColumnVisibilityMenu,
} from "@delpi/plugin-ui/index";

import type { TableColumnKey } from "../utils/tableColumns";
import { TABLE_COLUMNS } from "../utils/tableColumns";

type TableColumnSettingsProps = {
  visibility: Record<TableColumnKey, boolean>;
  onToggleColumn: (key: TableColumnKey, visible: boolean) => void;
  onReset: () => void;
};

export function TableColumnSettings({
  visibility,
  onToggleColumn,
  onReset,
}: TableColumnSettingsProps) {
  return (
    <TableColumnVisibilityMenu
      columns={TABLE_COLUMNS}
      visibility={visibility}
      onToggleColumn={(key, visible) => onToggleColumn(key as TableColumnKey, visible)}
      onReset={onReset}
      labels={DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS}
    />
  );
}
