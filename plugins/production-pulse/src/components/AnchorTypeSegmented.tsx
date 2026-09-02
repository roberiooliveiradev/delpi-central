import { PpFieldLabel, PpSegmentToggle } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import type { AnchorType } from "../types/form";

type AnchorTypeSegmentedProps = {
  value: AnchorType;
  onChange: (value: AnchorType) => void;
  stacked?: boolean;
};

const OPTIONS = [
  { value: "work_center" as const, label: "Posto PCP" },
  { value: "equipment" as const, label: "Equipamento" },
  { value: "machine" as const, label: "Máquina" },
  { value: "area" as const, label: "Área" },
  { value: "standalone" as const, label: "Avulso" },
];

export function AnchorTypeSegmented({ value, onChange, stacked }: AnchorTypeSegmentedProps) {
  return (
    <div className="pp-anchor-segmented">
      <PpFieldLabel label="Tipo de amarração" hint={PP_HELP.form.anchorType} />
      <PpSegmentToggle
        ariaLabel="Tipo de amarração"
        direction={stacked ? "column" : "row"}
        value={value}
        onChange={(next) => onChange(next as AnchorType)}
        options={OPTIONS}
      />
    </div>
  );
}
