import type { ReactNode } from "react";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
  align?: "left" | "right" | "center";
  /** Impede propagação do clique da linha (ex.: coluna de ações). */
  interactive?: boolean;
  sortable?: boolean;
  sortValue?: (row: T) => string | number | boolean | null | undefined;
};

export type ServerPaginationConfig = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};
