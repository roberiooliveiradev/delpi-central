import type { ComunicadoBlockStyle, ComunicadoContentRun } from "./comunicadoTypes";
import {
  isComunicadoVisualBoxBlock,
  type ComunicadoVisualBoxBlock,
} from "./comunicadoVisualBox";
import { syncTextBlockFields } from "./comunicadoContentRuns";

export type ClearVisualBoxTextFormattingPatch = {
  content: string;
  contentRuns: ComunicadoContentRun[] | undefined;
  style: ComunicadoBlockStyle;
  textProjection?: undefined;
};

const TEXT_PRESENTATION_STYLE_KEYS = [
  "fontFamily",
  "fontSize",
  "fontWeight",
  "fontStyle",
  "color",
  "colorPaint",
  "textDecoration",
  "textHighlight",
  "textAlign",
  "verticalAlign",
  "lineHeight",
  "letterSpacing",
  "paragraphSpacingBefore",
  "paragraphSpacingAfter",
  "baselineShift",
  "indentLevel",
  "textCase",
  "textShadow",
  "textStrokeColor",
  "textStrokeWidth",
  "textReflection",
  "namedStyle",
] as const;

/**
 * Strip run-level text presentation; keep dataRef / displayFormat / binding intact.
 */
function stripRunTextPresentation(run: ComunicadoContentRun): ComunicadoContentRun {
  if (run.dataRef?.field?.trim()) {
    return { text: run.text ?? "", dataRef: run.dataRef };
  }
  return { text: run.text ?? "" };
}

function preserveBoundContentRuns(
  runs: ComunicadoContentRun[] | undefined,
): ComunicadoContentRun[] | undefined {
  if (!runs?.length) return undefined;
  const hasBinding = runs.some((run) => Boolean(run.dataRef?.field?.trim()));
  if (!hasBinding) return undefined;
  return runs.map(stripRunTextPresentation);
}

function resetTextPresentationStyle(
  block: ComunicadoVisualBoxBlock,
  defaults: ComunicadoBlockStyle,
): ComunicadoBlockStyle {
  if (block.type === "heading" || block.type === "text") {
    const next: ComunicadoBlockStyle = {
      ...defaults,
      zIndex: block.style?.zIndex ?? defaults.zIndex,
      fill: block.style?.fill ?? defaults.fill,
      backgroundColor: block.style?.backgroundColor ?? defaults.backgroundColor,
      stroke: block.style?.stroke ?? defaults.stroke,
      strokeWidth: block.style?.strokeWidth ?? defaults.strokeWidth,
      borderWidth: block.style?.borderWidth ?? defaults.borderWidth,
      borderColor: block.style?.borderColor ?? defaults.borderColor,
      borderRadius: block.style?.borderRadius,
      boxShadow: block.style?.boxShadow,
      opacity: block.style?.opacity,
    };
    for (const key of TEXT_PRESENTATION_STYLE_KEYS) {
      if (key in next && !(key in defaults)) {
        delete next[key as keyof ComunicadoBlockStyle];
      }
    }
    return next;
  }
  const next: ComunicadoBlockStyle = { ...block.style };
  next.fontFamily = defaults.fontFamily;
  next.fontSize = defaults.fontSize;
  next.fontWeight = defaults.fontWeight;
  next.fontStyle = undefined;
  next.color = defaults.color;
  next.textDecoration = undefined;
  next.textHighlight = undefined;
  next.textAlign = defaults.textAlign;
  next.verticalAlign = defaults.verticalAlign;
  next.lineHeight = defaults.lineHeight;
  next.letterSpacing = undefined;
  next.paragraphSpacingBefore = undefined;
  next.paragraphSpacingAfter = undefined;
  next.baselineShift = undefined;
  next.indentLevel = undefined;
  next.textCase = undefined;
  next.textShadow = undefined;
  next.textStrokeColor = undefined;
  next.textStrokeWidth = undefined;
  next.textReflection = undefined;
  return next;
}

/**
 * Limpa tipografia da caixa (TEXT PRESENTATION).
 * NÃO remove binding / dataRef / displayFormat / textProjection field.
 * Em heading/text sem binding, compacta para texto plano (comportamento legado).
 */
export function clearVisualBoxTextFormatting(
  block: ComunicadoVisualBoxBlock,
  defaults: ComunicadoBlockStyle,
): ClearVisualBoxTextFormattingPatch {
  const boundRuns = preserveBoundContentRuns(
    "contentRuns" in block ? block.contentRuns : undefined,
  );
  const hasTextProjection =
    "textProjection" in block &&
    Boolean(
      block.textProjection &&
        typeof block.textProjection === "object" &&
        String((block.textProjection as { field?: string }).field || "").trim(),
    );

  if (boundRuns || hasTextProjection) {
    const plain = syncTextBlockFields(
      block.content ?? "",
      boundRuns ?? ("contentRuns" in block ? block.contentRuns : undefined),
    );
    return {
      content: plain.content,
      contentRuns: boundRuns ?? plain.contentRuns,
      style: resetTextPresentationStyle(block, defaults),
    };
  }

  const plain = syncTextBlockFields(block.content ?? "", undefined);
  return {
    content: plain.content,
    contentRuns: undefined,
    style: resetTextPresentationStyle(block, defaults),
  };
}

/** Type guard helper for callers that receive ComunicadoBlock. */
export function isClearableVisualBox(
  block: { type: string } | null | undefined,
): block is ComunicadoVisualBoxBlock {
  return Boolean(block && isComunicadoVisualBoxBlock(block as ComunicadoVisualBoxBlock));
}
