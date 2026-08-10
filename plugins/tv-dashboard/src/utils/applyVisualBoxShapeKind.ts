import {
  defaultFrame,
  defaultStrokeWidthForPrimitive,
  isComunicadoVisualBoxBlock,
  resolveShapePrimitive,
  resolveVisualBoxShapeKind,
  type ComunicadoBlock,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";

/**
 * Patch para «Alterar forma» — mantém posição; só recalcula frame/stroke
 * quando o primitivo muda (ex.: retângulo → linha).
 * Canônico para ribbon e menu de contexto.
 */
export function buildVisualBoxShapeKindPatch(
  block: ComunicadoBlock,
  kind: ComunicadoShapeKind,
): Partial<ComunicadoBlock> | null {
  if (!isComunicadoVisualBoxBlock(block)) return null;

  const currentKind = resolveVisualBoxShapeKind(block);
  const prevPrimitive = resolveShapePrimitive(currentKind);
  const nextPrimitive = resolveShapePrimitive(kind);
  const patch: Record<string, unknown> = { shape: kind };

  if (prevPrimitive !== nextPrimitive) {
    const nextFrame = defaultFrame("shape", kind);
    patch.frame = {
      ...nextFrame,
      x: Math.max(0, Math.min(100 - nextFrame.w, block.frame.x)),
      y: Math.max(0, Math.min(100 - nextFrame.h, block.frame.y)),
    };
    patch.style = {
      ...block.style,
      strokeWidth:
        block.type === "heading" || block.type === "text"
          ? (block.style?.strokeWidth ?? block.style?.borderWidth ?? 0)
          : defaultStrokeWidthForPrimitive(nextPrimitive),
      ...(nextPrimitive === "point"
        ? { markerRadius: block.style?.markerRadius ?? (kind === "efficiency-pin" ? 32 : 8) }
        : {}),
    };
  }

  if (kind === "efficiency-pin") {
    patch.efficiencyPin =
      block.type === "shape" && block.efficiencyPin
        ? block.efficiencyPin
        : { role: "pin", infoMode: "attached" };
    const baseStyle = (patch.style as Record<string, unknown> | undefined) ?? {
      ...block.style,
    };
    patch.style = {
      ...baseStyle,
      fill: "transparent",
      stroke: "transparent",
      strokeWidth: 0,
    };
  } else if (block.type === "shape" && block.efficiencyPin) {
    patch.efficiencyPin = undefined;
  }

  return patch as Partial<ComunicadoBlock>;
}
