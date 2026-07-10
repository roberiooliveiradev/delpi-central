import type { ComunicadoImageCrop } from "./comunicadoImageCrop";

export type ComunicadoFrame = {
  x: number;
  y: number;
  w: number;
  h: number;
};

export type ComunicadoTextAlign = "left" | "center" | "right" | "justify";

export type ComunicadoVerticalAlign = "top" | "middle" | "bottom";

export type ComunicadoTextDecoration =
  | "none"
  | "underline"
  | "line-through"
  | "underline line-through";

export type ComunicadoListType = "bullet" | "ordered";

export type ComunicadoShapeKind =
  | "rectangle"
  | "rounded-rect"
  | "ellipse"
  | "triangle"
  | "arrow-right"
  | "chevron-right"
  | "star"
  | "line";

export type ComunicadoContentRunStyle = {
  fontSize?: number;
  color?: string;
  fontFamily?: string;
  textHighlight?: string;
  fontWeight?: "normal" | "bold";
  fontStyle?: "normal" | "italic";
  textDecoration?: ComunicadoTextDecoration;
  /** Marcador de parágrafo (4C.3) — aplicado por linha (`\n` separa itens). */
  listType?: ComunicadoListType;
};

export type ComunicadoContentRun = {
  text: string;
  style?: ComunicadoContentRunStyle;
};

export type ComunicadoBlockStyle = {
  fontSize?: number;
  color?: string;
  fontFamily?: string;
  textAlign?: ComunicadoTextAlign;
  verticalAlign?: ComunicadoVerticalAlign;
  lineHeight?: number;
  letterSpacing?: number;
  textHighlight?: string;
  fontWeight?: "normal" | "bold";
  fontStyle?: "normal" | "italic";
  textDecoration?: ComunicadoTextDecoration;
  objectFit?: "cover" | "contain";
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
  borderRadius?: number;
  boxShadow?: string;
  opacity?: number;
  rotation?: number;
  zIndex?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
};

export type ComunicadoBlockBase = {
  id: string;
  frame: ComunicadoFrame;
  style?: ComunicadoBlockStyle;
  groupId?: string;
};

export type ComunicadoTextBlock = ComunicadoBlockBase & {
  type: "heading" | "text";
  /** Texto plano — espelha a concatenação de `contentRuns` ou fallback legado. */
  content: string;
  /** Trechos com estilo inline opcional (4C); omitido quando equivalente a `content` plano. */
  contentRuns?: ComunicadoContentRun[];
  href?: string;
  linkTarget?: "_blank" | "_self";
};

export type ComunicadoMediaBlock = ComunicadoBlockBase & {
  type: "image" | "video";
  assetId?: string;
  url?: string;
  href?: string;
  linkTarget?: "_blank" | "_self";
  imageCrop?: ComunicadoImageCrop;
};

export type ComunicadoShapeBlock = ComunicadoBlockBase & {
  type: "shape";
  shape: ComunicadoShapeKind;
  content?: string;
  href?: string;
  linkTarget?: "_blank" | "_self";
};

export type ComunicadoIconBlock = ComunicadoBlockBase & {
  type: "icon";
  iconName: string;
  href?: string;
  linkTarget?: "_blank" | "_self";
};

export type ComunicadoDataDisplayMode = "kpi" | "line_chart" | "bar_chart" | "table" | "auto";

export type ComunicadoDataBinding = {
  operationId: string;
  params?: Record<string, string | number | boolean | null>;
  displayMode?: ComunicadoDataDisplayMode;
  label?: string;
  valueField?: string;
  maxRows?: number;
  refreshSec?: number;
};

export type ComunicadoDataBlockType = "data_kpi" | "data_chart" | "data_table" | "data_metric";

export type ComunicadoDataBlock = ComunicadoBlockBase & {
  type: ComunicadoDataBlockType;
  dataBinding: ComunicadoDataBinding;
  resolved?: ComunicadoDataResolved;
};

export type ComunicadoDataResolved = {
  meta?: Record<string, unknown>;
  data?: unknown;
  error?: string | null;
  displayMode?: string;
  label?: string;
  kpi?: { value?: unknown; label?: string };
  chart?: { points?: Array<{ label?: unknown; value?: unknown }> };
  table?: { rows?: Array<Record<string, unknown>> };
};

export type ComunicadoBlock =
  | ComunicadoTextBlock
  | ComunicadoMediaBlock
  | ComunicadoShapeBlock
  | ComunicadoIconBlock
  | ComunicadoDataBlock;

export type ComunicadoDataFilters = Record<string, string | number | boolean | null>;

export type ComunicadoConfig = {
  version?: number;
  headline?: string;
  subtitle?: string;
  background?: ComunicadoBackground;
  blocks?: ComunicadoBlock[];
  dataFilters?: ComunicadoDataFilters;
};

export type ComunicadoScreenData = {
  version?: number;
  headline?: string;
  subtitle?: string;
  background?: ComunicadoBackground;
  blocks?: ComunicadoBlock[];
  dataFilters?: ComunicadoDataFilters;
};

export type ComunicadoBackground =
  | { type: "color"; value: string }
  | { type: "image"; assetId?: string; url?: string; value?: string }
  | { type: "gradient"; from: string; to: string; angle?: number };

export const COMUNICADO_FONT_FAMILIES = [
  "Inter, system-ui, sans-serif",
  "Arial, Helvetica, sans-serif",
  "Georgia, serif",
  "Times New Roman, Times, serif",
  "Courier New, Courier, monospace",
  "Verdana, Geneva, sans-serif",
  "Trebuchet MS, sans-serif",
  "Impact, Haettenschweiler, sans-serif",
] as const;

export const COMUNICADO_FONT_SIZE_MIN = 12;
export const COMUNICADO_FONT_SIZE_MAX = 120;
export const COMUNICADO_FONT_SIZE_STEP = 2;

export const COMUNICADO_LINE_HEIGHT_OPTIONS = [1, 1.15, 1.5, 2] as const;

export const COMUNICADO_SHAPE_KINDS: Array<{ kind: ComunicadoShapeKind; label: string }> = [
  { kind: "rectangle", label: "Retângulo" },
  { kind: "rounded-rect", label: "Retângulo arredondado" },
  { kind: "ellipse", label: "Elipse" },
  { kind: "triangle", label: "Triângulo" },
  { kind: "arrow-right", label: "Seta" },
  { kind: "chevron-right", label: "Chevron" },
  { kind: "star", label: "Estrela" },
  { kind: "line", label: "Linha" },
];

export const COMUNICADO_ICON_OPTIONS: Array<{ name: string; label: string }> = [
  { name: "Star", label: "Estrela" },
  { name: "Factory", label: "Fábrica" },
  { name: "TrendingUp", label: "Tendência" },
  { name: "Users", label: "Equipe" },
  { name: "Shield", label: "Segurança" },
  { name: "AlertTriangle", label: "Alerta" },
  { name: "CheckCircle2", label: "Concluído" },
  { name: "BarChart3", label: "Gráfico" },
];
