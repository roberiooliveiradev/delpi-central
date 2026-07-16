import type { CSSProperties, ReactNode } from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";
import {
  bindTablePartPointer,
  resolveTablePartPaintStyle,
  type TableInteraction,
  type TablePartsMap,
} from "../configurableTableParts";

export type TableCellProps = {
  children: ReactNode;
  rowIndex?: number;
  colIndex?: number;
  columnSelected?: boolean;
  interaction?: TableInteraction | null;
  tableParts?: TablePartsMap | null;
};

export function TableCell({
  children,
  rowIndex = 0,
  colIndex = 0,
  columnSelected = false,
  interaction,
  tableParts,
}: TableCellProps) {
  const cn = useConfigurableTableClasses();
  const ref = { kind: "cell" as const, rowIndex, colIndex };
  const { selected, onPointerDown, onDoubleClick, editing: _e, ...dom } = bindTablePartPointer(
    ref,
    interaction,
  );
  const paint = resolveTablePartPaintStyle(tableParts, ref);
  const style: CSSProperties | undefined =
    paint.backgroundColor || paint.color || paint.fontWeight != null
      ? {
          ...(paint.backgroundColor ? { backgroundColor: paint.backgroundColor } : {}),
          ...(paint.color ? { color: paint.color } : {}),
          ...(paint.fontWeight != null ? { fontWeight: paint.fontWeight } : {}),
        }
      : undefined;

  return (
    <td
      className={[
        cn.cell,
        selected ? `${cn.root}__part--selected` : "",
        columnSelected ? cn.columnSelected : "",
      ].filter(Boolean).join(" ")}
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
};

export function TableRow({ rowIndex, children, total = false }: TableRowProps) {
  const cn = useConfigurableTableClasses();
  return (
    <tr
      className={[cn.row, total ? cn.rowTotal : ""].filter(Boolean).join(" ")}
      data-row-index={rowIndex}
      data-table-total={total ? "true" : undefined}
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
