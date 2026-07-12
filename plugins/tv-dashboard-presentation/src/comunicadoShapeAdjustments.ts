import type { ComunicadoBlockStyle, ComunicadoShapeKind } from "./comunicadoTypes";

/**
 * Ajustes de geometria no modelo PowerPoint (Adjustments 0..1 tipicamente).
 * Cada handle amarelo no canvas corresponde a um índice em `style.adjustments`.
 */
export type ShapeAdjustmentAxis = "x" | "y" | "xy";

export type ShapeAdjustmentSpec = {
  index: number;
  id: string;
  label: string;
  defaultValue: number;
  min: number;
  max: number;
  axis: ShapeAdjustmentAxis;
  /** Posição do handle no quadro de seleção (0–100 %). */
  handleAt: (values: number[]) => { x: number; y: number };
  /** Converte ponteiro local (0–100 % no quadro) → valor do ajuste. */
  valueFromPointer: (localX: number, localY: number, values: number[]) => number;
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function linearFromX(localX: number, min: number, max: number): number {
  return clamp(min + (localX / 100) * (max - min), min, max);
}

function linearFromY(localY: number, min: number, max: number): number {
  return clamp(min + (localY / 100) * (max - min), min, max);
}

/** Cantos arredondados (retângulo / processo) — equivalente ao adj do Rounded Rectangle.
 * handleAt e valueFromPointer são inversos.
 * Início em ~12% no topo (não no canto NW) para não cobrir o handle azul de resize.
 */
function cornerSpec(index = 0): ShapeAdjustmentSpec {
  const trackStart = 12;
  const trackEnd = 50;
  const track = trackEnd - trackStart;
  return {
    index,
    id: "corner",
    label: "Cantos",
    defaultValue: 0.16,
    min: 0,
    max: 0.5,
    axis: "x",
    handleAt: (values) => ({
      x: clamp(trackStart + ((values[index] ?? 0.16) / 0.5) * track, trackStart, trackEnd),
      y: 0,
    }),
    valueFromPointer: (localX) =>
      clamp(((localX - trackStart) / track) * 0.5, 0, 0.5),
  };
}

function slantSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "slant",
    label: "Inclinação",
    defaultValue: 0.2,
    min: 0.05,
    max: 0.45,
    axis: "x",
    handleAt: (values) => ({ x: (values[index] ?? 0.2) * 100, y: 8 }),
    valueFromPointer: (localX) => linearFromX(localX, 0.05, 0.45),
  };
}

function topInsetSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "topInset",
    label: "Topo",
    defaultValue: 0.22,
    min: 0.05,
    max: 0.4,
    axis: "x",
    handleAt: (values) => ({ x: (values[index] ?? 0.22) * 100, y: 8 }),
    valueFromPointer: (localX) => linearFromX(localX, 0.05, 0.4),
  };
}

function tipXSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "tip",
    label: "Ponta",
    defaultValue: 0.5,
    min: 0.15,
    max: 0.85,
    axis: "x",
    handleAt: (values) => ({ x: (values[index] ?? 0.5) * 100, y: 4 }),
    valueFromPointer: (localX) => linearFromX(localX, 0.15, 0.85),
  };
}

function sideInsetSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "sideInset",
    label: "Faces",
    defaultValue: 0.2,
    min: 0.05,
    max: 0.4,
    axis: "x",
    handleAt: (values) => ({ x: 100 - (values[index] ?? 0.2) * 100, y: 50 }),
    valueFromPointer: (localX) => clamp(1 - localX / 100, 0.05, 0.4),
  };
}

function cutSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "cut",
    label: "Corte",
    defaultValue: 0.25,
    min: 0.08,
    max: 0.4,
    axis: "x",
    handleAt: (values) => ({ x: (values[index] ?? 0.25) * 100, y: 4 }),
    valueFromPointer: (localX) => linearFromX(localX, 0.08, 0.4),
  };
}

function armSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "arm",
    label: "Braços",
    defaultValue: 0.28,
    min: 0.12,
    max: 0.42,
    axis: "x",
    handleAt: (values) => ({ x: 50 + (values[index] ?? 0.28) * 50, y: 8 }),
    valueFromPointer: (localX) => clamp((localX - 50) / 50, 0.12, 0.42),
  };
}

function cylinderSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "cap",
    label: "Tampa",
    defaultValue: 0.18,
    min: 0.08,
    max: 0.35,
    axis: "y",
    handleAt: (values) => ({ x: 50, y: (values[index] ?? 0.18) * 100 }),
    valueFromPointer: (_x, localY) => linearFromY(localY, 0.08, 0.35),
  };
}

function arrowHeadSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "head",
    label: "Ponta da seta",
    defaultValue: 0.35,
    min: 0.15,
    max: 0.55,
    axis: "x",
    handleAt: (values) => ({ x: 100 - (values[index] ?? 0.35) * 100, y: 20 }),
    valueFromPointer: (localX) => clamp(1 - localX / 100, 0.15, 0.55),
  };
}

function arrowShaftSpec(index = 1): ShapeAdjustmentSpec {
  return {
    index,
    id: "shaft",
    label: "Espessura",
    defaultValue: 0.28,
    min: 0.12,
    max: 0.45,
    axis: "y",
    handleAt: (values) => ({ x: 40, y: 50 - (values[index] ?? 0.28) * 50 }),
    valueFromPointer: (_x, localY) => clamp(Math.abs(50 - localY) / 50, 0.12, 0.45),
  };
}

function chevronSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "depth",
    label: "Profundidade",
    defaultValue: 0.45,
    min: 0.2,
    max: 0.7,
    axis: "x",
    handleAt: (values) => ({ x: (values[index] ?? 0.45) * 100, y: 50 }),
    valueFromPointer: (localX) => linearFromX(localX, 0.2, 0.7),
  };
}

function starInnerSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "inner",
    label: "Raio interno",
    defaultValue: 0.4,
    min: 0.15,
    max: 0.7,
    axis: "xy",
    handleAt: (values) => {
      const inner = values[index] ?? 0.4;
      return { x: 50, y: 50 - inner * 40 };
    },
    valueFromPointer: (localX, localY) => {
      const dx = localX - 50;
      const dy = localY - 50;
      return clamp(Math.hypot(dx, dy) / 40, 0.15, 0.7);
    },
  };
}

function bannerSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "fold",
    label: "Dobra",
    defaultValue: 0.18,
    min: 0.06,
    max: 0.35,
    axis: "x",
    handleAt: (values) => ({ x: 100 - (values[index] ?? 0.18) * 100, y: 28 }),
    valueFromPointer: (localX) => clamp(1 - localX / 100, 0.06, 0.35),
  };
}

function waveSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "wave",
    label: "Onda",
    defaultValue: 0.22,
    min: 0.08,
    max: 0.4,
    axis: "y",
    handleAt: (values) => ({ x: 28, y: 40 - (values[index] ?? 0.22) * 40 }),
    valueFromPointer: (_x, localY) => clamp(Math.abs(40 - localY) / 40, 0.08, 0.4),
  };
}

function snipSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "snip",
    label: "Corte",
    defaultValue: 0.2,
    min: 0.05,
    max: 0.45,
    axis: "x",
    handleAt: (values) => ({ x: 100 - (values[index] ?? 0.2) * 40, y: 8 }),
    valueFromPointer: (localX) => clamp((100 - localX) / 40, 0.05, 0.45),
  };
}

function roundSameSideSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "round",
    label: "Arredondamento",
    defaultValue: 0.18,
    min: 0.05,
    max: 0.4,
    axis: "x",
    handleAt: (values) => ({ x: (values[index] ?? 0.18) * 100, y: 8 }),
    valueFromPointer: (localX) => linearFromX(localX, 0.05, 0.4),
  };
}

function documentWaveSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "curve",
    label: "Curva",
    defaultValue: 0.2,
    min: 0.05,
    max: 0.4,
    axis: "y",
    handleAt: (values) => ({ x: 50, y: 70 + (values[index] ?? 0.2) * 30 }),
    valueFromPointer: (_x, localY) => clamp((localY - 70) / 30, 0.05, 0.4),
  };
}

function calloutPointerX(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "pointerX",
    label: "Ponteiro X",
    defaultValue: 0.5,
    min: 0.15,
    max: 0.85,
    axis: "x",
    handleAt: (values) => ({ x: (values[index] ?? 0.5) * 100, y: 88 }),
    valueFromPointer: (localX) => linearFromX(localX, 0.15, 0.85),
  };
}

function calloutPointerY(index = 1): ShapeAdjustmentSpec {
  return {
    index,
    id: "pointerY",
    label: "Ponteiro Y",
    defaultValue: 0.9,
    min: 0.7,
    max: 1.05,
    axis: "y",
    handleAt: (values) => ({ x: 50, y: Math.min(100, (values[index] ?? 0.9) * 100) }),
    valueFromPointer: (_x, localY) => linearFromY(localY, 0.7, 1.05),
  };
}

function moonSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "crescent",
    label: "Crescente",
    defaultValue: 0.45,
    min: 0.2,
    max: 0.7,
    axis: "x",
    handleAt: (values) => ({ x: 30 + (values[index] ?? 0.45) * 40, y: 50 }),
    valueFromPointer: (localX) => clamp((localX - 30) / 40, 0.2, 0.7),
  };
}

function sunCoreSpec(index = 0): ShapeAdjustmentSpec {
  return {
    index,
    id: "core",
    label: "Núcleo",
    defaultValue: 0.35,
    min: 0.2,
    max: 0.55,
    axis: "xy",
    handleAt: (values) => ({ x: 50 + (values[index] ?? 0.35) * 30, y: 50 }),
    valueFromPointer: (localX, localY) => clamp(Math.hypot(localX - 50, localY - 50) / 30, 0.2, 0.55),
  };
}

const SPECS_BY_KIND: Partial<Record<ComunicadoShapeKind, ShapeAdjustmentSpec[]>> = {
  rectangle: [cornerSpec(0)],
  "rounded-rect": [cornerSpec(0)],
  "flowchart-process": [{ ...cornerSpec(0), defaultValue: 0.05 }],
  "snip-rect": [snipSpec(0)],
  "round-same-side-rect": [roundSameSideSpec(0)],
  triangle: [tipXSpec(0)],
  parallelogram: [slantSpec(0)],
  "flowchart-data": [slantSpec(0)],
  trapezoid: [topInsetSpec(0)],
  "flowchart-preparation": [topInsetSpec(0)],
  pentagon: [tipXSpec(0)],
  hexagon: [sideInsetSpec(0)],
  octagon: [cutSpec(0)],
  cross: [armSpec(0)],
  cylinder: [cylinderSpec(0)],
  "arrow-right": [arrowHeadSpec(0), arrowShaftSpec(1)],
  "arrow-left": [arrowHeadSpec(0), arrowShaftSpec(1)],
  "arrow-up": [
    {
      ...arrowHeadSpec(0),
      axis: "y",
      handleAt: (values) => ({ x: 20, y: (values[0] ?? 0.35) * 100 }),
      valueFromPointer: (_x, localY) => linearFromY(localY, 0.15, 0.55),
    },
    {
      ...arrowShaftSpec(1),
      axis: "x",
      handleAt: (values) => ({ x: 50 - (values[1] ?? 0.28) * 50, y: 60 }),
      valueFromPointer: (localX) => clamp(Math.abs(50 - localX) / 50, 0.12, 0.45),
    },
  ],
  "arrow-down": [
    {
      ...arrowHeadSpec(0),
      axis: "y",
      handleAt: (values) => ({ x: 20, y: 100 - (values[0] ?? 0.35) * 100 }),
      valueFromPointer: (_x, localY) => clamp(1 - localY / 100, 0.15, 0.55),
    },
    {
      ...arrowShaftSpec(1),
      axis: "x",
      handleAt: (values) => ({ x: 50 - (values[1] ?? 0.28) * 50, y: 40 }),
      valueFromPointer: (localX) => clamp(Math.abs(50 - localX) / 50, 0.12, 0.45),
    },
  ],
  "arrow-left-right": [arrowHeadSpec(0), arrowShaftSpec(1)],
  "arrow-up-down": [
    {
      ...arrowHeadSpec(0),
      axis: "y",
      handleAt: (values) => ({ x: 20, y: (values[0] ?? 0.35) * 100 }),
      valueFromPointer: (_x, localY) => linearFromY(localY, 0.15, 0.55),
    },
    {
      ...arrowShaftSpec(1),
      axis: "x",
      handleAt: (values) => ({ x: 50 - (values[1] ?? 0.28) * 50, y: 50 }),
      valueFromPointer: (localX) => clamp(Math.abs(50 - localX) / 50, 0.12, 0.45),
    },
  ],
  "chevron-right": [chevronSpec(0)],
  "chevron-left": [
    {
      ...chevronSpec(0),
      handleAt: (values) => ({ x: 100 - (values[0] ?? 0.45) * 100, y: 50 }),
      valueFromPointer: (localX) => clamp(1 - localX / 100, 0.2, 0.7),
    },
  ],
  "notched-arrow-right": [arrowHeadSpec(0), arrowShaftSpec(1)],
  star: [starInnerSpec(0)],
  "star-4": [starInnerSpec(0)],
  "star-6": [starInnerSpec(0)],
  "star-8": [starInnerSpec(0)],
  banner: [bannerSpec(0)],
  wave: [waveSpec(0)],
  "flowchart-document": [documentWaveSpec(0)],
  "callout-rect": [calloutPointerX(0), calloutPointerY(1)],
  "callout-rounded": [calloutPointerX(0), calloutPointerY(1), { ...cornerSpec(2), defaultValue: 0.2 }],
  "callout-cloud": [calloutPointerX(0), calloutPointerY(1)],
  moon: [moonSpec(0)],
  sun: [sunCoreSpec(0)],
};

export function shapeAdjustmentSpecs(kind: ComunicadoShapeKind): ShapeAdjustmentSpec[] {
  return SPECS_BY_KIND[kind] ?? [];
}

export function shapeHasAdjustments(kind: ComunicadoShapeKind): boolean {
  return shapeAdjustmentSpecs(kind).length > 0;
}

export function defaultShapeAdjustments(kind: ComunicadoShapeKind): number[] {
  return shapeAdjustmentSpecs(kind).map((spec) => spec.defaultValue);
}

/**
 * Resolve valores efetivos (defaults + legado `borderRadius` em px → adj de cantos).
 */
export function resolveShapeAdjustments(
  kind: ComunicadoShapeKind,
  style?: ComunicadoBlockStyle | null,
): number[] {
  const specs = shapeAdjustmentSpecs(kind);
  if (specs.length === 0) return [];

  const stored = style?.adjustments;
  const values = specs.map((spec, index) => {
    const raw = stored?.[index];
    if (typeof raw === "number" && Number.isFinite(raw)) {
      return clamp(raw, spec.min, spec.max);
    }
    return spec.defaultValue;
  });

  const cornerIndex = specs.findIndex((spec) => spec.id === "corner" || spec.id === "round");
  if (
    cornerIndex >= 0 &&
    (stored == null || stored[cornerIndex] == null) &&
    typeof style?.borderRadius === "number" &&
    style.borderRadius > 0 &&
    style.borderRadius < 999
  ) {
    values[cornerIndex] = clamp(style.borderRadius / 64, specs[cornerIndex].min, specs[cornerIndex].max);
  }

  return values;
}

/** Converte adj de canto (0–0.5) → raio em px (lado curto estimado). */
export function cornerAdjustmentToBorderRadiusPx(
  adj: number,
  shortSidePx: number,
): number {
  return Math.round(clamp(adj, 0, 0.5) * Math.max(0, shortSidePx));
}

export function borderRadiusPxToCornerAdjustment(px: number, shortSidePx: number): number {
  if (shortSidePx <= 0) return clamp(px / 64, 0, 0.5);
  return clamp(px / shortSidePx, 0, 0.5);
}

export function patchShapeAdjustment(
  kind: ComunicadoShapeKind,
  style: ComunicadoBlockStyle | undefined,
  index: number,
  value: number,
  shortSidePx?: number,
): Partial<ComunicadoBlockStyle> {
  const specs = shapeAdjustmentSpecs(kind);
  const spec = specs.find((item) => item.index === index) ?? specs[index];
  if (!spec) return {};

  const nextValues = resolveShapeAdjustments(kind, style);
  nextValues[spec.index] = clamp(value, spec.min, spec.max);

  const patch: Partial<ComunicadoBlockStyle> = { adjustments: nextValues };
  if ((spec.id === "corner" || spec.id === "round") && shortSidePx != null && shortSidePx > 0) {
    patch.borderRadius = cornerAdjustmentToBorderRadiusPx(nextValues[spec.index], shortSidePx);
  } else if (spec.id === "corner" || spec.id === "round") {
    patch.borderRadius = Math.round(nextValues[spec.index] * 64);
  }
  return patch;
}

export function adjustmentHandleCssPosition(spec: ShapeAdjustmentSpec, values: number[]): {
  left: string;
  top: string;
} {
  const pos = spec.handleAt(values);
  return {
    left: `${clamp(pos.x, 0, 100)}%`,
    top: `${clamp(pos.y, 0, 100)}%`,
  };
}
