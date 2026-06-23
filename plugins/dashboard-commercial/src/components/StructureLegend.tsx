import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "./HelpTooltip";

export function StructureLegend() {
  return (
    <div className="dc-structure-legend" aria-label="Legenda da estrutura do produto">
      <FieldLabel
        label="Código"
        hint={COMMERCIAL_HELP_TOOLTIPS.detail.structureCode}
      />
      <FieldLabel
        label="Descrição"
        hint={COMMERCIAL_HELP_TOOLTIPS.detail.structureDescription}
      />
      <FieldLabel label="Tipo" hint={COMMERCIAL_HELP_TOOLTIPS.detail.structureType} />
      <FieldLabel
        label="Quantidade"
        hint={COMMERCIAL_HELP_TOOLTIPS.detail.structureQuantity}
      />
    </div>
  );
}
