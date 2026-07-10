import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "@delpi/plugin-ui/index";

export function StructureLegend() {
  return (
    <div className="dc-structure-legend" aria-label="Legenda da estrutura do produto">
      <FieldLabel
        label="Código"
        hint={COMMERCIAL_HELP_TOOLTIPS.detail.structureCode}
        className="dc-field__label"
      />
      <FieldLabel
        label="Descrição"
        hint={COMMERCIAL_HELP_TOOLTIPS.detail.structureDescription}
        className="dc-field__label"
      />
      <FieldLabel
        label="Tipo"
        hint={COMMERCIAL_HELP_TOOLTIPS.detail.structureType}
        className="dc-field__label"
      />
      <FieldLabel
        label="Quantidade"
        hint={COMMERCIAL_HELP_TOOLTIPS.detail.structureQuantity}
        className="dc-field__label"
      />
    </div>
  );
}
