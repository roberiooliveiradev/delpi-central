import type { ComunicadoImageCrop } from "./comunicadoImageCrop";
import type { ComunicadoChartOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartPartsMap } from "./comunicadoChartParts";
import type { ComunicadoTableOptions } from "./comunicadoTableOptions";
import type { ComunicadoTablePartsMap } from "./comunicadoTableParts";

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

/** Estilo de parágrafo nomeado (4C.4) — aplicado por linha via `contentRuns`. */
export type ComunicadoNamedTextStyle = "title1" | "subtitle" | "body";

export type ComunicadoShapeKind =
  | "point"
  | "rectangle"
  | "rounded-rect"
  | "snip-rect"
  | "round-same-side-rect"
  | "ellipse"
  | "triangle"
  | "right-triangle"
  | "parallelogram"
  | "trapezoid"
  | "diamond"
  | "pentagon"
  | "hexagon"
  | "octagon"
  | "cross"
  | "cylinder"
  | "heart"
  | "lightning"
  | "cloud"
  | "moon"
  | "sun"
  | "arrow-right"
  | "arrow-left"
  | "arrow-up"
  | "arrow-down"
  | "arrow-left-right"
  | "arrow-up-down"
  | "chevron-right"
  | "chevron-left"
  | "notched-arrow-right"
  | "star"
  | "star-4"
  | "star-6"
  | "star-8"
  | "banner"
  | "wave"
  | "line"
  | "line-arrow-right"
  | "line-arrow-left"
  | "line-arrow-both"
  | "flowchart-process"
  | "flowchart-decision"
  | "flowchart-terminator"
  | "flowchart-data"
  | "flowchart-document"
  | "flowchart-preparation"
  | "callout-rect"
  | "callout-rounded"
  | "callout-cloud"
  | "equation-plus"
  | "equation-minus"
  | "equation-multiply"
  | "equation-divide"
  | "equation-equal";

export type ComunicadoContentRunStyle = {
  fontSize?: number;
  color?: string;
  fontFamily?: string;
  textHighlight?: string;
  fontWeight?: "normal" | "bold";
  fontStyle?: "normal" | "italic";
  textDecoration?: ComunicadoTextDecoration;
  lineHeight?: number;
  /** Marcador de parágrafo (4C.3) — aplicado por linha (`\n` separa itens). */
  listType?: ComunicadoListType;
  /** Estilo nomeado (4C.4) — Título 1, Subtítulo ou Corpo por linha. */
  namedStyle?: ComunicadoNamedTextStyle;
  /** Sombra tipográfica (CSS text-shadow). */
  textShadow?: string;
  /** Contorno do glifo (cor). */
  textStrokeColor?: string;
  /** Contorno do glifo (px). */
  textStrokeWidth?: number;
  /** Reflexo tipográfico espelhado. */
  textReflection?: boolean;
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
  /** Sombra tipográfica (CSS text-shadow) — distinta de boxShadow do bloco. */
  textShadow?: string;
  textStrokeColor?: string;
  textStrokeWidth?: number;
  /** Reflexo tipográfico (`-webkit-box-reflect`). */
  textReflection?: boolean;
  opacity?: number;
  rotation?: number;
  zIndex?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  /** Raio visual do marcador (px) — só primitivo ponto. */
  markerRadius?: number;
  /**
   * Ajustes de geometria (modelo PowerPoint Adjustments).
   * Valores tipicamente 0–1; cada índice corresponde a um handle amarelo.
   */
  adjustments?: number[];
};

export type ComunicadoBlockAnimationKind = "fade" | "slide-in";

export type ComunicadoBlockAnimationDirection = "up" | "down" | "left" | "right";

export type ComunicadoBlockAnimationEasing = "ease" | "ease-out" | "ease-in-out" | "linear";

export type ComunicadoBlockAnimation = {
  phase: "entrance";
  kind: ComunicadoBlockAnimationKind;
  delayMs?: number;
  durationMs?: number;
  easing?: ComunicadoBlockAnimationEasing;
  /** Direção do deslize (`slide-in`); padrão `up`. */
  direction?: ComunicadoBlockAnimationDirection;
};

export type ComunicadoBlockBase = {
  id: string;
  frame: ComunicadoFrame;
  style?: ComunicadoBlockStyle;
  groupId?: string;
  /** Animações do bloco (4E.2) — entrada na TV. */
  animations?: ComunicadoBlockAnimation[];
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

export type ComunicadoGeometryVertex = { x: number; y: number };

/** Ligação entre blocos (MVP conector) — ver `comunicadoConnectors`. */
export type ComunicadoShapeConnector = {
  fromBlockId: string;
  toBlockId: string;
  fromAnchor?: "center" | "n" | "s" | "e" | "w";
  toAnchor?: "center" | "n" | "s" | "e" | "w";
};

export type ComunicadoShapeBlock = ComunicadoBlockBase & {
  type: "shape";
  shape: ComunicadoShapeKind;
  /** Vértices explícitos (%): 1 ponto, ≥2 linha, ≥3 forma fechada. */
  vertices?: ComunicadoGeometryVertex[];
  /**
   * Ligação a outros blocos (MVP conector). Endpoints derivados → `vertices`/`frame`.
   * Só faz sentido em kinds de linha (`line`, `line-arrow-*`).
   */
  connector?: ComunicadoShapeConnector;
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
  /** Campo principal (legado). Preferir `selectedValueFields` para multi-métrica. */
  valueField?: string;
  /** Campos exibidos no visual; vazio/ausente = todas as métricas disponíveis da rota. */
  selectedValueFields?: string[];
  maxRows?: number;
  refreshSec?: number;
};

export type ComunicadoDataBlockType = "data_kpi" | "data_chart" | "data_table" | "data_metric";

/** Tipos de gráfico para blocos `chart_view` (catálogo completo). */
export type ComunicadoChartType =
  | "line"
  | "bar"
  | "area"
  | "stacked_bar"
  | "pie"
  | "doughnut"
  | "scatter"
  | "bubble"
  | "radar"
  | "combo"
  | "waterfall"
  | "funnel"
  | "histogram";

export type ComunicadoTablePreset = "grid" | "minimal" | "banded";

export type ComunicadoDataSourceBlock = ComunicadoBlockBase & {
  type: "data_source";
  dataBinding: ComunicadoDataBinding;
  resolved?: ComunicadoDataResolved;
};

export type ComunicadoChartViewBlock = ComunicadoBlockBase & {
  type: "chart_view";
  chartType: ComunicadoChartType;
  dataSourceId?: string;
  /** Override da seleção de métricas da fonte (escalares multi-campo). */
  selectedValueFields?: string[];
  valueField?: string;
  chartOptions?: ComunicadoChartOptions;
  /** Onda 4G — estilo/visibilidade por parte (adapter com chartOptions). */
  chartParts?: ComunicadoChartPartsMap;
  resolved?: ComunicadoDataResolved;
};

export type ComunicadoTableViewBlock = ComunicadoBlockBase & {
  type: "table_view";
  tablePreset: ComunicadoTablePreset;
  tableOptions?: ComunicadoTableOptions;
  /** Onda 4G.8 — estilo/visibilidade por parte (adapter com tableOptions). */
  tableParts?: ComunicadoTablePartsMap;
  dataSourceId?: string;
  selectedValueFields?: string[];
  valueField?: string;
  /** Truncamento de exibição: máx. de linhas (vazio = todas do resolved, com scroll). */
  maxRows?: number;
  /** Truncamento de exibição: máx. de colunas (vazio = todas). */
  maxCols?: number;
  resolved?: ComunicadoDataResolved;
};

/** Grade estática editável, independente de fontes de dados. */
export type ComunicadoCanvasTableBlock = ComunicadoBlockBase & {
  type: "canvas_table";
  rows: number;
  cols: number;
  cells: string[][];
  headerRow?: boolean;
};

export type ComunicadoKpiViewBlock = ComunicadoBlockBase & {
  type: "kpi_view";
  dataSourceId?: string;
  selectedValueFields?: string[];
  valueField?: string;
  kpiOptions?: import("./comunicadoKpiOptions").ComunicadoKpiOptions;
  /** Partes primitivas (card/title/value/hint/icon) — padrão chartParts. */
  kpiParts?: import("./comunicadoKpiParts").ComunicadoKpiPartsMap;
  resolved?: ComunicadoDataResolved;
};

export type ComunicadoDataBlock = ComunicadoBlockBase & {
  type: ComunicadoDataBlockType;
  dataBinding: ComunicadoDataBinding;
  resolved?: ComunicadoDataResolved;
};

export type ComunicadoDataTableColumn = {
  key: string;
  label: string;
};

export type ComunicadoDataKpiMetric = {
  field: string;
  value?: unknown;
  label: string;
};

export type ComunicadoDataResolved = {
  meta?: Record<string, unknown>;
  data?: unknown;
  error?: string | null;
  /** Mensagem bruta da api-delpi / gateway (quando o error foi genérico legado). */
  detail?: string | null;
  statusCode?: number | null;
  displayMode?: string;
  label?: string;
  kpi?: { value?: unknown; label?: string };
  /** Métricas escalares disponíveis (multi-campo). */
  kpiMetrics?: ComunicadoDataKpiMetric[];
  chart?: {
    points?: Array<{ label?: unknown; value?: unknown }>;
    chartType?: "line" | "bar";
  };
  table?: {
    rows?: Array<Record<string, unknown>>;
    columns?: ComunicadoDataTableColumn[];
  };
};

export type ComunicadoBlock =
  | ComunicadoTextBlock
  | ComunicadoMediaBlock
  | ComunicadoShapeBlock
  | ComunicadoIconBlock
  | ComunicadoDataBlock
  | ComunicadoDataSourceBlock
  | ComunicadoChartViewBlock
  | ComunicadoTableViewBlock
  | ComunicadoCanvasTableBlock
  | ComunicadoKpiViewBlock;

export type ComunicadoDataFilters = Record<string, string | number | boolean | null>;

export type ComunicadoConfig = {
  version?: number;
  headline?: string;
  subtitle?: string;
  background?: ComunicadoBackground;
  blocks?: ComunicadoBlock[];
  dataFilters?: ComunicadoDataFilters;
  /** Notas do apresentador (não exibidas no kiosk TV). */
  speakerNotes?: string;
  /** Fontes custom da playlist referenciadas neste slide. */
  customFonts?: ComunicadoCustomFontRef[];
};

export type ComunicadoCustomFontRef = {
  assetId: string;
  familyName: string;
  /** URL enriquecida no payload (admin/public); opcional no persistido. */
  url?: string;
  fontFamily?: string;
};

export type ComunicadoScreenData = {
  version?: number;
  headline?: string;
  subtitle?: string;
  background?: ComunicadoBackground;
  blocks?: ComunicadoBlock[];
  dataFilters?: ComunicadoDataFilters;
  customFonts?: ComunicadoCustomFontRef[];
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
/**
 * @deprecated Sem teto tipográfico — só sugerido nos presets. Preferir `clampFontSize` (só min).
 * Mantido para compatibilidade de imports antigos.
 */
export const COMUNICADO_FONT_SIZE_MAX = Number.POSITIVE_INFINITY;
export const COMUNICADO_FONT_SIZE_STEP = 2;

/** Presets da lista do controle de tamanho (usuário ainda pode digitar valores fora da lista). */
export const COMUNICADO_FONT_SIZE_PRESETS = [
  12, 14, 16, 18, 20, 22, 24, 28, 32, 36, 40, 44, 48, 54, 60, 72, 80, 96, 120, 144, 192, 288,
] as const;

export const COMUNICADO_LINE_HEIGHT_OPTIONS = [1, 1.15, 1.5, 2] as const;

export const COMUNICADO_ICON_OPTIONS: Array<{ name: string; label: string }> = [
  { name: "Star", label: "Estrela" },
  { name: "Factory", label: "Fábrica" },
  { name: "TrendingUp", label: "Tendência" },
  { name: "TrendingDown", label: "Queda" },
  { name: "Gauge", label: "Indicador" },
  { name: "Activity", label: "Atividade" },
  { name: "Target", label: "Meta" },
  { name: "Users", label: "Equipe" },
  { name: "Shield", label: "Segurança" },
  { name: "AlertTriangle", label: "Alerta" },
  { name: "CheckCircle2", label: "Concluído" },
  { name: "BarChart3", label: "Gráfico" },
  { name: "Percent", label: "Percentual" },
  { name: "DollarSign", label: "Financeiro" },
  { name: "Package", label: "Produto" },
];
