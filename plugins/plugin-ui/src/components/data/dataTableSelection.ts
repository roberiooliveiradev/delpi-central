import { resolveDataCellSemantics } from "./dataCellSemantics";

export type DataTableCellRef = { rowIndex: number; columnKey: string };

export type DataTableSelection =
  | { kind: "column"; keys: string[] }
  | { kind: "row"; indices: number[] }
  | { kind: "cell"; cells: DataTableCellRef[] };

export type DataTableSelectionModifiers = {
  toggle?: boolean;
  range?: boolean;
};

function uniquePreserveOrder<T>(items: T[]): T[] {
  const seen = new Set<T>();
  const next: T[] = [];
  for (const item of items) {
    if (seen.has(item)) continue;
    seen.add(item);
    next.push(item);
  }
  return next;
}

function hasOwn(row: Record<string, unknown>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(row, key);
}

export function selectionFromColumnKey(columnKey: string | null | undefined): DataTableSelection | null {
  if (!columnKey) return null;
  return { kind: "column", keys: [columnKey] };
}

export function primaryColumnKey(selection: DataTableSelection | null | undefined): string | null {
  if (!selection) return null;
  if (selection.kind === "column") return selection.keys[0] ?? null;
  if (selection.kind === "cell") return selection.cells[0]?.columnKey ?? null;
  return null;
}

export function isColumnSelected(
  selection: DataTableSelection | null | undefined,
  columnKey: string,
): boolean {
  if (!selection) return false;
  if (selection.kind === "column") return selection.keys.includes(columnKey);
  if (selection.kind === "cell") return selection.cells.some((cell) => cell.columnKey === columnKey);
  return false;
}

export function isRowSelected(
  selection: DataTableSelection | null | undefined,
  rowIndex: number,
): boolean {
  if (!selection) return false;
  if (selection.kind === "row") return selection.indices.includes(rowIndex);
  if (selection.kind === "cell") return selection.cells.some((cell) => cell.rowIndex === rowIndex);
  return false;
}

export function isCellSelected(
  selection: DataTableSelection | null | undefined,
  rowIndex: number,
  columnKey: string,
): boolean {
  if (!selection) return false;
  if (selection.kind === "cell") {
    return selection.cells.some(
      (cell) => cell.rowIndex === rowIndex && cell.columnKey === columnKey,
    );
  }
  if (selection.kind === "column") return selection.keys.includes(columnKey);
  if (selection.kind === "row") return selection.indices.includes(rowIndex);
  return false;
}

function rangeKeys(columnKeys: string[], fromKey: string, toKey: string): string[] {
  const from = columnKeys.indexOf(fromKey);
  const to = columnKeys.indexOf(toKey);
  if (from < 0 || to < 0) return [toKey];
  const start = Math.min(from, to);
  const end = Math.max(from, to);
  return columnKeys.slice(start, end + 1);
}

function rangeIndices(from: number, to: number): number[] {
  const start = Math.min(from, to);
  const end = Math.max(from, to);
  return Array.from({ length: end - start + 1 }, (_, index) => start + index);
}

export function resolveColumnSelection(
  previous: DataTableSelection | null | undefined,
  columnKey: string,
  columnKeys: string[],
  modifiers: DataTableSelectionModifiers = {},
): DataTableSelection {
  const currentKeys = previous?.kind === "column" ? previous.keys : [];
  if (modifiers.range && currentKeys[0]) {
    return { kind: "column", keys: rangeKeys(columnKeys, currentKeys[0], columnKey) };
  }
  if (modifiers.toggle) {
    const exists = currentKeys.includes(columnKey);
    const keys = exists
      ? currentKeys.filter((key) => key !== columnKey)
      : [...currentKeys, columnKey];
    return { kind: "column", keys: uniquePreserveOrder(keys) };
  }
  return { kind: "column", keys: [columnKey] };
}

export function resolveRowSelection(
  previous: DataTableSelection | null | undefined,
  rowIndex: number,
  modifiers: DataTableSelectionModifiers = {},
): DataTableSelection {
  const current = previous?.kind === "row" ? previous.indices : [];
  if (modifiers.range && current[0] != null) {
    return { kind: "row", indices: rangeIndices(current[0], rowIndex) };
  }
  if (modifiers.toggle) {
    const exists = current.includes(rowIndex);
    const indices = exists
      ? current.filter((index) => index !== rowIndex)
      : [...current, rowIndex];
    return { kind: "row", indices: uniquePreserveOrder(indices).sort((a, b) => a - b) };
  }
  return { kind: "row", indices: [rowIndex] };
}

export function resolveCellSelection(
  previous: DataTableSelection | null | undefined,
  cell: DataTableCellRef,
  modifiers: DataTableSelectionModifiers = {},
): DataTableSelection {
  const current = previous?.kind === "cell" ? previous.cells : [];
  if (modifiers.range && current[0]) {
    const rowIndices = rangeIndices(current[0].rowIndex, cell.rowIndex);
    const columnKeys = [current[0].columnKey, cell.columnKey];
    // Range retangular simples entre âncora e alvo (mesma coluna ou duas).
    const cols =
      current[0].columnKey === cell.columnKey
        ? [cell.columnKey]
        : uniquePreserveOrder(columnKeys);
    const cells: DataTableCellRef[] = [];
    for (const rowIndex of rowIndices) {
      for (const columnKey of cols) {
        cells.push({ rowIndex, columnKey });
      }
    }
    return { kind: "cell", cells };
  }
  if (modifiers.toggle) {
    const exists = current.some(
      (item) => item.rowIndex === cell.rowIndex && item.columnKey === cell.columnKey,
    );
    const cells = exists
      ? current.filter(
          (item) => !(item.rowIndex === cell.rowIndex && item.columnKey === cell.columnKey),
        )
      : [...current, cell];
    return { kind: "cell", cells };
  }
  return { kind: "cell", cells: [cell] };
}

export function selectionToTsv(
  selection: DataTableSelection | null | undefined,
  rows: Array<Record<string, unknown>>,
  columnKeys: string[],
): string {
  if (!selection || rows.length === 0 || columnKeys.length === 0) return "";

  if (selection.kind === "column") {
    const keys = selection.keys.filter((key) => columnKeys.includes(key));
    if (keys.length === 0) return "";
    const header = keys.join("\t");
    const body = rows
      .map((row) =>
        keys
          .map((key) => stringifyCell(row[key], hasOwn(row, key)))
          .join("\t"),
      )
      .join("\n");
    return `${header}\n${body}`;
  }

  if (selection.kind === "row") {
    const indices = selection.indices.filter((index) => index >= 0 && index < rows.length);
    if (indices.length === 0) return "";
    const header = columnKeys.join("\t");
    const body = indices
      .map((index) => {
        const row = rows[index] ?? {};
        return columnKeys
          .map((key) => stringifyCell(row[key], hasOwn(row, key)))
          .join("\t");
      })
      .join("\n");
    return `${header}\n${body}`;
  }

  const cells = selection.cells.filter(
    (cell) =>
      cell.rowIndex >= 0 &&
      cell.rowIndex < rows.length &&
      columnKeys.includes(cell.columnKey),
  );
  if (cells.length === 0) return "";
  if (cells.length === 1) {
    const cell = cells[0]!;
    const row = rows[cell.rowIndex] ?? {};
    return stringifyCell(row[cell.columnKey], hasOwn(row, cell.columnKey));
  }
  const rowSet = uniquePreserveOrder(cells.map((cell) => cell.rowIndex)).sort((a, b) => a - b);
  const colSet = uniquePreserveOrder(
    cells.map((cell) => cell.columnKey).filter((key) => columnKeys.includes(key)),
  );
  return rowSet
    .map((rowIndex) => {
      const row = rows[rowIndex] ?? {};
      return colSet
        .map((key) => stringifyCell(row[key], hasOwn(row, key)))
        .join("\t");
    })
    .join("\n");
}

function stringifyCell(value: unknown, present: boolean): string {
  const text = resolveDataCellSemantics(value, { present }).copyText;
  if (/[\t\n\r"]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}
