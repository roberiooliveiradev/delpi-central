import type { ComunicadoBlockStyle } from "./comunicadoTypes";
import {
  isComunicadoVisualBoxBlock,
  type ComunicadoVisualBoxBlock,
} from "./comunicadoVisualBox";
import { syncTextBlockFields } from "./comunicadoContentRuns";

export type ClearVisualBoxTextFormattingPatch = {
  content: string;
  contentRuns: undefined;
  style: ComunicadoBlockStyle;
};

/**
 * Limpa tipografia da caixa e zera/compacta `contentRuns` (texto plano permanece).
 * Em heading/text, preserva chrome geométrico (fill/stroke/sombra da caixa).
 */
export function clearVisualBoxTextFormatting(
  block: ComunicadoVisualBoxBlock,
  defaults: ComunicadoBlockStyle,
): ClearVisualBoxTextFormattingPatch {
  const plain = syncTextBlockFields(block.content ?? "", undefined);
  if (block.type === "heading" || block.type === "text") {
    return {
      content: plain.content,
      contentRuns: undefined,
      style: {
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
      },
    };
  }
  return {
    content: plain.content,
    contentRuns: undefined,
    style: {
      ...block.style,
      fontFamily: defaults.fontFamily,
      fontSize: defaults.fontSize,
      fontWeight: defaults.fontWeight,
      fontStyle: undefined,
      color: defaults.color,
      textDecoration: undefined,
      textHighlight: undefined,
      textAlign: defaults.textAlign,
      verticalAlign: defaults.verticalAlign,
      lineHeight: defaults.lineHeight,
      letterSpacing: undefined,
      textShadow: undefined,
      textStrokeColor: undefined,
      textStrokeWidth: undefined,
      textReflection: undefined,
    },
  };
}

/** Type guard helper for callers that receive ComunicadoBlock. */
export function isClearableVisualBox(
  block: { type: string } | null | undefined,
): block is ComunicadoVisualBoxBlock {
  return Boolean(block && isComunicadoVisualBoxBlock(block as ComunicadoVisualBoxBlock));
}
