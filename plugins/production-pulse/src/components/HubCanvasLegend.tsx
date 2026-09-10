import { Ban, Check, Link2 } from "lucide-react";

import { HelpTooltip } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";

type HubCanvasLegendProps = {
  linkModeActive?: boolean;
};

/** Canvas connections: solid OTA link in normal mode; candidate states in link mode. */
export function HubCanvasLegend({ linkModeActive = false }: HubCanvasLegendProps) {
  if (linkModeActive) {
    return (
      <div className="pp-hub-legend pp-hub-legend--compact" role="group" aria-label="Legenda do modo vínculo">
        <div className="pp-hub-legend__title-row">
          <span className="pp-hub-legend__title">{PP_HELP.hub.linkModeTitle}</span>
          <HelpTooltip
            content={PP_HELP.hub.edgeModesHint}
            ariaLabel="Ajuda: modo vínculo"
            placement="bottom"
          />
        </div>
        <span className="pp-hub-legend__item pp-hub-legend__item--compatible">
          <Link2 size={12} aria-hidden="true" /> {PP_HELP.hub.linkCompatible}
        </span>
        <span className="pp-hub-legend__item pp-hub-legend__item--incompatible">
          <Ban size={12} aria-hidden="true" /> Incompatível
        </span>
        <span className="pp-hub-legend__item pp-hub-legend__item--linked">
          <Check size={12} aria-hidden="true" /> {PP_HELP.hub.linkAlreadyAssigned}
        </span>
      </div>
    );
  }

  return (
    <div className="pp-hub-legend pp-hub-legend--compact" role="group" aria-label="Legenda das conexões">
      <div className="pp-hub-legend__title-row">
        <span className="pp-hub-legend__title">{PP_HELP.hub.edgeModesTitle}</span>
        <HelpTooltip
          content={PP_HELP.hub.edgeModesHint}
          ariaLabel="Ajuda: modos de conexão no mapa"
          placement="bottom"
        />
      </div>
      <span className="pp-hub-legend__item pp-hub-legend__item--solid">
        {PP_HELP.hub.edgeSolid}
      </span>
      <span className="pp-hub-legend__item pp-hub-legend__item--none">
        {PP_HELP.hub.edgeNone}
      </span>
    </div>
  );
}
