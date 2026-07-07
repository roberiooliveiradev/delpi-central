import { Database } from "lucide-react";

import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { HelpTooltip } from "@delpi/plugin-ui";

export function TotvsSourceBanner() {
  return (
    <div className="dc-totvs-banner dc-no-print" role="note">
      <Database size={18} aria-hidden="true" />
      <div>
        <strong className="dc-totvs-banner__title">
          Origem: TOTVS Protheus
          <HelpTooltip
            content={COMMERCIAL_HELP_TOOLTIPS.actions.totvsBanner}
            ariaLabel="Ajuda: origem dos dados"
            className="dc-totvs-banner__help"
          />
        </strong>
        <p>
          ROL por unidade (filiais 01 e 02), taxa de conversão, OTD e novos
          negócios — metas do Indicadores Estratégicos.
        </p>
      </div>
    </div>
  );
}
