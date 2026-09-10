import { Ban, Check, Link2 } from "lucide-react";

import { PpSectionHintLabel } from "../app/productionPulseUi";
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
          <PpSectionHintLabel
            label={PP_HELP.hub.linkModeTitle}
            hint={PP_HELP.hub.edgeModesHint}
            className="pp-hub-legend__title"
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
        <PpSectionHintLabel
          label={PP_HELP.hub.edgeModesTitle}
          hint={PP_HELP.hub.edgeModesHint}
          className="pp-hub-legend__title"
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
