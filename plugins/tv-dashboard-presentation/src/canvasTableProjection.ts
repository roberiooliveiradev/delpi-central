/**
 * Projeção de dados na Grade (`canvas_table`) — espelho 4P.
 * Fonte no bloco (`dataSourceId`); campo por célula (`dataRef`).
 */

import {
  CANVAS_TABLE_SPARKLINE_MAX_POINTS,
  CANVAS_TABLE_SPARKLINE_MIN_POINTS,
  normalizeCanvasTableCell,
  type CanvasTableCell,
  type CanvasTableCellRef,
} from "./comunicadoCanvasTable";
import type {
  ComunicadoBlock,
  ComunicadoCanvasTableBlock,
  ComunicadoDataResolved,
  ComunicadoTextDataRef,
} from "./comunicadoTypes";
import {
  parseProjectionNumber,
  resolveProjectedField,
  suggestDefaultAggregationForField,
  suggestPreferredProjectionField,
} from "./fieldValueProjection";
import {
  formatTextProjectionValue,
  normalizeTextDataRef,
  resolveTextDataRefValue,
  suggestDefaultTextProjection,
} from "./textViewProjection";
import { discoverResolvedFieldOptions } from "./viewProjection";

export function isCanvasTableDataBoundBlockType(type: string): boolean {
  return type === "canvas_table";
}

export function isCanvasTableDataBoundBlock(
  block: { type: string },
): block is ComunicadoCanvasTableBlock {
  return block.type === "canvas_table";
}

export function canvasTableHasDataBinding(
  block: Pick<ComunicadoCanvasTableBlock, "dataSourceId" | "cells">,
): boolean {
  if (block.dataSourceId?.trim()) return true;
  return block.cells.some((row) =>
    row.some((cell) => Boolean(normalizeCanvasTableCell(cell).dataRef?.field?.trim())),
  );
}

export function canvasTableCellHasDataRef(cell: CanvasTableCell | unknown): boolean {
  return Boolean(normalizeCanvasTableCell(cell).dataRef?.field?.trim());
}

export type CanvasTableCellDisplay = {
  text: string;
  color?: string;
  series?: number[];
  value?: number | null;
  fromData: boolean;
};

/** Resolve display de uma célula (estático ou dataRef + resolved). */
export function resolveCanvasTableCellDisplay(
  cell: CanvasTableCell | unknown,
  resolved?: ComunicadoDataResolved,
): CanvasTableCellDisplay {
  const normalized = normalizeCanvasTableCell(cell);
  const ref = normalizeTextDataRef(normalized.dataRef);
  if (!ref) {
    if (normalized.kind === "number" && normalized.value != null) {
      return {
        text: formatTextProjectionValue(
          normalized.value,
          mapNumberFormatToTextFormat(normalized.format),
        ),
        value: normalized.value,
        fromData: false,
      };
    }
    if (normalized.kind === "sparkline") {
      return {
        text:
          normalized.value != null
            ? formatTextProjectionValue(
                normalized.value,
                mapNumberFormatToTextFormat(normalized.format),
              )
            : normalized.text ?? "",
        series: normalized.series,
        value: normalized.value ?? null,
        fromData: false,
      };
    }
    return { text: normalized.text ?? "", fromData: false };
  }

  const wantsSeries =
    normalized.kind === "sparkline" || ref.aggregation === "list";
  if (wantsSeries) {
    const projected = resolveProjectedField(resolved, ref.field, "list");
    if (projected.kind === "empty") {
      return {
        text: normalized.text?.trim() || "—",
        series: normalized.series,
        value: normalized.value ?? null,
        fromData: true,
      };
    }
    const series = projected.values
      .map((v) => parseProjectionNumber(v))
      .filter((n): n is number => n != null)
      .slice(0, CANVAS_TABLE_SPARKLINE_MAX_POINTS);
    const anchor = series[series.length - 1] ?? null;
    const displayText =
      anchor != null
        ? formatTextProjectionValue(anchor, ref.format ?? "number")
        : normalized.text?.trim() || "—";
    const tone = resolveTextDataRefValue(
      resolved,
      { ...ref, aggregation: "first" },
      displayText,
    );
    return {
      text: displayText,
      color: tone.color,
      series: series.length >= 2 ? series : normalized.series,
      value: anchor,
      fromData: true,
    };
  }

  const { text, color } = resolveTextDataRefValue(
    resolved,
    ref,
    normalized.text?.trim() || "—",
  );
  const numeric = parseProjectionNumber(text);
  return {
    text,
    color,
    value: numeric,
    fromData: true,
  };
}

function mapNumberFormatToTextFormat(
  format: CanvasTableCell["format"],
): "number" | "percent" | "currency" | "raw" {
  if (format === "percent") return "percent";
  if (format === "currency") return "currency";
  if (format === "plain") return "raw";
  return "number";
}

export type BuildCanvasTableDataLinkPatchInput = {
  dataSourceId: string;
  resolved?: ComunicadoDataResolved;
  catalogFields?: Array<{ field: string; label: string }>;
  /** Célula alvo para sugerir dataRef (opcional). */
  targetCell?: CanvasTableCellRef | null;
  existingCells?: CanvasTableCell[][];
};

/** Liga a fonte ao bloco; se houver célula alvo sem dataRef, sugere campo. */
export function buildCanvasTableDataLinkPatch(
  input: BuildCanvasTableDataLinkPatchInput,
): Partial<ComunicadoCanvasTableBlock> {
  const { dataSourceId, resolved, catalogFields, targetCell, existingCells } = input;
  const patch: Partial<ComunicadoCanvasTableBlock> = { dataSourceId };
  if (!targetCell || !existingCells) return patch;
  const current = normalizeCanvasTableCell(
    existingCells[targetCell.row]?.[targetCell.col],
  );
  if (current.dataRef?.field?.trim()) return patch;
  const suggested = suggestDefaultTextProjection(resolved, catalogFields);
  if (!suggested) return patch;
  const dataRef: ComunicadoTextDataRef = {
    field: suggested.field,
    aggregation: suggested.aggregation,
    format: suggested.format,
  };
  const cells = existingCells.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
  const kind =
    current.kind === "sparkline"
      ? "sparkline"
      : suggested.format === "raw"
        ? "text"
        : "number";
  cells[targetCell.row]![targetCell.col] = {
    ...current,
    kind,
    dataRef:
      kind === "sparkline"
        ? { ...dataRef, aggregation: "list" }
        : dataRef,
  };
  patch.cells = cells;
  return patch;
}

export type ApplyCanvasTableDataRefScope = "cell" | "column" | "body";

/** Aplica (ou remove) dataRef em uma célula, coluna ou corpo da grade. */
export function applyCanvasTableDataRef(
  block: ComunicadoCanvasTableBlock,
  cellRef: CanvasTableCellRef,
  dataRef: ComunicadoTextDataRef | null,
  scope: ApplyCanvasTableDataRefScope = "cell",
): ComunicadoCanvasTableBlock {
  const ref = dataRef ? normalizeTextDataRef(dataRef) : undefined;
  const cells = block.cells.map((row, rowIndex) =>
    row.map((raw, colIndex) => {
      const cell = normalizeCanvasTableCell(raw);
      const inScope =
        scope === "cell"
          ? rowIndex === cellRef.row && colIndex === cellRef.col
          : scope === "column"
            ? colIndex === cellRef.col && !(block.headerRow && rowIndex === 0)
            : !(block.headerRow && rowIndex === 0);
      if (!inScope) return cell;
      if (!ref) {
        const next = { ...cell };
        delete next.dataRef;
        return next;
      }
      const kind =
        cell.kind === "sparkline"
          ? "sparkline"
          : ref.format === "raw"
            ? "text"
            : cell.kind === "text" && !ref.format
              ? "text"
              : cell.kind === "text"
                ? "number"
                : cell.kind;
      return {
        ...cell,
        kind,
        dataRef:
          kind === "sparkline"
            ? { ...ref, aggregation: ref.aggregation ?? "list" }
            : ref,
      };
    }),
  );
  return { ...block, cells };
}

export function suggestCanvasTableCellDataRef(
  resolved: ComunicadoDataResolved | undefined,
  catalogFields?: Array<{ field: string; label: string }>,
  preferSeries = false,
): ComunicadoTextDataRef | undefined {
  const fields = discoverResolvedFieldOptions(resolved, catalogFields);
  if (fields.length === 0) return undefined;
  const field =
    (preferSeries
      ? suggestPreferredProjectionField(resolved, fields)
      : suggestPreferredProjectionField(resolved, fields)) ?? fields[0]?.field;
  if (!field) return undefined;
  if (preferSeries) {
    return { field, aggregation: "list", format: "number" };
  }
  return {
    field,
    aggregation: suggestDefaultAggregationForField(resolved, field),
    format: "number",
  };
}

export function syncCanvasTableBlocksWithResolved(
  blocks: ComunicadoBlock[],
  resolvedBySourceId: Record<string, ComunicadoDataResolved | undefined>,
): { next: ComunicadoBlock[]; changedIds: string[] } {
  const changedIds: string[] = [];
  const next = blocks.map((block) => {
    if (!isCanvasTableDataBoundBlock(block)) return block;
    if (!canvasTableHasDataBinding(block)) return block;
    const sourceId = block.dataSourceId?.trim();
    if (!sourceId) return block;
    const resolved = resolvedBySourceId[sourceId];
    if (!resolved) return block;
    // Materializa dataRef só quando já há células ligadas sem campo (não inventa coluna inteira).
    let touched = false;
    const cells = block.cells.map((row) =>
      row.map((raw) => {
        const cell = normalizeCanvasTableCell(raw);
        if (!cell.dataRef) return cell;
        if (cell.dataRef.field?.trim()) return cell;
        const suggested = suggestCanvasTableCellDataRef(
          resolved,
          undefined,
          cell.kind === "sparkline",
        );
        if (!suggested) return cell;
        touched = true;
        return { ...cell, dataRef: suggested };
      }),
    );
    if (!touched) return block;
    changedIds.push(block.id);
    return { ...block, cells };
  });
  return { next, changedIds };
}

/** Garante série mínima para sparkline ligado (placeholder até o resolved chegar). */
export function ensureSparklineSeriesFloor(series: number[] | undefined): number[] | undefined {
  if (!series?.length) return undefined;
  if (series.length >= CANVAS_TABLE_SPARKLINE_MIN_POINTS) return series;
  return series;
}
