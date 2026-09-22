import { HelpTooltip } from "@delpi/plugin-ui/index";

import { TmStatusBadge } from "../../components/tmChromeUi";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";

const H = TM_HELP_TOOLTIPS.resultados;

/**
 * Compact provenance legend — presentation only.
 * OBSERVADO omitted: no canonical contract for that label in this surface.
 */
export function ResultsProvenanceLegend() {
  return (
    <div
      className="tm-processo-results-legend"
      role="note"
      aria-label="Natureza dos dados"
    >
      <span className="tm-processo-results-legend__label">
        Natureza dos dados
        <HelpTooltip content={H.naturezaLegenda} ariaLabel="Ajuda: Natureza dos dados" />
      </span>
      <ul className="tm-processo-results-legend__list">
        <li>
          <TmStatusBadge label="INFORMADO" variant="neutral" />
          <span>registrado na referência</span>
        </li>
        <li>
          <TmStatusBadge label="PROPOSTO" variant="neutral" />
          <span>cenário ainda não realizado</span>
        </li>
        <li>
          <TmStatusBadge label="CALCULADO" variant="neutral" />
          <span>derivado automaticamente</span>
        </li>
      </ul>
    </div>
  );
}
