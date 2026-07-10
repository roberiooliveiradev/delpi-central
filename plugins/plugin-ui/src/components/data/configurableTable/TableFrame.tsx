import type { ReactNode } from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";

export type TableFrameProps = {
  children: ReactNode;
  ariaLabel?: string;
};

export function TableFrame({ children, ariaLabel }: TableFrameProps) {
  const cn = useConfigurableTableClasses();
  return (
    <table className={`${cn.dataTable} ${cn.tableFrame}`} aria-label={ariaLabel}>
      {children}
    </table>
  );
}
