import {
  DataTable as BaseDataTable,
  type DashboardDataTableProps,
} from "@delpi/plugin-ui/index";

import {
  ENGINEERING_DATA_TABLE_CLASSES,
  ENGINEERING_DATA_TABLE_LABELS,
} from "../../../ui/engineeringUi";

export type { DataTableColumn } from "@delpi/plugin-ui/index";

/** DataTable canônica do Portal Engenharia. */
export function DataTable<T>(props: DashboardDataTableProps<T>) {
  return (
    <BaseDataTable
      classNames={ENGINEERING_DATA_TABLE_CLASSES}
      labels={ENGINEERING_DATA_TABLE_LABELS}
      {...props}
    />
  );
}
