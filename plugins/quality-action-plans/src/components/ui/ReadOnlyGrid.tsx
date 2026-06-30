import type { ReactNode } from "react";

type ReadOnlyGridProps = {
  children: ReactNode;
};

/** Mesma grade do modo edição (`pac-form-grid`) para manter ordem e colunas alinhadas. */
export function ReadOnlyGrid({ children }: ReadOnlyGridProps) {
  return <div className="pac-form-grid">{children}</div>;
}
