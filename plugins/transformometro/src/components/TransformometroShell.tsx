import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
};

/** Envolve todas as páginas do MFE com layout e animação consistentes. */
export function TransformometroShell({ children }: Props) {
  return <div className="dashboard-transformometro dashboard-page ds-app-shell">{children}</div>;
}
