import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckRangeField } from "./deck/DeckRangeField";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";

type Props = {
  id?: string;
  value: number;
  onChange: (radius: number) => void;
  max?: number;
  label?: string;
  /** Sem grupo próprio — para embutir em «Aparência». */
  embedded?: boolean;
};

/** Controle compartilhado de cantos arredondados (formas, chartArea, KPI, tabela). */
export function ShapeCornerRadiusControl({
  id = "td-shape-corner-radius",
  value,
  onChange,
  max = 64,
  label = "Cantos",
  embedded = false,
}: Props) {
  const control = (
    <DeckRangeField
      id={id}
      label="Raio (px)"
      hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.borderRadius}
      min={0}
      max={max}
      step={1}
      value={value}
      density="full"
      aria-label="Cantos arredondados em pixels"
      onChange={(next) => onChange(Math.max(0, Math.min(max, next)))}
    />
  );

  if (embedded) return control;

  return (
    <DeckRibbonGroup groupId="shape-corner" label={label} hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.borderRadius}>
      {control}
    </DeckRibbonGroup>
  );
}
