import type { DashboardDataTableSectionProps } from "@delpi/plugin-ui";

import { DataTableSection as BaseDataTableSection, type DataTableColumn } from "./dataTableUi";

export type SortDirection = "asc" | "desc";

export type DataTableSectionProps<T> = Omit<
  DashboardDataTableSectionProps<T>,
  "defaultSortKey" | "defaultSortDirection" | "clearClientSortOnThirdClick" | "hidePageSizeSelect"
> & {
  initialSort?: { key: string; dir: SortDirection } | null;
};

export function DataTableSection<T>({
  initialSort = null,
  ...props
}: DataTableSectionProps<T>) {
  return (
    <BaseDataTableSection
      hidePageSizeSelect
      clearClientSortOnThirdClick
      defaultSortKey={initialSort?.key ?? null}
      defaultSortDirection={initialSort?.dir ?? "asc"}
      {...props}
    />
  );
}

export type { DataTableColumn };
