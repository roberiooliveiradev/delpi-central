/** Sheet auxiliar header→key para reimport (XLSX). */
export function buildFieldKeyMapRows(
  columns: Array<{ key: string; label: string }>,
): string[][] {
  return [
    ["Cabeçalho", "Campo técnico"],
    ...columns.map((column) => [column.label || column.key, column.key]),
  ];
}
