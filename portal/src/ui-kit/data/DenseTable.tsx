// portal/src/ui-kit/data/DenseTable.tsx

import type { HTMLAttributes, ReactNode, TableHTMLAttributes } from "react";
import "./DenseTable.css";

export type DenseTableProps = HTMLAttributes<HTMLDivElement> & {
  toolbar?: ReactNode;
  empty?: ReactNode;
  /** Conteúdo da tabela: use <table> via children OU passe tableProps + children como tbody rows */
  children: ReactNode;
  tableProps?: TableHTMLAttributes<HTMLTableElement>;
  /** Se true, children são as linhas <tr> e o kit envolve em <table> */
  wrapTable?: boolean;
};

export function DenseTable({
  toolbar,
  empty,
  children,
  tableProps,
  wrapTable = false,
  className,
  ...rest
}: DenseTableProps) {
  const classes = ["portal-ui-dense", className ?? ""].filter(Boolean).join(" ");

  return (
    <div className={classes} {...rest}>
      {toolbar != null ? (
        <div className="portal-ui-dense__toolbar">{toolbar}</div>
      ) : null}

      <div className="portal-ui-dense__scroll">
        {wrapTable ? (
          <table className="portal-ui-dense__table" {...tableProps}>
            {children}
          </table>
        ) : (
          children
        )}
      </div>

      {empty != null ? <div className="portal-ui-dense__empty">{empty}</div> : null}
    </div>
  );
}
