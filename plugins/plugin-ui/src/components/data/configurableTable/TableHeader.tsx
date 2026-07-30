import type {
  CSSProperties,
  MouseEvent as ReactMouseEvent,
  PointerEvent as ReactPointerEvent,
  ReactNode,
} from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";
import {
  bindTablePartPointer,
  getTablePartState,
  resolveTableHeaderCellPaintStyle,
  tablePartPaintToCss,
  type TableInteraction,
  type TablePartsMap,
} from "../configurableTableParts";

export type TableHeaderCellProps = {
  children: ReactNode;
  columnKey: string;
  colIndex?: number;
  interaction?: TableInteraction | null;
  tableParts?: TablePartsMap | null;
};

export function TableHeaderCell({
  children,
  columnKey,
  colIndex = 0,
  interaction,
  tableParts,
}: TableHeaderCellProps) {
  const cn = useConfigurableTableClasses();
  const ref = { kind: "headerCell" as const, colIndex };
  const { selected, onPointerDown, onDoubleClick, editing, ...dom } = bindTablePartPointer(
    ref,
    interaction,
  );
  const paint = resolveTableHeaderCellPaintStyle(tableParts, colIndex);
  const css = tablePartPaintToCss(paint);
  const style: CSSProperties | undefined = Object.keys(css).length > 0 ? css : undefined;
  const resizable = selected && Boolean(interaction?.onColumnResize);
  const displayLabel = typeof children === "string" ? children : String(children ?? "");

  const startColumnResize = (event: ReactPointerEvent<HTMLSpanElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const handle = event.currentTarget;
    const edge = handle.dataset.columnResizeEdge === "west" ? "west" : "east";
    const cell = handle.closest("th");
    const table = handle.closest("table");
    if (!cell || !table || !interaction?.onColumnResize) return;

    const startX = event.clientX;
    const startWidthPx = cell.getBoundingClientRect().width;
    const tableWidthPx = table.getBoundingClientRect().width;
    if (tableWidthPx <= 0) return;

    const pointerId = event.pointerId;
    handle.setPointerCapture?.(pointerId);

    const onPointerMove = (moveEvent: PointerEvent) => {
      const deltaX =
        edge === "west" ? startX - moveEvent.clientX : moveEvent.clientX - startX;
      const nextWidthPx = Math.max(8, startWidthPx + deltaX);
      const nextWidthPct = Math.max(
        1,
        Math.min(100, Math.round((nextWidthPx / tableWidthPx) * 1000) / 10),
      );
      interaction.onColumnResize?.(columnKey, nextWidthPct);
    };
    const finish = () => {
      handle.removeEventListener("pointermove", onPointerMove);
      handle.removeEventListener("pointerup", finish);
      handle.removeEventListener("pointercancel", finish);
      if (handle.hasPointerCapture?.(pointerId)) handle.releasePointerCapture(pointerId);
    };

    handle.addEventListener("pointermove", onPointerMove);
    handle.addEventListener("pointerup", finish);
    handle.addEventListener("pointercancel", finish);
  };

  /** Duplo clique na alça: mede a largura natural do conteúdo e ajusta a coluna. */
  const autoFitColumn = (event: ReactMouseEvent<HTMLSpanElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const handle = event.currentTarget;
    const cell = handle.closest("th");
    const table = handle.closest("table");
    const frame = table?.parentElement;
    if (!cell || !table || !frame || !interaction?.onColumnResize) return;

    const frameWidth = frame.getBoundingClientRect().width;
    if (frameWidth <= 0) return;

    const root = table.closest(`.${cn.root}`);
    const cols = Array.from(table.querySelectorAll("colgroup col")) as HTMLElement[];
    const previousColWidths = cols.map((col) => col.style.width);
    const hadWrap = root?.classList.contains(cn.rootWrap) ?? false;
    const hadFixedCols = root?.classList.contains(cn.rootFixedCols) ?? false;

    // Solta larguras fixas temporariamente para o navegador calcular a largura natural.
    root?.classList.remove(cn.rootWrap, cn.rootFixedCols);
    for (const col of cols) col.style.width = "";
    const naturalWidth = cell.getBoundingClientRect().width;
    cols.forEach((col, index) => {
      col.style.width = previousColWidths[index] ?? "";
    });
    if (hadWrap) root?.classList.add(cn.rootWrap);
    if (hadFixedCols) root?.classList.add(cn.rootFixedCols);

    if (naturalWidth <= 0) return;
    const nextWidthPct = Math.max(
      1,
      Math.min(100, Math.round((naturalWidth / frameWidth) * 1000) / 10),
    );
    interaction.onColumnResize(columnKey, nextWidthPct);
  };

  const resizeHandles: Array<{
    corner: "nw" | "ne" | "sw" | "se" | "w" | "e";
    edge: "west" | "east";
  }> = [
    { corner: "nw", edge: "west" },
    { corner: "ne", edge: "east" },
    { corner: "w", edge: "west" },
    { corner: "e", edge: "east" },
    { corner: "sw", edge: "west" },
    { corner: "se", edge: "east" },
  ];

  return (
    <th
      className={[
        cn.headerCell,
        selected ? `${cn.root}__part--selected` : "",
        resizable ? `${cn.root}__header-cell--resizable` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={style}
      {...dom}
      onPointerDown={editing ? undefined : onPointerDown}
      onDoubleClick={editing ? undefined : onDoubleClick}
    >
      {editing ? (
        <input
          className={`${cn.root}__header-edit`}
          defaultValue={displayLabel}
          autoFocus
          aria-label={`Rótulo da coluna ${columnKey}`}
          onPointerDown={(event) => event.stopPropagation()}
          onBlur={(event) => interaction?.onPartContentCommit?.(ref, event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              (event.target as HTMLInputElement).blur();
            }
            if (event.key === "Escape") {
              event.preventDefault();
              interaction?.onPartEditCancel?.();
            }
          }}
        />
      ) : (
        children
      )}
      {resizable && !editing
        ? resizeHandles.map(({ corner, edge }) => (
            <span
              key={corner}
              className={`${cn.columnResizeHandle} ${cn.columnResizeHandle}--${corner}`}
              role="separator"
              aria-orientation="vertical"
              aria-hidden="true"
              title={
                edge === "west"
                  ? "Redimensionar coluna pela esquerda"
                  : "Redimensionar coluna pela direita"
              }
              data-column-resize-handle={corner}
              data-column-resize-edge={edge}
              onPointerDown={startColumnResize}
              onDoubleClick={autoFitColumn}
            />
          ))
        : null}
    </th>
  );
}

export type TableHeaderProps = {
  visible?: boolean;
  children: ReactNode;
  interaction?: TableInteraction | null;
  tableParts?: TablePartsMap | null;
};

export function TableHeader({
  visible = true,
  children,
  interaction,
  tableParts,
}: TableHeaderProps) {
  const cn = useConfigurableTableClasses();
  const ref = { kind: "header" as const };
  const partVisible = getTablePartState(tableParts, ref)?.visible !== false;
  if (!visible || !partVisible) return null;

  const { selected, onPointerDown, onDoubleClick, editing: _e, ...dom } = bindTablePartPointer(
    ref,
    interaction,
  );

  return (
    <thead
      className={[cn.header, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      <tr className={`${cn.row} ${cn.rowHeader}`}>{children}</tr>
    </thead>
  );
}
