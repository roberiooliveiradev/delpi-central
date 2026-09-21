import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  /** Habilita impressão/PDF só desta página (oculta chrome do portal). */
  printRoot?: boolean;
  /**
   * Preenche a altura do mount do Portal (contrato dashboard-page--fill).
   * Usar em superfícies com scroll interno (ex.: Sala de interação).
   */
  fillViewport?: boolean;
};

/** Envolve todas as páginas do MFE com layout e animação consistentes. */
export function TransformometroShell({
  children,
  printRoot = false,
  fillViewport = false,
}: Props) {
  const className = [
    "dashboard-transformometro",
    "dashboard-page",
    "ds-app-shell",
    fillViewport ? "dashboard-page--fill" : "",
    printRoot ? "ds-print-root" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className}>
      <div className="tm-page-sections">{children}</div>
    </div>
  );
}
