import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "@delpi/plugin-ui";

export function StructureLegend() {
  return (
    <div className="lmps-structure-legend" aria-label="Legenda da estrutura do produto">
      <FieldLabel
        label="Código"
        hint={LMPS_HELP_TOOLTIPS.detail.structureCode} className="lmps-field__label"   />
      <FieldLabel
        label="Descrição"
        hint={LMPS_HELP_TOOLTIPS.detail.structureDescription} className="lmps-field__label"   />
      <FieldLabel label="Tipo" hint={LMPS_HELP_TOOLTIPS.detail.structureType} className="lmps-field__label" />
      <FieldLabel
        label="Quantidade"
        hint={LMPS_HELP_TOOLTIPS.detail.structureQuantity} className="lmps-field__label"   />
    </div>
  );
}
