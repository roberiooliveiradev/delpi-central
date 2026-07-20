import { ESS_ROUTES } from "../constants/routes";
import { navigateEssPath } from "../hooks/useEssRouterPath";

type EssPageNavProps = {
  active: "monitor" | "analysis";
};

export function EssPageNav({ active }: EssPageNavProps) {
  return (
    <nav className="ess-page-nav" aria-label="Telas do estoque de segurança">
      <button
        type="button"
        className={
          active === "monitor"
            ? "ess-page-nav__link ess-page-nav__link--active"
            : "ess-page-nav__link"
        }
        onClick={() => navigateEssPath(ESS_ROUTES.home)}
      >
        Monitoramento
      </button>
      <button
        type="button"
        className={
          active === "analysis"
            ? "ess-page-nav__link ess-page-nav__link--active"
            : "ess-page-nav__link"
        }
        onClick={() => navigateEssPath(ESS_ROUTES.consumptionAnalysis)}
      >
        Análise de consumo
      </button>
    </nav>
  );
}
