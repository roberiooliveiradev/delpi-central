import {
  joinContentLinesToRuns,
  splitContentRunsIntoLines,
  type ContentLineSegment,
} from "./comunicadoContentList";
import { plainTextFromContentRuns } from "./comunicadoContentRuns";
import {
  namedTextStylePreset,
  stripNamedStyleFromRunStyle,
} from "./comunicadoNamedTextStyles";
import {
  stripContentRunStylesOverriddenByContainer,
  typographyKeysFromContainerPatch,
  type ContainerTypographyStyleKey,
} from "./containerTypographyOverride";
import { defaultStyle } from "./comunicadoHelpers";
import type {
  ComunicadoBlockStyle,
  ComunicadoContentRun,
  ComunicadoContentRunStyle,
  ComunicadoNamedTextStyle,
} from "./comunicadoTypes";
import type { ComunicadoVisualBoxBlock } from "./comunicadoVisualBox";

/** Tipografia efetiva visível na caixa visual — espelha contrato da ribbon Fonte. */
export type VisualBoxTextFormatSnapshot = {
  fontFamily?: string;
  fontSize?: number;
  fontWeight?: string;
  fontStyle?: string;
  color?: string;
  colorPaint?: ComunicadoBlockStyle["colorPaint"];
  textDecoration?: string;
  textHighlight?: string;
  textAlign?: string;
  verticalAlign?: string;
  textShadow?: string;
  textStrokeColor?: string;
  textStrokeWidth?: number;
  textReflection?: boolean;
};

function resolveBlockRuns(block: ComunicadoVisualBoxBlock): ComunicadoContentRun[] {
  if (block.contentRuns?.length) return block.contentRuns;
  const text = block.content ?? "";
  return text ? [{ text }] : [];
}

function lineNamedStyle(line: ContentLineSegment): ComunicadoNamedTextStyle | undefined {
  if (line.namedStyle) return line.namedStyle;
  for (const run of line.runs) {
    if (run.style?.namedStyle) return run.style.namedStyle;
  }
  return undefined;
}

function effectiveTypographyForLine(line: ContentLineSegment): ComunicadoContentRunStyle {
  const merged: ComunicadoContentRunStyle = {};
  const named = lineNamedStyle(line);
  if (named) Object.assign(merged, namedTextStylePreset(named));
  for (const run of line.runs) {
    if (!run.style) continue;
    const inline = stripNamedStyleFromRunStyle(run.style) ?? {};
    Object.assign(merged, inline);
    if (run.style.namedStyle && !named) {
      Object.assign(merged, namedTextStylePreset(run.style.namedStyle));
    }
  }
  return merged;
}

function aggregateOptional<T>(values: Array<T | undefined>): T | undefined {
  const defined = values.filter((value): value is T => value != null);
  if (defined.length === 0) return undefined;
  const [first] = defined;
  return defined.every((value) => value === first) ? first : undefined;
}

function snapshotFromBlockStyle(
  style: ComunicadoBlockStyle | undefined,
  defaults: ComunicadoBlockStyle,
): VisualBoxTextFormatSnapshot {
  const fontSize = style?.fontSize ?? defaults.fontSize;
  return {
    fontFamily: style?.fontFamily ?? defaults.fontFamily,
    fontSize: typeof fontSize === "number" && fontSize > 0 ? fontSize : undefined,
    fontWeight:
      style?.fontWeight != null ? String(style.fontWeight) : defaults.fontWeight != null
        ? String(defaults.fontWeight)
        : undefined,
    fontStyle: style?.fontStyle ?? defaults.fontStyle,
    color: style?.color ?? defaults.color,
    colorPaint: style?.colorPaint,
    textDecoration: style?.textDecoration,
    textHighlight: style?.textHighlight,
    textAlign: style?.textAlign ?? defaults.textAlign,
    verticalAlign: style?.verticalAlign ?? defaults.verticalAlign,
    textShadow: style?.textShadow,
    textStrokeColor: style?.textStrokeColor,
    textStrokeWidth: style?.textStrokeWidth,
    textReflection: style?.textReflection,
  };
}

/**
 * Tipografia efetiva que o usuário vê — agrega runs + namedStyle; efeitos de caixa vêm de block.style.
 */
export function resolveVisualBoxEffectiveTextFormatSnapshot(
  block: ComunicadoVisualBoxBlock,
): VisualBoxTextFormatSnapshot {
  const defaults =
    block.type === "shape"
      ? defaultStyle("shape", block.shape)
      : defaultStyle(block.type);
  const container = snapshotFromBlockStyle(block.style, defaults);
  const runs = resolveBlockRuns(block);
  if (!runs.length || !plainTextFromContentRuns(runs).trim()) {
    return container;
  }

  const lines = splitContentRunsIntoLines(runs);
  const lineTypographies = lines.map((line) => effectiveTypographyForLine(line));

  const fontFamily = aggregateOptional(lineTypographies.map((item) => item.fontFamily));
  const fontSize = aggregateOptional(lineTypographies.map((item) => item.fontSize));
  const fontWeight = aggregateOptional(
    lineTypographies.map((item) =>
      item.fontWeight != null ? String(item.fontWeight) : undefined,
    ),
  );
  const fontStyle = aggregateOptional(lineTypographies.map((item) => item.fontStyle));
  const color = aggregateOptional(lineTypographies.map((item) => item.color));
  const textHighlight = aggregateOptional(lineTypographies.map((item) => item.textHighlight));
  const textDecoration = aggregateOptional(lineTypographies.map((item) => item.textDecoration));

  return {
    fontFamily: fontFamily ?? container.fontFamily,
    fontSize: fontSize ?? container.fontSize,
    fontWeight: fontWeight ?? container.fontWeight,
    fontStyle: fontStyle ?? container.fontStyle,
    color: color ?? container.color,
    colorPaint: container.colorPaint,
    textDecoration: textDecoration ?? container.textDecoration,
    textHighlight: textHighlight ?? container.textHighlight,
    textAlign: container.textAlign,
    verticalAlign: container.verticalAlign,
    textShadow: container.textShadow,
    textStrokeColor: container.textStrokeColor,
    textStrokeWidth: container.textStrokeWidth,
    textReflection: container.textReflection,
  };
}

function materializeLineNamedStyle(
  line: ContentLineSegment,
  keys: readonly ContainerTypographyStyleKey[],
): ContentLineSegment {
  const named = lineNamedStyle(line);
  if (!named) return line;

  const preset = namedTextStylePreset(named);
  const affectsPreset = keys.some(
    (key) => key in preset || key === "fontWeight" || key === "fontStyle" || key === "fontSize",
  );
  if (!affectsPreset) return line;

  const materializedBase = { ...preset };
  const nextRuns = line.runs.map((run) => {
    const inline = stripNamedStyleFromRunStyle(run.style) ?? {};
    const merged: ComunicadoContentRunStyle = { ...materializedBase, ...inline };
    return Object.keys(merged).length > 0
      ? { text: run.text, style: merged }
      : { text: run.text };
  });

  return {
    runs: nextRuns,
    listType: line.listType,
    namedStyle: undefined,
  };
}

/**
 * Expande preset namedStyle em inline quando o container sobrescreve tipografia.
 */
export function materializeNamedStylesForContainerOverride(
  runs: ComunicadoContentRun[] | undefined,
  keys: readonly ContainerTypographyStyleKey[],
): ComunicadoContentRun[] | undefined {
  if (!runs?.length || keys.length === 0) return runs;
  const lines = splitContentRunsIntoLines(runs);
  const hasNamed = lines.some((line) => lineNamedStyle(line) != null);
  if (!hasNamed) return runs;
  const nextLines = lines.map((line) => materializeLineNamedStyle(line, keys));
  return joinContentLinesToRuns(nextLines);
}

/**
 * Patch tipográfico de container: materializa namedStyle + strip nos runs.
 * Caller aplica patch em block.style antes ou depois conforme fluxo do editor.
 */
export function applyVisualBoxContentRunsTypographyOverride(
  block: ComunicadoVisualBoxBlock,
  typographyKeys: readonly ContainerTypographyStyleKey[],
): ComunicadoVisualBoxBlock {
  if (!typographyKeys.length || !block.contentRuns?.length) return block;
  let runs = materializeNamedStylesForContainerOverride(block.contentRuns, typographyKeys);
  runs = stripContentRunStylesOverriddenByContainer(runs, typographyKeys);
  return { ...block, contentRuns: runs };
}

export function applyVisualBoxContainerTypographyPatch(
  block: ComunicadoVisualBoxBlock,
  patch: Partial<ComunicadoBlockStyle>,
): ComunicadoVisualBoxBlock {
  const typographyKeys = typographyKeysFromContainerPatch(patch);
  const nextStyle: ComunicadoBlockStyle = { ...block.style, ...patch };
  let next: ComunicadoVisualBoxBlock = { ...block, style: nextStyle };
  if (typographyKeys.length > 0) {
    next = applyVisualBoxContentRunsTypographyOverride(next, typographyKeys);
  }
  return next;
}
