import {
  cornerAdjustmentToBorderRadiusPx,
  patchShapeAdjustment,
  resolveShapeAdjustments,
  shapeAdjustmentSpecs,
  type ShapeAdjustmentSpec,
} from "./comunicadoShapeAdjustments";
import {
  getChartPartState,
  resolveChartAreaStyle,
  upsertChartPartState,
} from "./comunicadoChartParts";
import {
  getKpiPartState,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  upsertKpiPartState,
} from "./comunicadoKpiParts";
import { mergeComunicadoKpiOptions } from "./comunicadoKpiOptions";
import type { ComunicadoBlock } from "./comunicadoTypes";
import { isAreaShapeKind, resolveShapePrimitive } from "./comunicadoVisualPrimitive";

/**
 * Chrome de forma compartilhado (cantos / contorno) — formas area, KPI card, tabela e chartArea.
 * Handles amarelos e ribbon usam este módulo; não duplicar por tipo de bloco.
 */

const CHROME_CORNER_KIND = "rounded-rect" as const;

export function blockSupportsShapeChromeHandles(block: ComunicadoBlock): boolean {
  if (block.type === "shape") {
    return isAreaShapeKind(block.shape) || shapeAdjustmentSpecs(block.shape).length > 0;
  }
  return block.type === "kpi_view" || block.type === "table_view" || block.type === "chart_view";
}

/** Specs de ajuste para handles no palco (forma completa ou só cantos do chrome). */
export function blockShapeChromeAdjustmentSpecs(block: ComunicadoBlock): ShapeAdjustmentSpec[] {
  if (block.type === "shape") {
    return shapeAdjustmentSpecs(block.shape);
  }
  if (blockSupportsShapeChromeHandles(block)) {
    return shapeAdjustmentSpecs(CHROME_CORNER_KIND);
  }
  return [];
}

export function resolveBlockShapeChromeCornerPx(block: ComunicadoBlock): number {
  if (block.type === "shape") {
    const values = resolveShapeAdjustments(block.shape, block.style);
    if (typeof block.style?.borderRadius === "number") return block.style.borderRadius;
    const corner = values[0];
    return typeof corner === "number" ? Math.round(corner * 64) : 0;
  }
  if (block.type === "kpi_view") {
    const card = getKpiPartState(block.kpiParts, { kind: "card" });
    return card?.style?.borderRadius ?? block.style?.borderRadius ?? 0;
  }
  if (block.type === "table_view") {
    return block.style?.borderRadius ?? 0;
  }
  if (block.type === "chart_view") {
    const area = resolveChartAreaStyle(block.chartOptions ?? {}, block.chartParts);
    const part = getChartPartState(block.chartParts, { kind: "chartArea" });
    return part?.style?.borderRadius ?? area.borderRadius ?? 0;
  }
  return 0;
}

export function resolveBlockShapeChromeAdjustmentValues(block: ComunicadoBlock): number[] {
  if (block.type === "shape") {
    return resolveShapeAdjustments(block.shape, block.style);
  }
  const px = resolveBlockShapeChromeCornerPx(block);
  const specs = shapeAdjustmentSpecs(CHROME_CORNER_KIND);
  const adj = Math.min(0.5, Math.max(0, px / 64));
  return specs.map((spec, index) => (index === 0 ? adj : spec.defaultValue));
}

/**
 * Aplica ajuste de chrome (handle amarelo) → patch de bloco.
 * KPI atualiza `kpiParts.card`; chart atualiza `chartArea`; tabela/forma usam `style`.
 */
export function applyBlockShapeChromeAdjustment(
  block: ComunicadoBlock,
  adjIndex: number,
  value: number,
  shortSidePx: number,
): Partial<ComunicadoBlock> | null {
  const specs = blockShapeChromeAdjustmentSpecs(block);
  const spec = specs.find((item) => item.index === adjIndex) ?? specs[adjIndex];
  if (!spec) return null;

  if (block.type === "shape") {
    const stylePatch = patchShapeAdjustment(block.shape, block.style, spec.index, value, shortSidePx);
    return { style: { ...block.style, ...stylePatch } };
  }

  if (spec.id !== "corner" && spec.id !== "round") {
    return null;
  }

  const px = cornerAdjustmentToBorderRadiusPx(value, shortSidePx > 0 ? shortSidePx : 64);

  if (block.type === "kpi_view") {
    const nextParts = upsertKpiPartState(block.kpiParts, { kind: "card" }, {
      style: { borderRadius: px },
    });
    const fromParts = partsToKpiOptions(nextParts);
    const nextOptions = mergeComunicadoKpiOptions({
      ...block.kpiOptions,
      ...fromParts,
    });
    return {
      kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
      kpiOptions: nextOptions,
    };
  }

  if (block.type === "table_view") {
    return {
      style: {
        ...block.style,
        borderRadius: px,
      },
    };
  }

  if (block.type === "chart_view") {
    return {
      chartParts: upsertChartPartState(block.chartParts, { kind: "chartArea" }, {
        style: { borderRadius: px },
      }),
    };
  }

  return null;
}

/** Raio para alinhar outline de seleção do wrap ao chrome interno. */
export function resolveBlockSelectionBorderRadiusPx(block: ComunicadoBlock): number | undefined {
  if (!blockSupportsShapeChromeHandles(block)) return undefined;
  if (block.type === "shape" && resolveShapePrimitive(block.shape) !== "area") {
    return undefined;
  }
  return resolveBlockShapeChromeCornerPx(block);
}
