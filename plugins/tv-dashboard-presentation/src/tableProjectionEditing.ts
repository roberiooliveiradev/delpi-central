import type { ComunicadoTablePartRef } from "./comunicadoTableParts";
import type { ComunicadoTableViewBlock } from "./comunicadoTypes";
import { resolveTableColumns } from "./tvDataPresentation";
import {
  applyViewProjection,
  type TableColumnProjection,
  type TableViewProjection,
} from "./viewProjection";

export function resolveEditableTableProjectionColumns(
  block: ComunicadoTableViewBlock,
): TableColumnProjection[] {
  const existing = block.tableProjection?.columns;
  if (existing?.length) {
    const resolved = applyViewProjection(block.resolved, {
      tableProjection: block.tableProjection,
    });
    const fromData = resolveTableColumns(resolved, resolved?.table?.rows ?? []);
    const known = new Set(existing.map((column) => column.key));
    const appended = fromData
      .filter((column) => !known.has(column.key))
      .map((column) => ({
        key: column.key,
        label: column.label,
        visible: true,
      }));
    return [...existing.map((column) => ({ ...column })), ...appended];
  }

  const resolved = applyViewProjection(block.resolved, {
    tableProjection: block.tableProjection,
  });
  const rows = resolved?.table?.rows ?? [];
  return resolveTableColumns(resolved, rows).map((column) => ({
    key: column.key,
    label: column.label,
    visible: true,
  }));
}

/** Chaves das colunas selecionadas (`headerCell` ou `cell`) na ordem das colunas visíveis. */
export function selectedTableProjectionColumnKeys(
  block: ComunicadoTableViewBlock,
  parts: readonly ComunicadoTablePartRef[],
): string[] {
  const visibleColumns = resolveEditableTableProjectionColumns(block).filter(
    (column) => column.visible !== false,
  );
  const indexes = new Set(
    parts.flatMap((part) =>
      part.kind === "headerCell" || part.kind === "cell" ? [part.colIndex] : [],
    ),
  );
  return visibleColumns.flatMap((column, colIndex) =>
    indexes.has(colIndex) ? [column.key] : [],
  );
}

/** Aplica formato de exibição às colunas selecionadas (spec + espelho legado). */
export function formatTableProjectionColumns(
  block: ComunicadoTableViewBlock,
  columnKeys: readonly string[],
  patch: {
    displayFormat: TableColumnProjection["displayFormat"];
    valueFormat?: TableColumnProjection["valueFormat"];
  },
): TableViewProjection {
  const keys = new Set(columnKeys);
  return {
    ...block.tableProjection,
    columns: resolveEditableTableProjectionColumns(block).map((column) => {
      if (!keys.has(column.key)) return column;
      const next: TableColumnProjection = {
        ...column,
        displayFormat: patch.displayFormat,
      };
      if (patch.valueFormat) next.valueFormat = patch.valueFormat;
      else delete next.valueFormat;
      return next;
    }),
  };
}

/** Distribui a largura igualmente entre as colunas visíveis (PowerPoint «Distribuir Colunas»). */
export function distributeTableProjectionColumnWidths(
  block: ComunicadoTableViewBlock,
): TableViewProjection {
  const columns = resolveEditableTableProjectionColumns(block);
  const visibleCount = columns.filter((column) => column.visible !== false).length;
  const evenWidthPct =
    visibleCount > 0 ? Math.round((100 / visibleCount) * 10) / 10 : undefined;

  return {
    ...block.tableProjection,
    columns: columns.map((column) => {
      const next = { ...column };
      if (column.visible === false || evenWidthPct == null) {
        delete next.widthPct;
      } else {
        next.widthPct = evenWidthPct;
      }
      return next;
    }),
  };
}

export function resizeTableProjectionColumn(
  block: ComunicadoTableViewBlock,
  columnKey: string,
  widthPct: number | undefined,
): TableViewProjection {
  return resizeTableProjectionColumns(block, [columnKey], widthPct);
}

/** Aplica a mesma largura a várias colunas (multi-seleção Excel-like). */
export function resizeTableProjectionColumns(
  block: ComunicadoTableViewBlock,
  columnKeys: readonly string[],
  widthPct: number | undefined,
): TableViewProjection {
  const keys = new Set(columnKeys);
  const normalizedWidth =
    widthPct == null || widthPct <= 0
      ? undefined
      : Math.max(1, Math.min(100, Math.round(widthPct * 10) / 10));

  return {
    ...block.tableProjection,
    columns: resolveEditableTableProjectionColumns(block).map((column) => {
      if (!keys.has(column.key)) return column;
      const next = { ...column };
      if (normalizedWidth == null) {
        delete next.widthPct;
      } else {
        next.widthPct = normalizedWidth;
      }
      return next;
    }),
  };
}
