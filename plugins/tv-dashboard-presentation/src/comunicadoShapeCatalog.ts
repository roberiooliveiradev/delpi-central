import type { ComunicadoShapeKind } from "./comunicadoTypes";
import type { ComunicadoVisualPrimitive } from "./comunicadoVisualPrimitive";

export type ComunicadoShapeCatalogCategory = {
  id: string;
  label: string;
  shapes: ComunicadoShapeKind[];
  primitive?: ComunicadoVisualPrimitive;
};

export type ComunicadoShapeCatalogEntry = {
  kind: ComunicadoShapeKind;
  label: string;
  categoryId: string;
};

const SHAPE_LABELS: Record<ComunicadoShapeKind, string> = {
  point: "Ponto",
  rectangle: "Retângulo",
  "rounded-rect": "Retângulo arredondado",
  ellipse: "Elipse",
  triangle: "Triângulo",
  diamond: "Losango",
  pentagon: "Pentágono",
  hexagon: "Hexágono",
  heart: "Coração",
  "arrow-right": "Seta direita",
  "arrow-left": "Seta esquerda",
  "arrow-up": "Seta para cima",
  "arrow-down": "Seta para baixo",
  "chevron-right": "Chevron direita",
  "chevron-left": "Chevron esquerda",
  star: "Estrela 5 pontas",
  "star-4": "Estrela 4 pontas",
  line: "Linha",
  "line-arrow-right": "Linha com seta",
  "flowchart-process": "Processo",
  "flowchart-decision": "Decisão",
  "flowchart-terminator": "Início/Fim",
  "callout-rect": "Balão retangular",
};

export const COMUNICADO_SHAPE_CATALOG_CATEGORIES: ComunicadoShapeCatalogCategory[] = [
  {
    id: "points",
    label: "Pontos",
    primitive: "point",
    shapes: ["point"],
  },
  {
    id: "lines",
    label: "Linhas",
    primitive: "line",
    shapes: ["line", "line-arrow-right"],
  },
  {
    id: "rectangles",
    label: "Retângulos",
    primitive: "area",
    shapes: ["rectangle", "rounded-rect", "callout-rect"],
  },
  {
    id: "basic",
    label: "Formas básicas",
    primitive: "area",
    shapes: ["ellipse", "triangle", "diamond", "pentagon", "hexagon", "heart", "star", "star-4"],
  },
  {
    id: "arrows",
    label: "Setas",
    primitive: "area",
    shapes: [
      "arrow-right",
      "arrow-left",
      "arrow-up",
      "arrow-down",
      "chevron-right",
      "chevron-left",
    ],
  },
  {
    id: "flowchart",
    label: "Fluxograma",
    primitive: "area",
    shapes: ["flowchart-process", "flowchart-decision", "flowchart-terminator"],
  },
];

export const COMUNICADO_SHAPE_KINDS: Array<{ kind: ComunicadoShapeKind; label: string }> =
  COMUNICADO_SHAPE_CATALOG_CATEGORIES.flatMap((category) =>
    category.shapes.map((kind) => ({
      kind,
      label: SHAPE_LABELS[kind],
    })),
  );

export const COMUNICADO_SHAPE_CATALOG: ComunicadoShapeCatalogEntry[] =
  COMUNICADO_SHAPE_CATALOG_CATEGORIES.flatMap((category) =>
    category.shapes.map((kind) => ({
      kind,
      label: SHAPE_LABELS[kind],
      categoryId: category.id,
    })),
  );

export function comunicadoShapeLabel(kind: ComunicadoShapeKind): string {
  return SHAPE_LABELS[kind];
}

export const COMUNICADO_SHAPE_KIND_VALUES = Object.keys(SHAPE_LABELS) as ComunicadoShapeKind[];

export function isComunicadoShapeKind(value: string): value is ComunicadoShapeKind {
  return value in SHAPE_LABELS;
}
