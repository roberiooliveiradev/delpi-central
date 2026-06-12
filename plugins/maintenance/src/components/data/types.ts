import type { ReactNode } from "react";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
  align?: "left" | "right" | "center";
  /** Impede propagação do clique da linha (ex.: coluna de ações). */
  interactive?: boolean;
};
