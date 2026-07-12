import type { TvDataTableColumn } from "./tvDataPresentation";

/** Cap de UI / truncamento do bloco table_view (alinhado ao default do enrichment). */
export const TABLE_VIEW_MAX_ROWS_CAP = 90;
export const TABLE_VIEW_MAX_COLS_CAP = 24;

export function normalizeTableViewLimit(
  value: unknown,
  cap: number,
): number | undefined {
  if (value == null || value === "") return undefined;
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n) || n < 1) return undefined;
  return Math.min(Math.round(n), cap);
}

/**
 * Truncamento de exibição do `table_view` (linhas/colunas).
 * Vazio = mostra tudo que veio no `resolved` (com scroll no bloco).
 */
export function applyTableViewDisplayLimits<T extends Record<string, unknown>>(
  rows: T[],
  columns: TvDataTableColumn[],
  limits: { maxRows?: number; maxCols?: number },
): { rows: T[]; columns: TvDataTableColumn[] } {
  const maxRows = normalizeTableViewLimit(limits.maxRows, TABLE_VIEW_MAX_ROWS_CAP);
  const maxCols = normalizeTableViewLimit(limits.maxCols, TABLE_VIEW_MAX_COLS_CAP);
  const nextColumns = maxCols != null ? columns.slice(0, maxCols) : columns;
  const keys = new Set(nextColumns.map((column) => column.key));
  const slicedRows = maxRows != null ? rows.slice(0, maxRows) : rows;
  const nextRows =
    maxCols != null
      ? slicedRows.map((row) => {
          const next: Record<string, unknown> = {};
          for (const key of keys) {
            if (key in row) next[key] = row[key];
          }
          return next as T;
        })
      : slicedRows;
  return { rows: nextRows, columns: nextColumns };
}
