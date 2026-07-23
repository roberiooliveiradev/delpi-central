import type { ComunicadoShapeKind } from "./comunicadoTypes";
import type { ComunicadoVisualPrimitive } from "./comunicadoVisualPrimitive";

export type ComunicadoShapeCatalogCategory = {
  id: string;
  label: string;
  shapes: ComunicadoShapeKind[];
  primitive?: ComunicadoVisualPrimitive;
  /**
   * Quando true, a categoria aparece no flyout Inserir → Formas (estilo Google Slides).
   * Linhas ficam no menu Linha separado.
   */
  libraryFlyout?: boolean;
};

export type ComunicadoShapeCatalogEntry = {
  kind: ComunicadoShapeKind;
  label: string;
  categoryId: string;
};

/** Ferramentas do menu Inserir → Linha (Google Slides). */
export type ComunicadoLineToolId =
  | "line"
  | "line-arrow"
  | "elbow-connector"
  | "curved-connector"
  | "curve"
  | "polyline"
  | "scribble";

export type ComunicadoLineToolDefinition = {
  id: ComunicadoLineToolId;
  label: string;
  /** Kind inserido imediatamente (sem desenho no palco). Ausente = ferramenta de desenho. */
  insertKind?: ComunicadoShapeKind;
  /**
   * false = item visível mas ainda não implementado (Fases 2/3).
   * true = disponível para uso.
   */
  ready: boolean;
};

const SHAPE_LABELS: Record<ComunicadoShapeKind, string> = {
  point: "Ponto",
  rectangle: "Retângulo",
  "rounded-rect": "Retângulo arredondado",
  "snip-rect": "Retângulo recortado",
  "snip-diag-rect": "Retângulo recorte diagonal",
  "round-same-side-rect": "Retângulo cantos superiores",
  "round-1-rect": "Retângulo 1 canto",
  ellipse: "Elipse",
  triangle: "Triângulo",
  "right-triangle": "Triângulo retângulo",
  parallelogram: "Paralelogramo",
  trapezoid: "Trapézio",
  diamond: "Losango",
  pentagon: "Pentágono",
  hexagon: "Hexágono",
  heptagon: "Heptágono",
  octagon: "Octógono",
  decagon: "Decágono",
  dodecagon: "Dodecágono",
  cross: "Cruz",
  cylinder: "Cilindro",
  cube: "Cubo",
  donut: "Donut",
  pie: "Pizza",
  teardrop: "Lágrima",
  frame: "Moldura",
  corner: "Canto L",
  "folded-corner": "Canto dobrado",
  smiley: "Carinha",
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
  "bent-arrow": "Seta dobrada",
  "u-turn-arrow": "Seta retorno",
  "quad-arrow": "Seta quádrupla",
  "curved-right-arrow": "Seta curva",
  "striped-right-arrow": "Seta listrada",
  star: "Estrela 5 pontas",
  "star-4": "Estrela 4 pontas",
  "star-6": "Estrela 6 pontas",
  "star-7": "Estrela 7 pontas",
  "star-8": "Estrela 8 pontas",
  "star-10": "Estrela 10 pontas",
  "star-12": "Estrela 12 pontas",
  "star-16": "Estrela 16 pontas",
  "star-24": "Estrela 24 pontas",
  "burst-16": "Explosão",
  banner: "Faixa",
  scroll: "Pergaminho",
  wave: "Onda",
  line: "Linha",
  "line-arrow-right": "Linha com seta",
  "line-arrow-left": "Linha com seta esquerda",
  "line-arrow-both": "Linha com setas",
  polyline: "Polilinha",
  curve: "Curva",
  scribble: "Rabisco",
  "flowchart-process": "Processo",
  "flowchart-decision": "Decisão",
  "flowchart-terminator": "Início/Fim",
  "flowchart-data": "Dados",
  "flowchart-document": "Documento",
  "flowchart-preparation": "Preparação",
  "callout-rect": "Balão retangular",
  "callout-rounded": "Balão arredondado",
  "callout-cloud": "Balão nuvem",
  "callout-oval": "Balão oval",
  "callout-line": "Balão com linha",
  "equation-plus": "Mais",
  "equation-minus": "Menos",
  "equation-multiply": "Multiplicação",
  "equation-divide": "Divisão",
  "equation-equal": "Igual",
};

/**
 * Categorias alinhadas ao Google Slides (PT): Formas / Setas / Descrições / Equação.
 * Linhas e ponto ficam no catálogo completo, mas só as com `libraryFlyout` entram no flyout.
 */
export const COMUNICADO_SHAPE_CATALOG_CATEGORIES: ComunicadoShapeCatalogCategory[] = [
  {
    id: "formas",
    label: "Formas",
    primitive: "area",
    libraryFlyout: true,
    shapes: [
      "point",
      "rectangle",
      "rounded-rect",
      "round-1-rect",
      "snip-rect",
      "snip-diag-rect",
      "round-same-side-rect",
      "ellipse",
      "triangle",
      "right-triangle",
      "parallelogram",
      "trapezoid",
      "diamond",
      "pentagon",
      "hexagon",
      "heptagon",
      "octagon",
      "decagon",
      "dodecagon",
      "cross",
      "cylinder",
      "cube",
      "donut",
      "pie",
      "teardrop",
      "frame",
      "corner",
      "folded-corner",
      "smiley",
      "heart",
      "lightning",
      "cloud",
      "moon",
      "sun",
      "flowchart-process",
      "flowchart-decision",
      "flowchart-terminator",
      "flowchart-data",
      "flowchart-document",
      "flowchart-preparation",
    ],
  },
  {
    id: "setas",
    label: "Setas",
    primitive: "area",
    libraryFlyout: true,
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
      "bent-arrow",
      "u-turn-arrow",
      "quad-arrow",
      "curved-right-arrow",
      "striped-right-arrow",
    ],
  },
  {
    id: "descricoes",
    label: "Descrições",
    primitive: "area",
    libraryFlyout: true,
    shapes: [
      "star-4",
      "star",
      "star-6",
      "star-7",
      "star-8",
      "star-10",
      "star-12",
      "star-16",
      "star-24",
      "burst-16",
      "banner",
      "scroll",
      "wave",
      "callout-rect",
      "callout-rounded",
      "callout-oval",
      "callout-cloud",
      "callout-line",
    ],
  },
  {
    id: "equacao",
    label: "Equação",
    primitive: "area",
    libraryFlyout: true,
    shapes: [
      "equation-plus",
      "equation-minus",
      "equation-multiply",
      "equation-divide",
      "equation-equal",
    ],
  },
  {
    id: "linhas",
    label: "Linhas",
    primitive: "line",
    libraryFlyout: false,
    shapes: [
      "line",
      "line-arrow-right",
      "line-arrow-left",
      "line-arrow-both",
      "polyline",
      "curve",
      "scribble",
    ],
  },
];

/** Categorias do flyout Inserir → Formas (sem linhas). */
export const COMUNICADO_SHAPE_LIBRARY_FLYOUT_CATEGORIES: ComunicadoShapeCatalogCategory[] =
  COMUNICADO_SHAPE_CATALOG_CATEGORIES.filter((category) => category.libraryFlyout);

/**
 * Menu Inserir → Linha (paridade Google Slides).
 * Fase 0: Linha e Seta inserem bloco; demais tools entram nas Fases 2/3.
 */
export const COMUNICADO_LINE_TOOLS: ComunicadoLineToolDefinition[] = [
  /** Fase 2: Linha/Seta/conectores desenham no palco (sem insertKind). */
  { id: "line", label: "Linha", ready: true },
  { id: "line-arrow", label: "Seta", ready: true },
  { id: "elbow-connector", label: "Conector angulado", ready: true },
  { id: "curved-connector", label: "Conector curvado", ready: true },
  { id: "curve", label: "Curva", ready: true },
  { id: "polyline", label: "Polilinha", ready: true },
  { id: "scribble", label: "Rabisco", ready: true },
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

export function isComunicadoLineToolId(value: string): value is ComunicadoLineToolId {
  return COMUNICADO_LINE_TOOLS.some((tool) => tool.id === value);
}
