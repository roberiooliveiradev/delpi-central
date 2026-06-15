import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "./HelpTooltip";

export function StructureLegend() {
  return (
    <div className="lmps-structure-legend" aria-label="Legenda da estrutura do produto">
      <FieldLabel
        label="Código"
        hint={LMPS_HELP_TOOLTIPS.detail.structureCode}
      />
      <FieldLabel
        label="Descrição"
        hint={LMPS_HELP_TOOLTIPS.detail.structureDescription}
      />
      <FieldLabel label="Tipo" hint={LMPS_HELP_TOOLTIPS.detail.structureType} />
      <FieldLabel
        label="Quantidade"
        hint={LMPS_HELP_TOOLTIPS.detail.structureQuantity}
      />
    </div>
  );
}
