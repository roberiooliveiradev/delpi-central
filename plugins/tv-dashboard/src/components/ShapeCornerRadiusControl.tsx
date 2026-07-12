import { NativeTextControl } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";

type Props = {
  id?: string;
  value: number;
  onChange: (radius: number) => void;
  max?: number;
  label?: string;
};

/** Controle compartilhado de cantos arredondados (formas, chartArea, KPI, tabela). */
export function ShapeCornerRadiusControl({
  id = "td-shape-corner-radius",
  value,
  onChange,
  max = 64,
  label = "Cantos",
}: Props) {
  return (
    <DeckRibbonGroup label={label} hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.borderRadius}>
      <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--inline">
        <label className="td-deck-ribbon__field-label" htmlFor={id}>
          Raio (px)
        </label>
        <NativeTextControl
          id={id}
          type="number"
          className="td-deck-ribbon__number td-deck-ribbon__number--compact"
          min={0}
          max={max}
          step={1}
          aria-label="Cantos arredondados em pixels"
          value={value}
          onChange={(raw) => onChange(Math.max(0, Math.min(max, Number(raw) || 0)))}
        />
      </div>
    </DeckRibbonGroup>
  );
}
