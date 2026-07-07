export type { DataTableColumn } from "@delpi/plugin-ui";

export type ServerPaginationConfig = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

/** Paginação + ordenação controladas pela API (sem sort/paginação client-side). */
export type ServerTableConfig = ServerPaginationConfig & {
  sortKey: string | null;
  sortDirection: "asc" | "desc";
  onSortChange: (columnKey: string) => void;
};
