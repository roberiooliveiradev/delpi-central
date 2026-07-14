import {
  cornerAdjustmentToBorderRadiusPx,
  patchShapeAdjustment,
  resolveShapeAdjustments,
  shapeAdjustmentSpecs,
  type ComunicadoBlockStyle,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckRangeField } from "./deck/DeckRangeField";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";

type Props = {
  kind: ComunicadoShapeKind;
  style?: ComunicadoBlockStyle;
  onChange: (patch: Partial<ComunicadoBlockStyle>) => void;
  /** Layout compacto na faixa Forma; campos empilhados no inspetor. */
  variant?: "ribbon" | "inspector";
  idPrefix?: string;
  /**
   * Omite corner/round (raio) — já editável na seção Exibição.
   * Default true para evitar controle duplicado.
   */
  omitCornerRadius?: boolean;
};

/**
 * Controles contínuos dos ajustes de geometria (handles amarelos).
 * Raio/cantos ficam na seção Exibição (posição/tamanho) — omitidos aqui.
 */
export function ShapeAdjustmentsControl({
  kind,
  style,
  onChange,
  variant = "ribbon",
  idPrefix = "td-shape-adj",
  omitCornerRadius = true,
}: Props) {
  const specs = shapeAdjustmentSpecs(kind).filter(
    (spec) =>
      !(omitCornerRadius && (spec.id === "corner" || spec.id === "round")),
  );
  if (specs.length === 0) return null;

  const values = resolveShapeAdjustments(kind, style);

  const fields = specs.map((spec) => {
    const id = `${idPrefix}-${spec.id}`;
    const isCorner = spec.id === "corner" || spec.id === "round";
    const displayValue = isCorner
      ? (style?.borderRadius ?? cornerAdjustmentToBorderRadiusPx(values[spec.index], 64))
      : Math.round(values[spec.index] * 1000) / 1000;
    const min = isCorner ? 0 : spec.min;
    const max = isCorner ? 128 : spec.max;
    const step = isCorner ? 1 : 0.01;
    const label = isCorner
      ? variant === "inspector"
        ? "Cantos (px)"
        : "Raio (px)"
      : spec.label;

    return (
      <DeckRangeField
        key={spec.id}
        id={id}
        label={label}
        hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.shapeAdjustment}
        value={displayValue}
        min={min}
        max={max}
        step={step}
        aria-label={spec.label}
        onChange={(num) => {
          if (isCorner) {
            const adj = Math.max(0, Math.min(0.5, num / 64));
            onChange(patchShapeAdjustment(kind, style, spec.index, adj, 64));
            return;
          }
          onChange(patchShapeAdjustment(kind, style, spec.index, num));
        }}
      />
    );
  });

  if (variant === "inspector") {
    return <div className="td-deck-inspector__range-stack">{fields}</div>;
  }

  return (
    <DeckRibbonGroup label="Ajustes da forma" hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.shapeAdjustment}>
      {fields}
    </DeckRibbonGroup>
  );
}
