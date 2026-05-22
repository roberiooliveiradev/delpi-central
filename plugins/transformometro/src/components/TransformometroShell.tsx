import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  /** Habilita impressão/PDF só desta página (oculta chrome do portal). */
  printRoot?: boolean;
};

/** Envolve todas as páginas do MFE com layout e animação consistentes. */
export function TransformometroShell({ children, printRoot = false }: Props) {
  const className = [
    "dashboard-transformometro",
    "dashboard-page",
    "ds-app-shell",
    printRoot ? "ds-print-root" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return <div className={className}>{children}</div>;
}
