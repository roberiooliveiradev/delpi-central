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
  "snip-rect": "Retângulo recortado",
  "round-same-side-rect": "Retângulo cantos superiores",
  ellipse: "Elipse",
  triangle: "Triângulo",
  "right-triangle": "Triângulo retângulo",
  parallelogram: "Paralelogramo",
  trapezoid: "Trapézio",
  diamond: "Losango",
  pentagon: "Pentágono",
  hexagon: "Hexágono",
  octagon: "Octógono",
  cross: "Cruz",
  cylinder: "Cilindro",
  heart: "Coração",
  lightning: "Raio",
  cloud: "Nuvem",
  moon: "Lua",
  sun: "Sol",
  "arrow-right": "Seta direita",
  "arrow-left": "Seta esquerda",
  "arrow-up": "Seta para cima",
  "arrow-down": "Seta para baixo",
  "arrow-left-right": "Seta esquerda-direita",
  "arrow-up-down": "Seta cima-baixo",
  "chevron-right": "Chevron direita",
  "chevron-left": "Chevron esquerda",
  "notched-arrow-right": "Seta entalhada",
  star: "Estrela 5 pontas",
  "star-4": "Estrela 4 pontas",
  "star-6": "Estrela 6 pontas",
  "star-8": "Estrela 8 pontas",
  banner: "Faixa",
  wave: "Onda",
  line: "Linha",
  "line-arrow-right": "Linha com seta",
  "line-arrow-left": "Linha com seta esquerda",
  "line-arrow-both": "Linha com setas",
  "flowchart-process": "Processo",
  "flowchart-decision": "Decisão",
  "flowchart-terminator": "Início/Fim",
  "flowchart-data": "Dados",
  "flowchart-document": "Documento",
  "flowchart-preparation": "Preparação",
  "callout-rect": "Balão retangular",
  "callout-rounded": "Balão arredondado",
  "callout-cloud": "Balão nuvem",
  "equation-plus": "Mais",
  "equation-minus": "Menos",
  "equation-multiply": "Multiplicação",
  "equation-divide": "Divisão",
  "equation-equal": "Igual",
};

/** Categorias alinhadas à biblioteca de formas do Office Online. */
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
    shapes: ["line", "line-arrow-right", "line-arrow-left", "line-arrow-both"],
  },
  {
    id: "rectangles",
    label: "Retângulos",
    primitive: "area",
    shapes: ["rectangle", "rounded-rect", "snip-rect", "round-same-side-rect"],
  },
  {
    id: "basic",
    label: "Formas básicas",
    primitive: "area",
    shapes: [
      "ellipse",
      "triangle",
      "right-triangle",
      "parallelogram",
      "trapezoid",
      "diamond",
      "pentagon",
      "hexagon",
      "octagon",
      "cross",
      "cylinder",
      "heart",
      "lightning",
      "cloud",
      "moon",
      "sun",
    ],
  },
  {
    id: "arrows",
    label: "Setas largas",
    primitive: "area",
    shapes: [
      "arrow-right",
      "arrow-left",
      "arrow-up",
      "arrow-down",
      "arrow-left-right",
      "arrow-up-down",
      "chevron-right",
      "chevron-left",
      "notched-arrow-right",
    ],
  },
  {
    id: "equation",
    label: "Formas de equação",
    primitive: "area",
    shapes: [
      "equation-plus",
      "equation-minus",
      "equation-multiply",
      "equation-divide",
      "equation-equal",
    ],
  },
  {
    id: "flowchart",
    label: "Fluxograma",
    primitive: "area",
    shapes: [
      "flowchart-process",
      "flowchart-decision",
      "flowchart-terminator",
      "flowchart-data",
      "flowchart-document",
      "flowchart-preparation",
    ],
  },
  {
    id: "stars",
    label: "Estrelas e faixas",
    primitive: "area",
    shapes: ["star-4", "star", "star-6", "star-8", "banner", "wave"],
  },
  {
    id: "callouts",
    label: "Balões",
    primitive: "area",
    shapes: ["callout-rect", "callout-rounded", "callout-cloud"],
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
