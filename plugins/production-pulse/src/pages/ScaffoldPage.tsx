import { useEffect, useState } from "react";

import { fetchProductionPulseHealth } from "../api/productionPulseApi";
import { PP_HELP } from "../content/helpTooltips";
import { PpPageHero, PpStateBox, ppShellIcon } from "../app/productionPulseUi";

type ScaffoldPageProps = {
  mode: "panel" | "operator";
};

export function ScaffoldPage({ mode }: ScaffoldPageProps) {
  const [apiStatus, setApiStatus] = useState<string>("Verificando API…");
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchProductionPulseHealth()
      .then((health) => {
        if (cancelled) return;
        setApiStatus(`${health.service} — ${health.status}`);
        setApiError(null);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setApiError(error instanceof Error ? error.message : "Falha ao contactar a API.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const title = mode === "operator" ? "Operador · Pulso" : "Pulso de Produção";
  const hint = mode === "operator" ? PP_HELP.shell.modeOperator : PP_HELP.shell.heroTitle;

  return (
    <div className="pp-page-stack">
      <PpPageHero title={title} description={hint} badge={ppShellIcon} />
      <PpStateBox
        variant={apiError ? "error" : "empty"}
        title={apiError ? "API indisponível" : "Interface em construção"}
        message={
          apiError ??
          `${mode === "operator"
            ? "O hub operador será entregue na etapa E5.S5."
            : "O painel operacional será entregue na etapa E5.S2."} ${apiStatus}`
        }
      />
    </div>
  );
}
