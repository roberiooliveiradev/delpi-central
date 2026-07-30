import type { CSSProperties, ReactNode } from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";
import {
  bindTablePartPointer,
  resolveTableBodyCellPaintStyle,
  tablePartPaintToCss,
  type TableInteraction,
  type TablePartsMap,
} from "../configurableTableParts";

export type TableCellProps = {
  children: ReactNode;
  rowIndex?: number;
  colIndex?: number;
  columnSelected?: boolean;
  rowSelected?: boolean;
  interaction?: TableInteraction | null;
  tableParts?: TablePartsMap | null;
};

export function TableCell({
  children,
  rowIndex = 0,
  colIndex = 0,
  columnSelected = false,
  rowSelected = false,
  interaction,
  tableParts,
}: TableCellProps) {
  const cn = useConfigurableTableClasses();
  const ref = { kind: "cell" as const, rowIndex, colIndex };
  const { selected, onPointerDown, onDoubleClick, editing: _e, ...dom } = bindTablePartPointer(
    ref,
    interaction,
  );
  const paint = resolveTableBodyCellPaintStyle(tableParts, rowIndex, colIndex);
  const css = tablePartPaintToCss(paint);
  const style: CSSProperties | undefined = Object.keys(css).length > 0 ? css : undefined;

  return (
    <td
      className={[
        cn.cell,
        selected ? `${cn.root}__part--selected` : "",
        columnSelected ? cn.columnSelected : "",
        rowSelected ? `${cn.root}__row--selected` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={style}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {children}
    </td>
  );
}

export type TableRowProps = {
  rowIndex: number;
  children: ReactNode;
  /** Linha de totais (Excel Total Row). */
  total?: boolean;
  selected?: boolean;
  interaction?: TableInteraction | null;
};

export function TableRow({
  rowIndex,
  children,
  total = false,
  selected = false,
  interaction,
}: TableRowProps) {
  const cn = useConfigurableTableClasses();
  const ref = { kind: "row" as const, rowIndex };
  const bind = interaction
    ? bindTablePartPointer(ref, interaction)
    : { selected: false, onPointerDown: undefined, onDoubleClick: undefined };
  const rowSelected = selected || bind.selected;

  return (
    <tr
      className={[
        cn.row,
        total ? cn.rowTotal : "",
        rowSelected ? `${cn.root}__row--selected` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-row-index={rowIndex}
      data-table-total={total ? "true" : undefined}
      data-table-part={`row:${rowIndex}`}
      aria-selected={rowSelected ? true : undefined}
      onPointerDown={bind.onPointerDown}
      onDoubleClick={bind.onDoubleClick}
    >
      {children}
    </tr>
  );
}

export type TableBodyProps = {
  children: ReactNode;
};

export function TableBody({ children }: TableBodyProps) {
  const cn = useConfigurableTableClasses();
  return <tbody className={cn.body}>{children}</tbody>;
}
