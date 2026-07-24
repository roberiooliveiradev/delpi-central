import type { ReactNode } from "react";
import { dataTableBemClasses } from "@delpi/plugin-ui/index";

type Props = {
  children: ReactNode;
};

const tableCn = dataTableBemClasses("ds");

/** Grupo horizontal de botões na coluna de ações (padrão Action Plans / kit). */
export function TableRowActions({ children }: Props) {
  return (
    <div
      className={tableCn.actions}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      {children}
    </div>
  );
}
