/** Cor sólida com opacidade (0–1). */
export type ColorValue = {
  hex: string;
  alpha: number;
};

/** Preenchimento de forma — sólido ou transparente. */
export type FillValue =
  | { kind: "solid"; color: ColorValue }
  | { kind: "none" };

/** Contorno de forma. */
export type OutlineValue = {
  color: ColorValue | null;
  width: number;
  dash?: "solid" | "dashed" | "dotted";
};

export type ShapeStylePreset = {
  id: string;
  label?: string;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  boxShadow?: string;
};

export type ShapeColorLabels = {
  themeColors?: string;
  standardColors?: string;
  noFill?: string;
  noOutline?: string;
  /** Cor de texto automática (contraste com o fundo). */
  automatic?: string;
  moreColors?: string;
  eyedropper?: string;
  image?: string;
  gradient?: string;
  texture?: string;
  fill?: string;
  outline?: string;
  thickness?: string;
  dashed?: string;
  lineStyle?: string;
  arrows?: string;
  effects?: string;
  preset?: string;
  shadow?: string;
  reflection?: string;
  glow?: string;
  softEdges?: string;
  bevel?: string;
  rotation3d?: string;
  themeStyles?: string;
  presets?: string;
  colorDialogTitle?: string;
  tabStandard?: string;
  tabCustom?: string;
  newColor?: string;
  currentColor?: string;
  red?: string;
  green?: string;
  blue?: string;
  hex?: string;
  transparency?: string;
  colorModel?: string;
  ok?: string;
  cancel?: string;
};

export type ThemePalette = readonly string[];
