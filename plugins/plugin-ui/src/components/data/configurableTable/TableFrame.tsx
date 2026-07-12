import type { ReactNode } from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";

export type TableFrameProps = {
  children: ReactNode;
  ariaLabel?: string;
};

/**
 * Área rolável da grade — scroll vertical/horizontal quando linhas/colunas
 * excedem o bloco; o título fica fora (não rola junto).
 */
export function TableFrame({ children, ariaLabel }: TableFrameProps) {
  const cn = useConfigurableTableClasses();
  return (
    <div className={cn.tableFrame}>
      <table className={cn.dataTable} aria-label={ariaLabel}>
        {children}
      </table>
    </div>
  );
}
