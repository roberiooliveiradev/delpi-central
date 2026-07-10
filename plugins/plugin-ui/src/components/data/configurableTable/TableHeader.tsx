import type { ReactNode } from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";

export type TableHeaderCellProps = {
  children: ReactNode;
};

export function TableHeaderCell({ children }: TableHeaderCellProps) {
  const cn = useConfigurableTableClasses();
  return <th className={cn.headerCell}>{children}</th>;
}

export type TableHeaderProps = {
  visible?: boolean;
  children: ReactNode;
};

export function TableHeader({ visible = true, children }: TableHeaderProps) {
  const cn = useConfigurableTableClasses();
  if (!visible) return null;
  return (
    <thead className={cn.header}>
      <tr className={`${cn.row} ${cn.rowHeader}`}>{children}</tr>
    </thead>
  );
}
