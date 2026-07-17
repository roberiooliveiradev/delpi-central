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
  const { selected, onPointerDown, onDoubleClick, editing: _e, ...dom } = bindTablePartPointer(
    ref,
    interaction,
  );
  const paint = resolveTableHeaderCellPaintStyle(tableParts, colIndex);
  const style: CSSProperties | undefined =
    paint.backgroundColor || paint.color || paint.fontWeight != null
      ? {
          ...(paint.backgroundColor ? { backgroundColor: paint.backgroundColor } : {}),
          ...(paint.color ? { color: paint.color } : {}),
          ...(paint.fontWeight != null ? { fontWeight: paint.fontWeight } : {}),
        }
      : undefined;
  const resizable = selected && Boolean(interaction?.onColumnResize);

  const startColumnResize = (event: ReactPointerEvent<HTMLSpanElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const handle = event.currentTarget;
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
      const nextWidthPx = Math.max(8, startWidthPx + moveEvent.clientX - startX);
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

  return (
    <th
      className={[cn.headerCell, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      style={style}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {children}
      {resizable ? (
        <>
          <span
            className={`${cn.columnResizeHandle} ${cn.columnResizeHandle}--top`}
            role="separator"
            aria-orientation="vertical"
            data-column-resize-handle="top"
            onPointerDown={startColumnResize}
            onDoubleClick={autoFitColumn}
          />
          <span
            className={`${cn.columnResizeHandle} ${cn.columnResizeHandle}--bottom`}
            role="separator"
            aria-orientation="vertical"
            data-column-resize-handle="bottom"
            onPointerDown={startColumnResize}
            onDoubleClick={autoFitColumn}
          />
        </>
      ) : null}
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
