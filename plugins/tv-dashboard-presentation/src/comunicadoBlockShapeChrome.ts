import {
  borderRadiusPxToCornerAdjustment,
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
  getInputPartState,
  resolveInputShapeChromePartRef,
  upsertInputPartState,
  type ComunicadoInputPartRef,
} from "./comunicadoInputParts";
import {
  getKpiPartState,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  upsertKpiPartState,
} from "./comunicadoKpiParts";
import { mergeComunicadoKpiOptions } from "./comunicadoKpiOptions";
import {
  getTablePartState,
  mergeTablePartsWithOptions,
  upsertTablePartState,
} from "./comunicadoTableParts";
import type { ComunicadoBlock } from "./comunicadoTypes";
import { isAreaShapeKind, resolveShapePrimitive } from "./comunicadoVisualPrimitive";

/**
 * Chrome de forma compartilhado (cantos / contorno) — formas area, KPI card, tabela, chartArea e filtro.
 * Handles amarelos e ribbon usam este módulo; não duplicar por tipo de bloco.
 */

const CHROME_CORNER_KIND = "rounded-rect" as const;

export function blockSupportsShapeChromeHandles(block: ComunicadoBlock): boolean {
  if (block.type === "shape") {
    return isAreaShapeKind(block.shape) || shapeAdjustmentSpecs(block.shape).length > 0;
  }
  return (
    block.type === "kpi_view" ||
    block.type === "table_view" ||
    block.type === "chart_view" ||
    block.type === "input"
  );
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
    const frame = getTablePartState(block.tableParts, { kind: "frame" });
    return frame?.style?.borderRadius ?? block.style?.borderRadius ?? 0;
  }
  if (block.type === "chart_view") {
    const area = resolveChartAreaStyle(block.chartOptions ?? {}, block.chartParts);
    const part = getChartPartState(block.chartParts, { kind: "chartArea" });
    return part?.style?.borderRadius ?? area.borderRadius ?? 0;
  }
  if (block.type === "input") {
    const frame = getInputPartState(block.inputParts, { kind: "frame" });
    return frame?.style?.borderRadius ?? block.style?.borderRadius ?? 0;
  }
  return 0;
}

export function resolveBlockShapeChromeAdjustmentValues(
  block: ComunicadoBlock,
  shortSidePx = 64,
): number[] {
  if (block.type === "shape") {
    return resolveShapeAdjustments(block.shape, block.style);
  }
  const px = resolveBlockShapeChromeCornerPx(block);
  const specs = shapeAdjustmentSpecs(CHROME_CORNER_KIND);
  const adj = borderRadiusPxToCornerAdjustment(px, shortSidePx > 0 ? shortSidePx : 64);
  return specs.map((spec, index) => (index === 0 ? adj : spec.defaultValue));
}

/**
 * Aplica ajuste de chrome (handle amarelo) → patch de bloco.
 * KPI atualiza `kpiParts.card`; chart atualiza `chartArea`; tabela atualiza `tableParts.frame`.
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
    const nextParts = upsertTablePartState(block.tableParts, { kind: "frame" }, {
      style: { borderRadius: px },
    });
    return {
      tableParts: mergeTablePartsWithOptions(nextParts, block.tableOptions),
      style: { ...block.style, borderRadius: px },
    };
  }

  if (block.type === "chart_view") {
    return {
      chartParts: upsertChartPartState(block.chartParts, { kind: "chartArea" }, {
        style: { borderRadius: px },
      }),
    };
  }

  if (block.type === "input") {
    return {
      inputParts: upsertInputPartState(block.inputParts, { kind: "frame" }, {
        style: { borderRadius: px },
      }),
      style: { ...block.style, borderRadius: px },
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

/** Tipos cuja moldura visual (fill/stroke/radius) vive em parts, não no wrapper. */
export function blockUsesInnerShapeChrome(block: ComunicadoBlock): boolean {
  return (
    block.type === "kpi_view" ||
    block.type === "table_view" ||
    block.type === "chart_view" ||
    block.type === "input"
  );
}

export type BlockShapeChromeStyle = {
  borderRadius: number;
  strokeWidth: number;
  stroke: string;
  fill?: string;
};

/** Contorno/raio efetivos da moldura (KPI card / table frame / chartArea). */
export function resolveBlockShapeChromeStyle(block: ComunicadoBlock): BlockShapeChromeStyle | null {
  if (block.type === "kpi_view") {
    const card = getKpiPartState(block.kpiParts, { kind: "card" });
    return {
      borderRadius: card?.style?.borderRadius ?? block.style?.borderRadius ?? 0,
      strokeWidth: card?.style?.strokeWidth ?? block.style?.borderWidth ?? block.style?.strokeWidth ?? 0,
      stroke: card?.style?.stroke ?? block.style?.borderColor ?? block.style?.stroke ?? "transparent",
      fill: card?.style?.fill ?? block.kpiOptions?.backgroundColor ?? block.style?.backgroundColor,
    };
  }
  if (block.type === "table_view") {
    const frame = getTablePartState(block.tableParts, { kind: "frame" });
    const area = {
      borderRadius: frame?.style?.borderRadius ?? block.style?.borderRadius ?? 0,
      strokeWidth: frame?.style?.strokeWidth ?? block.style?.borderWidth ?? 1,
      stroke: frame?.style?.stroke ?? block.style?.borderColor ?? "#b4b4b4",
      fill: frame?.style?.fill ?? block.style?.backgroundColor,
    };
    return area;
  }
  if (block.type === "chart_view") {
    const area = resolveChartAreaStyle(block.chartOptions ?? {}, block.chartParts);
    const part = getChartPartState(block.chartParts, { kind: "chartArea" });
    return {
      borderRadius: part?.style?.borderRadius ?? area.borderRadius ?? 0,
      strokeWidth: part?.style?.strokeWidth ?? area.strokeWidth ?? 0,
      stroke: part?.style?.stroke ?? area.stroke,
      fill: part?.style?.fill ?? area.fill,
    };
  }
  if (block.type === "input") {
    const frame = getInputPartState(block.inputParts, { kind: "frame" });
    return {
      borderRadius: frame?.style?.borderRadius ?? block.style?.borderRadius ?? 0,
      strokeWidth:
        frame?.style?.strokeWidth ?? block.style?.borderWidth ?? block.style?.strokeWidth ?? 0,
      stroke: frame?.style?.stroke ?? block.style?.borderColor ?? block.style?.stroke ?? "transparent",
      fill: frame?.style?.fill ?? block.style?.backgroundColor,
    };
  }
  return null;
}

export type BlockShapeChromeStylePatch = {
  borderRadius?: number;
  /** Espessura — aceita nome da ribbon Organizar (`borderWidth`) ou stroke. */
  borderWidth?: number;
  strokeWidth?: number;
  borderColor?: string;
  stroke?: string;
  fill?: string;
  backgroundColor?: string;
};

export type ApplyBlockShapeChromeStyleOptions = {
  /** Filtro: parte ativa da ribbon/inspetor (default: moldura). */
  selectedInputPart?: ComunicadoInputPartRef | null;
};

/**
 * Aplica fill/stroke/radius na moldura interna (parts).
 * Usado pela ribbon Organizar e por `updateSelectedStyle` para não gravar só em `block.style`
 * (que `stripOuterChromeStyle` descarta no KPI/chart/tabela).
 */
export function applyBlockShapeChromeStyle(
  block: ComunicadoBlock,
  patch: BlockShapeChromeStylePatch,
  options?: ApplyBlockShapeChromeStyleOptions,
): Partial<ComunicadoBlock> | null {
  if (!blockUsesInnerShapeChrome(block)) return null;

  const strokeWidth =
    patch.strokeWidth ?? patch.borderWidth;
  const stroke = patch.stroke ?? patch.borderColor;
  const fill = patch.fill ?? patch.backgroundColor;
  const partStyle: {
    borderRadius?: number;
    strokeWidth?: number;
    stroke?: string;
    fill?: string;
  } = {};
  if (typeof patch.borderRadius === "number") {
    partStyle.borderRadius = Math.max(0, patch.borderRadius);
  }
  if (typeof strokeWidth === "number") {
    partStyle.strokeWidth = Math.max(0, strokeWidth);
  }
  if (typeof stroke === "string") {
    partStyle.stroke = stroke;
  }
  if (typeof fill === "string") {
    partStyle.fill = fill;
  }
  if (Object.keys(partStyle).length === 0) return null;

  if (block.type === "kpi_view") {
    const nextParts = upsertKpiPartState(block.kpiParts, { kind: "card" }, { style: partStyle });
    const fromParts = partsToKpiOptions(nextParts);
    const nextOptions = mergeComunicadoKpiOptions({
      ...block.kpiOptions,
      ...fromParts,
      ...(typeof fill === "string" ? { backgroundColor: fill } : {}),
    });
    return {
      kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
      kpiOptions: nextOptions,
      style: {
        ...block.style,
        ...(typeof partStyle.borderRadius === "number" ? { borderRadius: partStyle.borderRadius } : {}),
        ...(typeof partStyle.strokeWidth === "number"
          ? { borderWidth: partStyle.strokeWidth, strokeWidth: partStyle.strokeWidth }
          : {}),
        ...(typeof stroke === "string" ? { borderColor: stroke, stroke } : {}),
        ...(typeof fill === "string" ? { backgroundColor: fill, fill } : {}),
      },
    };
  }

  if (block.type === "table_view") {
    const nextParts = upsertTablePartState(block.tableParts, { kind: "frame" }, { style: partStyle });
    return {
      tableParts: mergeTablePartsWithOptions(nextParts, block.tableOptions),
      style: {
        ...block.style,
        ...(typeof partStyle.borderRadius === "number" ? { borderRadius: partStyle.borderRadius } : {}),
        ...(typeof partStyle.strokeWidth === "number"
          ? { borderWidth: partStyle.strokeWidth, strokeWidth: partStyle.strokeWidth }
          : {}),
        ...(typeof stroke === "string" ? { borderColor: stroke, stroke } : {}),
        ...(typeof fill === "string" ? { backgroundColor: fill, fill } : {}),
      },
    };
  }

  if (block.type === "chart_view") {
    return {
      chartParts: upsertChartPartState(block.chartParts, { kind: "chartArea" }, { style: partStyle }),
      style: {
        ...block.style,
        ...(typeof partStyle.borderRadius === "number" ? { borderRadius: partStyle.borderRadius } : {}),
        ...(typeof partStyle.strokeWidth === "number"
          ? { borderWidth: partStyle.strokeWidth, strokeWidth: partStyle.strokeWidth }
          : {}),
        ...(typeof stroke === "string" ? { borderColor: stroke, stroke } : {}),
        ...(typeof fill === "string" ? { backgroundColor: fill, fill } : {}),
      },
    };
  }

  if (block.type === "input") {
    const chromePart = resolveInputShapeChromePartRef(options?.selectedInputPart);
    const nextParts = upsertInputPartState(block.inputParts, chromePart, { style: partStyle });
    const mirrorOnBlockStyle = chromePart.kind === "frame";
    return {
      inputParts: nextParts,
      style: {
        ...block.style,
        ...(mirrorOnBlockStyle && typeof partStyle.borderRadius === "number"
          ? { borderRadius: partStyle.borderRadius }
          : {}),
        ...(mirrorOnBlockStyle && typeof partStyle.strokeWidth === "number"
          ? { borderWidth: partStyle.strokeWidth, strokeWidth: partStyle.strokeWidth }
          : {}),
        ...(mirrorOnBlockStyle && typeof stroke === "string"
          ? { borderColor: stroke, stroke }
          : {}),
        ...(mirrorOnBlockStyle && typeof fill === "string"
          ? { backgroundColor: fill, fill }
          : {}),
      },
    };
  }

  return null;
}

/** Chaves de estilo que, em KPI/chart/tabela, pertencem à moldura interna. */
export function isInnerShapeChromeStyleKey(key: string): boolean {
  return (
    key === "borderRadius" ||
    key === "borderWidth" ||
    key === "borderColor" ||
    key === "strokeWidth" ||
    key === "stroke" ||
    key === "fill" ||
    key === "backgroundColor"
  );
}

