import { NativeTextControl } from "@delpi/plugin-ui/index";
import {
  cornerAdjustmentToBorderRadiusPx,
  patchShapeAdjustment,
  resolveShapeAdjustments,
  shapeAdjustmentSpecs,
  type ComunicadoBlockStyle,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckField } from "./deck/DeckField";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";

type Props = {
  kind: ComunicadoShapeKind;
  style?: ComunicadoBlockStyle;
  onChange: (patch: Partial<ComunicadoBlockStyle>) => void;
  /** Layout compacto na faixa Forma; campos empilhados no inspetor. */
  variant?: "ribbon" | "inspector";
  idPrefix?: string;
};

/**
 * Controles numéricos dos ajustes de geometria (equivalente aos handles amarelos do PowerPoint).
 */
export function ShapeAdjustmentsControl({
  kind,
  style,
  onChange,
  variant = "ribbon",
  idPrefix = "td-shape-adj",
}: Props) {
  const specs = shapeAdjustmentSpecs(kind);
  if (specs.length === 0) return null;

  const values = resolveShapeAdjustments(kind, style);

  const fields = specs.map((spec) => {
    const id = `${idPrefix}-${spec.id}`;
    const isCorner = spec.id === "corner" || spec.id === "round";
    const displayValue = isCorner
      ? (style?.borderRadius ?? cornerAdjustmentToBorderRadiusPx(values[spec.index], 64))
      : Math.round(values[spec.index] * 1000) / 1000;

    return (
      <div key={spec.id} className={variant === "ribbon" ? "td-deck-ribbon__toolbar td-deck-ribbon__toolbar--inline" : undefined}>
        {variant === "ribbon" ? (
          <label className="td-deck-ribbon__field-label" htmlFor={id}>
            {isCorner ? "Raio (px)" : spec.label}
          </label>
        ) : null}
        {variant === "inspector" ? (
          <DeckField
            id={id}
            label={isCorner ? "Cantos (px)" : spec.label}
            hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.shapeAdjustment}
          >
            <NativeTextControl
              id={id}
              type="number"
              min={isCorner ? 0 : spec.min}
              max={isCorner ? 128 : spec.max}
              step={isCorner ? 1 : 0.01}
              value={displayValue}
              onChange={(raw) => {
                const num = Number(raw) || 0;
                if (isCorner) {
                  const adj = Math.max(0, Math.min(0.5, num / 64));
                  onChange(patchShapeAdjustment(kind, style, spec.index, adj, 64));
                  return;
                }
                onChange(patchShapeAdjustment(kind, style, spec.index, num));
              }}
            />
          </DeckField>
        ) : (
          <NativeTextControl
            id={id}
            type="number"
            className="td-deck-ribbon__number td-deck-ribbon__number--compact"
            min={isCorner ? 0 : spec.min}
            max={isCorner ? 128 : spec.max}
            step={isCorner ? 1 : 0.01}
            aria-label={spec.label}
            value={displayValue}
            onChange={(raw) => {
              const num = Number(raw) || 0;
              if (isCorner) {
                const adj = Math.max(0, Math.min(0.5, num / 64));
                onChange(patchShapeAdjustment(kind, style, spec.index, adj, 64));
                return;
              }
              onChange(patchShapeAdjustment(kind, style, spec.index, num));
            }}
          />
        )}
      </div>
    );
  });

  if (variant === "inspector") {
    return <>{fields}</>;
  }

  return (
    <DeckRibbonGroup label="Ajustes da forma" hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.shapeAdjustment}>
      {fields}
    </DeckRibbonGroup>
  );
}
