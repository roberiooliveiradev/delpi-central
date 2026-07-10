import type { ReactNode } from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";

export type TableCellProps = {
  children: ReactNode;
};

export function TableCell({ children }: TableCellProps) {
  const cn = useConfigurableTableClasses();
  return <td className={cn.cell}>{children}</td>;
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
