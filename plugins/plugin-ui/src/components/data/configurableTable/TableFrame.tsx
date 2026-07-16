import type { ReactNode } from "react";

import type { PresentationTableColumn } from "../configurableTableOptions";
import { useConfigurableTableClasses } from "../configurableTableClasses";

export type TableFrameProps = {
  children: ReactNode;
  ariaLabel?: string;
  /** Quando há widthPct, renderiza `<colgroup>` e força layout fixo. */
  columns?: PresentationTableColumn[];
};

/**
 * Área rolável da grade — scroll vertical/horizontal quando linhas/colunas
 * excedem o bloco; o título fica fora (não rola junto).
 */
export function TableFrame({ children, ariaLabel, columns }: TableFrameProps) {
  const cn = useConfigurableTableClasses();
  const hasWidths = Boolean(columns?.some((column) => column.widthPct != null && column.widthPct > 0));
  return (
    <div className={cn.tableFrame}>
      <table className={cn.dataTable} aria-label={ariaLabel}>
        {hasWidths && columns ? (
          <colgroup>
            {columns.map((column) => {
              const pct =
                column.widthPct != null && column.widthPct > 0
                  ? Math.max(1, Math.min(100, column.widthPct))
                  : undefined;
              return (
                <col
                  key={column.key}
                  style={pct != null ? { width: `${pct}%` } : undefined}
                />
              );
            })}
          </colgroup>
        ) : null}
        {children}
      </table>
    </div>
  );
}
