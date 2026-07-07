export type ComunicadoFrame = {
  x: number;
  y: number;
  w: number;
  h: number;
};

export type ComunicadoTextAlign = "left" | "center" | "right";

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
  fontWeight?: "normal" | "bold";
  fontStyle?: "normal" | "italic";
  textDecoration?: "none" | "underline";
  objectFit?: "cover" | "contain";
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
  borderRadius?: number;
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
};

export type ComunicadoShapeBlock = ComunicadoBlockBase & {
  type: "shape";
  shape: ComunicadoShapeKind;
  content?: string;
};

export type ComunicadoBlock =
  | ComunicadoTextBlock
  | ComunicadoMediaBlock
  | ComunicadoShapeBlock;

export type ComunicadoBackground =
  | { type: "color"; value: string }
  | { type: "image"; assetId?: string; url?: string; value?: string };

export type ComunicadoConfig = {
  version?: number;
  headline?: string;
  subtitle?: string;
  background?: ComunicadoBackground;
  blocks?: ComunicadoBlock[];
};

export type ComunicadoScreenData = {
  version?: number;
  headline?: string;
  subtitle?: string;
  background?: ComunicadoBackground;
  blocks?: ComunicadoBlock[];
};

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

export const COMUNICADO_SHAPE_KINDS: Array<{ kind: ComunicadoShapeKind; label: string }> = [
  { kind: "rectangle", label: "Retângulo" },
  { kind: "rounded-rect", label: "Retângulo arredondado" },
  { kind: "ellipse", label: "Elipse" },
  { kind: "triangle", label: "Triângulo" },
  { kind: "arrow-right", label: "Seta" },
  { kind: "line", label: "Linha" },
];
