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
  if (existing?.length) return existing.map((column) => ({ ...column }));

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
  const normalizedWidth =
    widthPct == null || widthPct <= 0
      ? undefined
      : Math.max(1, Math.min(100, Math.round(widthPct * 10) / 10));

  return {
    ...block.tableProjection,
    columns: resolveEditableTableProjectionColumns(block).map((column) => {
      if (column.key !== columnKey) return column;
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
