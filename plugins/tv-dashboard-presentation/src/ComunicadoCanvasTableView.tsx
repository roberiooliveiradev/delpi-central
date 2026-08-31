import {
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type FocusEvent,
  type KeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";

import { resolveCanvasTableCellDisplay, resolveCanvasTableCellResolved } from "./canvasTableProjection";
import { resolveCanvasTableKeyboardAction } from "./canvasTableKeyboard";
import {
  resolveCanvasTableSelectionOverlayRects,
  type CanvasTableCellDomRect,
} from "./canvasTableSelectionOverlay";
import {
  buildCanvasTableSparklinePath,
  canvasTableCellDisplayRuns,
  canvasTableCellPlainText,
  commitCanvasTableCellText,
  mergeCanvasTableOptions,
  normalizeCanvasTableCell,
  resolveCanvasTableHostStyle,
  resolveCanvasTableRowHeightStyles,
  resolveColumnSparklineAxis,
  type CanvasTableCell,
  type CanvasTableCellRef,
} from "./comunicadoCanvasTable";
import { hasRichTextRuns } from "./comunicadoContentRuns";
import { ComunicadoTextRunsView } from "./ComunicadoTextRunsView";
import type { ComunicadoCanvasTableBlock } from "./comunicadoTypes";

export type ComunicadoCanvasTableInteraction = {
  selectedCells?: CanvasTableCellRef[];
  /** @deprecated Prefer `selectedCells`. */
  selectedCell?: CanvasTableCellRef | null;
  /**
   * Grade no editor: `false` = 1º clique sobe ao wrap (só container);
   * `true` = permite selecionar/editar célula. Omitido = legado (sempre célula).
   */
  blockSelected?: boolean;
  onSelectCell?: (request: {
    cell: CanvasTableCellRef;
    additive?: boolean;
    range?: boolean;
  }) => void;
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

function measureCellRects(host: HTMLElement): CanvasTableCellDomRect[] {
  const hostBox = host.getBoundingClientRect();
  const nodes = host.querySelectorAll<HTMLElement>("[data-cell-row][data-cell-col]");
  const rects: CanvasTableCellDomRect[] = [];
  nodes.forEach((node) => {
    const row = Number(node.dataset.cellRow);
    const col = Number(node.dataset.cellCol);
    if (!Number.isFinite(row) || !Number.isFinite(col)) return;
    const box = node.getBoundingClientRect();
    rects.push({
      row,
      col,
      left: box.left - hostBox.left,
      top: box.top - hostBox.top,
      width: box.width,
      height: box.height,
    });
  });
  return rects;
}

export function ComunicadoCanvasTableView({
  block,
  editable = false,
  onCellChange,
  interaction = null,
}: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [cellRects, setCellRects] = useState<CanvasTableCellDomRect[]>([]);
  const [editingCell, setEditingCell] = useState<CanvasTableCellRef | null>(null);
  const pendingReplaceRef = useRef<string | null>(null);
  const opts = mergeCanvasTableOptions(block.canvasTableOptions);
  const hostStyle = resolveCanvasTableHostStyle(block) as CSSProperties;
  const rowHeightStyles = resolveCanvasTableRowHeightStyles(opts.rowHeights, block.rows);
  const selectedCells =
    interaction?.selectedCells ??
    (interaction?.selectedCell ? [interaction.selectedCell] : []);
  const focusCell = selectedCells[selectedCells.length - 1] ?? null;
  const resolvedCells = block.cells.map((row) =>
    row.map((raw) => {
      const cell = normalizeCanvasTableCell(raw);
      const display = resolveCanvasTableCellDisplay(
        cell,
        resolveCanvasTableCellResolved(block, cell),
      );
      if (display.series?.length) {
        return { ...cell, kind: "sparkline" as const, series: display.series };
      }
      return cell;
    }),
  );

  const selectionKey = selectedCells.map((c) => `${c.row}:${c.col}`).join(",");

  useLayoutEffect(() => {
    if (!editable || !selectedCells.length) {
      setCellRects([]);
      return;
    }
    const host = hostRef.current;
    if (!host) return;
    setCellRects(measureCellRects(host));
  }, [
    editable,
    selectionKey,
    selectedCells.length,
    block.rows,
    block.cols,
    block.frame?.w,
    block.frame?.h,
    opts.columnWidths,
    opts.rowHeights,
  ]);

  useLayoutEffect(() => {
    if (!editingCell) return;
    const host = hostRef.current;
    if (!host) return;
    const el = host.querySelector<HTMLElement>(
      `[data-cell-row="${editingCell.row}"][data-cell-col="${editingCell.col}"]`,
    );
    if (!el) return;
    el.focus();
    const pending = pendingReplaceRef.current;
    pendingReplaceRef.current = null;
    if (pending != null) {
      el.textContent = pending;
      const sel = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(el);
      range.collapse(false);
      sel?.removeAllRanges();
      sel?.addRange(range);
    }
  }, [editingCell]);

  const overlay =
    editable && selectedCells.length
      ? resolveCanvasTableSelectionOverlayRects({
          cellRects,
          selectedCells,
          focus: focusCell,
        })
      : { range: null, focus: null };

  function commitText(row: number, col: number, raw: string) {
    const prev = normalizeCanvasTableCell(block.cells[row]?.[col]);
    const next = commitCanvasTableCellText(prev, raw);
    if (prev.kind === "number" && next.kind === "text" && next.text === canvasTableCellPlainText(prev)) {
      return;
    }
    interaction?.onCellCommit?.(row, col, next);
    onCellChange?.(row, col, canvasTableCellPlainText(next));
  }

  const allowCellSelection = interaction?.blockSelected !== false;

  function isCellEditing(row: number, col: number) {
    return Boolean(editingCell && editingCell.row === row && editingCell.col === col);
  }

  function focusCellAt(row: number, col: number) {
    hostRef.current
      ?.querySelector<HTMLElement>(`[data-cell-row="${row}"][data-cell-col="${col}"]`)
      ?.focus();
  }

  function selectAndMaybeEdit(
    cell: CanvasTableCellRef,
    opts: { additive?: boolean; range?: boolean; enterEdit?: boolean },
  ) {
    interaction?.onSelectCell?.({
      cell,
      additive: opts.additive,
      range: opts.range,
    });
    if (opts.enterEdit) setEditingCell(cell);
    else setEditingCell(null);
  }

  function onCellPointerDown(
    event: ReactPointerEvent<HTMLTableCellElement>,
    row: number,
    col: number,
    canEdit: boolean,
  ) {
    if (!editable) return;
    /* Container ainda não selecionado: deixa o wrap do bloco receber o gesto. */
    if (!allowCellSelection) return;
    event.stopPropagation();
    const sameFocus =
      focusCell?.row === row && focusCell?.col === col && !event.ctrlKey && !event.metaKey && !event.shiftKey;
    const enterEdit = canEdit && sameFocus && !isCellEditing(row, col);
    selectAndMaybeEdit(
      { row, col },
      {
        additive: event.ctrlKey || event.metaKey,
        range: event.shiftKey,
        enterEdit,
      },
    );
  }

  function onCellKeyDown(
    event: KeyboardEvent<HTMLTableCellElement>,
    row: number,
    col: number,
    canEdit: boolean,
  ) {
    if (!editable || !allowCellSelection) return;
    const mode = isCellEditing(row, col) ? "edit" : "navigate";
    const action = resolveCanvasTableKeyboardAction({
      key: event.key,
      shift: event.shiftKey,
      ctrl: event.ctrlKey,
      alt: event.altKey,
      meta: event.metaKey,
      mode,
      row,
      col,
      rows: block.rows,
      cols: block.cols,
    });

    if (action.type === "editCaret" || action.type === "ignore") return;

    if (action.type === "enterEdit") {
      if (!canEdit) return;
      event.preventDefault();
      if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
        pendingReplaceRef.current = event.key;
      }
      setEditingCell({ row, col });
      interaction?.onSelectCell?.({ cell: { row, col } });
      return;
    }

    if (action.type === "cancelEdit") {
      event.preventDefault();
      const prev = normalizeCanvasTableCell(block.cells[row]?.[col]);
      event.currentTarget.textContent = canvasTableCellPlainText(prev);
      setEditingCell(null);
      return;
    }

    if (action.type === "commitStay") {
      event.preventDefault();
      commitText(row, col, event.currentTarget.textContent ?? "");
      setEditingCell(null);
      return;
    }

    if (action.type === "commitMove" || action.type === "navigate") {
      event.preventDefault();
      if (action.type === "commitMove") {
        commitText(row, col, event.currentTarget.textContent ?? "");
      }
      setEditingCell(null);
      interaction?.onSelectCell?.({
        cell: action.next,
        range: action.type === "navigate" ? action.range : false,
      });
      focusCellAt(action.next.row, action.next.col);
    }
  }

  return (
    <div
      ref={hostRef}
      className={[
        "td-canvas-table",
        editable ? "td-canvas-table--editable" : "",
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
            <tr key={rowIndex} style={rowHeightStyles[rowIndex]}>
              {row.map((rawCell, colIndex) => {
                const cell = normalizeCanvasTableCell(rawCell);
                const isHeader = Boolean(block.headerRow && rowIndex === 0);
                const Cell = isHeader ? "th" : "td";
                const display = resolveCanvasTableCellDisplay(
                  cell,
                  resolveCanvasTableCellResolved(block, cell),
                );
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
                const canEdit =
                  editable &&
                  allowCellSelection &&
                  cell.kind !== "sparkline" &&
                  !bound;
                const editing = isCellEditing(rowIndex, colIndex);

                return (
                  <Cell
                    key={colIndex}
                    data-cell-row={rowIndex}
                    data-cell-col={colIndex}
                    data-cell-kind={cell.kind}
                    data-cell-bound={bound ? "true" : undefined}
                    className={[
                      cell.kind === "sparkline" ? "td-canvas-table__cell--sparkline" : "",
                      cell.kind === "number" ? "td-canvas-table__cell--number" : "",
                      bound ? "td-canvas-table__cell--bound" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    style={cellStyle}
                    contentEditable={editing}
                    suppressContentEditableWarning
                    tabIndex={editable && allowCellSelection ? 0 : undefined}
                    onPointerDown={(event) =>
                      onCellPointerDown(event, rowIndex, colIndex, canEdit)
                    }
                    onKeyDown={(event) =>
                      onCellKeyDown(event, rowIndex, colIndex, canEdit)
                    }
                    onBlur={(event: FocusEvent<HTMLTableCellElement>) => {
                      if (!editing) return;
                      const value = event.currentTarget.textContent ?? "";
                      commitText(rowIndex, colIndex, value);
                      setEditingCell(null);
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
                    ) : !editing &&
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
      {overlay.range ? (
        <div
          className="td-canvas-table__sel-range"
          aria-hidden
          style={{
            left: overlay.range.left,
            top: overlay.range.top,
            width: overlay.range.width,
            height: overlay.range.height,
          }}
        />
      ) : null}
      {overlay.focus &&
      (selectedCells.length > 1 ||
        (overlay.range &&
          (overlay.focus.width !== overlay.range.width ||
            overlay.focus.height !== overlay.range.height ||
            overlay.focus.left !== overlay.range.left ||
            overlay.focus.top !== overlay.range.top))) ? (
        <div
          className="td-canvas-table__sel-focus"
          aria-hidden
          style={{
            left: overlay.focus.left,
            top: overlay.focus.top,
            width: overlay.focus.width,
            height: overlay.focus.height,
          }}
        />
      ) : null}
    </div>
  );
}
