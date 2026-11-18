/** Área Processos do Portal Engenharia — catálogo de ferramentas de
 * Engenharia de Processos (plano V3 de balanceamento). Host próprio,
 * independente da Ficha do Produto: resolve `processes/...` para a
 * página da ferramenta sem passar por ProductsFeature. */

import { EngineeringEmptyState } from "../../ui/engineeringUi";
import { ProcessesPage } from "./ProcessesPage";
import { LineBalancingPage } from "./line-balancing/LineBalancingPage";

export function ProcessesFeature({
  relativePath,
  basePath,
}: {
  relativePath?: string;
  basePath?: string;
  getAccessToken?: () => string | undefined;
}) {
  const rest = (relativePath ?? "")
    .replace(/^processes\/?/, "")
    .replace(/^\/+|\/+$/g, "");

  if (rest === "") {
    return <ProcessesPage basePath={basePath} />;
  }
  if (rest === "line-balancing") {
    return <LineBalancingPage />;
  }
  return (
    <EngineeringEmptyState message="Ferramenta de Processos não encontrada." />
  );
}
