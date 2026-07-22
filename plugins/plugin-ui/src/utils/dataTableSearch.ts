export type DataTableSearchColumn<T> = {
  render: (row: T) => unknown;
  sortValue?: (row: T) => string | number | boolean | null | undefined;
};

function cellSearchFragment(value: unknown): string {
  if (value == null || value === false) return "";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "";
}

/**
 * Haystack de busca local: usa o retorno primitivo de `render`;
 * se a célula for JSX/nó React, cai em `sortValue` (ex.: badge + código).
 */
export function buildDataTableSearchText<T>(
  row: T,
  columns: ReadonlyArray<DataTableSearchColumn<T>>,
): string {
  return columns
    .map((column) => {
      const fromRender = cellSearchFragment(column.render(row));
      if (fromRender) return fromRender;
      if (column.sortValue) {
        return cellSearchFragment(column.sortValue(row));
      }
      return "";
    })
    .join(" ")
    .toLowerCase();
}
