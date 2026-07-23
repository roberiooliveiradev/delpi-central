import type { CSSProperties, FocusEvent, KeyboardEvent, PointerEvent as ReactPointerEvent } from "react";

import { resolveCanvasTableCellDisplay } from "./canvasTableProjection";
import {
  buildCanvasTableSparklinePath,
  canvasTableCellDisplayRuns,
  canvasTableCellPlainText,
  inferCanvasTableCellFromText,
  mergeCanvasTableOptions,
  normalizeCanvasTableCell,
  resolveCanvasTableHostStyle,
  resolveColumnSparklineAxis,
  type CanvasTableCell,
  type CanvasTableCellRef,
} from "./comunicadoCanvasTable";
import { hasRichTextRuns } from "./comunicadoContentRuns";
import { ComunicadoTextRunsView } from "./ComunicadoTextRunsView";
import type { ComunicadoCanvasTableBlock } from "./comunicadoTypes";

export type ComunicadoCanvasTableInteraction = {
  selectedCell?: CanvasTableCellRef | null;
  onSelectCell?: (cell: CanvasTableCellRef | null) => void;
  onCellCommit?: (row: number, col: number, cell: CanvasTableCell) => void;
};

type Props = {
  block: ComunicadoCanvasTableBlock;
  editable?: boolean;
  /** Legado: texto puro. Preferir interaction.onCellCommit. */
  onCellChange?: (row: number, col: number, value: string) => void;
  interaction?: ComunicadoCanvasTableInteraction | null;
};

function CanvasSparkline({
  series,
  axis,
}: {
  series: number[];
  axis: { min: number; max: number } | null;
}) {
  const d = buildCanvasTableSparklinePath(series, 100, 28, axis?.min, axis?.max);
  if (!d) return null;
  return (
    <svg
      className="td-canvas-table__sparkline"
      viewBox="0 0 100 28"
      preserveAspectRatio="none"
      aria-hidden
    >
      <path
        d={d}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function ComunicadoCanvasTableView({
  block,
  editable = false,
  onCellChange,
  interaction = null,
}: Props) {
  const opts = mergeCanvasTableOptions(block.canvasTableOptions);
  const hostStyle = resolveCanvasTableHostStyle(block) as CSSProperties;
  const selected = interaction?.selectedCell ?? null;
  const resolvedCells = block.cells.map((row) =>
    row.map((raw) => {
      const cell = normalizeCanvasTableCell(raw);
      const display = resolveCanvasTableCellDisplay(cell, block.resolved);
      if (display.series?.length) {
        return { ...cell, kind: "sparkline" as const, series: display.series };
      }
      return cell;
    }),
  );

  function commitText(row: number, col: number, raw: string) {
    const next = inferCanvasTableCellFromText(raw);
    const prev = normalizeCanvasTableCell(block.cells[row]?.[col]);
    if (prev.kind === "number" && next.kind === "text" && next.text === canvasTableCellPlainText(prev)) {
      return;
    }
    interaction?.onCellCommit?.(row, col, next);
    onCellChange?.(row, col, canvasTableCellPlainText(next));
  }

  function onCellPointerDown(
    event: ReactPointerEvent<HTMLTableCellElement>,
    row: number,
    col: number,
  ) {
    if (!editable) return;
    event.stopPropagation();
    interaction?.onSelectCell?.({ row, col });
  }

  function onCellKeyDown(
    event: KeyboardEvent<HTMLTableCellElement>,
    row: number,
    col: number,
  ) {
    if (!editable || !interaction?.onSelectCell) return;
    const { key } = event;
    let nextRow = row;
    let nextCol = col;
    if (key === "ArrowUp") nextRow = Math.max(0, row - 1);
    else if (key === "ArrowDown") nextRow = Math.min(block.rows - 1, row + 1);
    else if (key === "ArrowLeft") nextCol = Math.max(0, col - 1);
    else if (key === "ArrowRight") nextCol = Math.min(block.cols - 1, col + 1);
    else if (key === "Tab") {
      event.preventDefault();
      if (event.shiftKey) {
        if (col > 0) nextCol = col - 1;
        else if (row > 0) {
          nextRow = row - 1;
          nextCol = block.cols - 1;
        }
      } else if (col < block.cols - 1) nextCol = col + 1;
      else if (row < block.rows - 1) {
        nextRow = row + 1;
        nextCol = 0;
      }
    } else if (key === "Enter") {
      event.preventDefault();
      nextRow = Math.min(block.rows - 1, row + 1);
    } else {
      return;
    }
    if (nextRow !== row || nextCol !== col) {
      interaction.onSelectCell({ row: nextRow, col: nextCol });
      const el = event.currentTarget
        .closest("table")
        ?.querySelector<HTMLElement>(`[data-cell-row="${nextRow}"][data-cell-col="${nextCol}"]`);
      el?.focus();
    }
  }

  return (
    <div
      className={[
        "td-canvas-table",
        opts.bandedRows ? "td-canvas-table--banded-rows" : "",
        opts.bandedColumns ? "td-canvas-table--banded-cols" : "",
        opts.borderStyle === "horizontal" ? "td-canvas-table--borders-h" : "",
        opts.borderStyle === "none" ? "td-canvas-table--borders-none" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-header-row={block.headerRow ? "true" : "false"}
      style={hostStyle}
    >
      <table>
        {opts.columnWidths?.length === block.cols ? (
          <colgroup>
            {opts.columnWidths.map((w, i) => (
              <col key={i} style={{ width: `${w}%` }} />
            ))}
          </colgroup>
        ) : null}
        <tbody>
          {block.cells.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((rawCell, colIndex) => {
                const cell = normalizeCanvasTableCell(rawCell);
                const isHeader = Boolean(block.headerRow && rowIndex === 0);
                const Cell = isHeader ? "th" : "td";
                const isSelected =
                  selected?.row === rowIndex && selected?.col === colIndex;
                const display = resolveCanvasTableCellDisplay(cell, block.resolved);
                const axis = resolveColumnSparklineAxis(resolvedCells, colIndex);
                const cellStyle: CSSProperties = {
                  ...(cell.style?.fontSize != null
                    ? { fontSize: `${cell.style.fontSize}px` }
                    : null),
                  ...(cell.style?.fontWeight != null
                    ? { fontWeight: cell.style.fontWeight }
                    : null),
                  ...(display.color
                    ? { color: display.color }
                    : cell.style?.color
                      ? { color: cell.style.color }
                      : null),
                  ...(cell.style?.backgroundColor
                    ? { backgroundColor: cell.style.backgroundColor }
                    : null),
                  ...(cell.style?.textAlign
                    ? { textAlign: cell.style.textAlign }
                    : null),
                };
                const displayText = display.text;
                const sparkSeries = display.series ?? cell.series;
                const bound = display.fromData;
                const allowEdit = editable && cell.kind !== "sparkline" && !bound;

                return (
                  <Cell
                    key={colIndex}
                    data-cell-row={rowIndex}
                    data-cell-col={colIndex}
                    data-cell-kind={cell.kind}
                    data-cell-bound={bound ? "true" : undefined}
                    className={[
                      isSelected ? "td-canvas-table__cell--selected" : "",
                      cell.kind === "sparkline" ? "td-canvas-table__cell--sparkline" : "",
                      cell.kind === "number" ? "td-canvas-table__cell--number" : "",
                      bound ? "td-canvas-table__cell--bound" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    style={cellStyle}
                    contentEditable={allowEdit}
                    suppressContentEditableWarning
                    tabIndex={editable ? 0 : undefined}
                    onPointerDown={(event) => onCellPointerDown(event, rowIndex, colIndex)}
                    onKeyDown={(event) => onCellKeyDown(event, rowIndex, colIndex)}
                    onBlur={(event: FocusEvent<HTMLTableCellElement>) => {
                      if (!allowEdit) return;
                      const value = event.currentTarget.textContent ?? "";
                      commitText(rowIndex, colIndex, value);
                    }}
                  >
                    {cell.kind === "sparkline" ? (
                      <span className="td-canvas-table__sparkline-wrap">
                        {sparkSeries && sparkSeries.length >= 2 ? (
                          <CanvasSparkline series={sparkSeries} axis={axis} />
                        ) : null}
                        {displayText ? (
                          <span className="td-canvas-table__sparkline-value">{displayText}</span>
                        ) : null}
                      </span>
                    ) : !allowEdit &&
                      hasRichTextRuns({ contentRuns: cell.contentRuns }) ? (
                      <ComunicadoTextRunsView
                        block={{
                          content: displayText,
                          contentRuns: canvasTableCellDisplayRuns(cell, displayText),
                        }}
                        as="span"
                      />
                    ) : (
                      displayText
                    )}
                  </Cell>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
