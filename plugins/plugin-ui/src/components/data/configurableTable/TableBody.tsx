import type { ReactNode } from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";
import { bindTablePartPointer, type TableInteraction } from "../configurableTableParts";

export type TableCellProps = {
  children: ReactNode;
  rowIndex?: number;
  colIndex?: number;
  interaction?: TableInteraction | null;
};

export function TableCell({
  children,
  rowIndex = 0,
  colIndex = 0,
  interaction,
}: TableCellProps) {
  const cn = useConfigurableTableClasses();
  const ref = { kind: "cell" as const, rowIndex, colIndex };
  const { selected, onPointerDown, onDoubleClick, editing: _e, ...dom } = bindTablePartPointer(
    ref,
    interaction,
  );
  return (
    <td
      className={[cn.cell, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
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
};

export function TableRow({ rowIndex, children }: TableRowProps) {
  const cn = useConfigurableTableClasses();
  return (
    <tr className={cn.row} data-row-index={rowIndex}>
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
