import type {
  CSSProperties,
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
          />
          <span
            className={`${cn.columnResizeHandle} ${cn.columnResizeHandle}--bottom`}
            role="separator"
            aria-orientation="vertical"
            data-column-resize-handle="bottom"
            onPointerDown={startColumnResize}
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
