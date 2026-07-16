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
