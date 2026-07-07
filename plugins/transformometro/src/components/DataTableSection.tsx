import type { ReactNode } from "react";

import {
  DataTableSection as BaseDataTableSection,
  DEFAULT_TABLE_PAGE_SIZE,
  type DataTableColumn,
} from "./dataTableUi";
import type { DashboardDataTableSectionProps } from "@delpi/plugin-ui";

export { DEFAULT_TABLE_PAGE_SIZE };
export type { DataTableColumn };

export type DataTableSectionProps<T> = DashboardDataTableSectionProps<T> & {
  filters?: ReactNode;
};

export function DataTableSection<T>({
  filters,
  toolbarExtra,
  hidePageSizeSelect = true,
  ...props
}: DataTableSectionProps<T>) {
  return (
    <BaseDataTableSection
      hidePageSizeSelect={hidePageSizeSelect}
      toolbarExtra={filters ?? toolbarExtra}
      {...props}
    />
  );
}
