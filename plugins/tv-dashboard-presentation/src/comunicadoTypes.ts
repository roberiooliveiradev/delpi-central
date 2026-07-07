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

export type ComunicadoShapeKind =
  | "rectangle"
  | "rounded-rect"
  | "ellipse"
  | "triangle"
  | "arrow-right"
  | "line";

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
};

export type ComunicadoTextBlock = ComunicadoBlockBase & {
  type: "heading" | "text";
  content: string;
  href?: string;
  linkTarget?: "_blank" | "_self";
};

export type ComunicadoMediaBlock = ComunicadoBlockBase & {
  type: "image" | "video";
  assetId?: string;
  url?: string;
  href?: string;
  linkTarget?: "_blank" | "_self";
};

export type ComunicadoShapeBlock = ComunicadoBlockBase & {
  type: "shape";
  shape: ComunicadoShapeKind;
  content?: string;
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
  { kind: "line", label: "Linha" },
];
