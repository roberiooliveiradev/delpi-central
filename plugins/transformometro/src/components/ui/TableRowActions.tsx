import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
};

/** Grupo horizontal de botões na coluna de ações (padrão Action Plans). */
export function TableRowActions({ children }: Props) {
  return (
    <div
      className="ds-table__actions"
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      {children}
    </div>
  );
}
