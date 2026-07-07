export function buildDataTableSearchText<T>(
  row: T,
  columns: ReadonlyArray<{ render: (row: T) => unknown }>,
): string {
  return columns
    .map((column) => {
      const value = column.render(row);
      if (value == null || value === false) return "";
      if (typeof value === "string" || typeof value === "number") {
        return String(value);
      }
      return "";
    })
    .join(" ")
    .toLowerCase();
}
