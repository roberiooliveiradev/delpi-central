import { HelpTooltip } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";

/** Canvas edge modes: none | inherited (dashed) | explicit (solid). */
export function HubCanvasLegend() {
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
      <span className="pp-hub-legend__item pp-hub-legend__item--none">
        {PP_HELP.hub.edgeNone}
      </span>
      <span className="pp-hub-legend__item pp-hub-legend__item--dashed">
        {PP_HELP.hub.edgeDashed}
      </span>
      <span className="pp-hub-legend__item pp-hub-legend__item--solid">
        {PP_HELP.hub.edgeSolid}
      </span>
    </div>
  );
}
