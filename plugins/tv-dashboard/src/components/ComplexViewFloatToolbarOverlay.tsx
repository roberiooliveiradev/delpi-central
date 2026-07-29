import type { CSSProperties } from "react";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { buildBlockTransformCss } from "../utils/comunicadoTransform";
import { resolveSelectionFloatToolbarOverlayZIndex } from "../utils/resolveBlockWrapStackZIndex";
import { ComplexViewFloatToolbar } from "./ComplexViewFloatToolbar";

type FramePercent = { x: number; y: number; w: number; h: number };

/** Estilo do shell de float — frame em % do container pai (palco ou group-layer). */
export function buildComplexViewFloatOverlayStyle(params: {
  frame: FramePercent;
  modelZIndex?: number | null;
  transform?: string;
}): CSSProperties {
  return {
    left: `${params.frame.x}%`,
    top: `${params.frame.y}%`,
    width: `${params.frame.w}%`,
    height: `${params.frame.h}%`,
    zIndex: resolveSelectionFloatToolbarOverlayZIndex({
      modelZIndex: params.modelZIndex,
    }),
    ...(params.transform
      ? { transform: params.transform, transformOrigin: "center center" }
      : {}),
  };
}

type Props = {
  block: ComunicadoBlock;
  /**
   * Frame em % do container pai. Default: frame do bloco no palco (design).
   * Em group-layer, passar coords locais do gesto.
   */
  framePercent?: FramePercent;
  transform?: string;
};

/**
 * Float (+ / pincel / funil) no palco — irmão do chrome de seleção.
 * z-index centralizado acima dos handles (resolveSelectionFloatToolbarOverlayZIndex).
 */
export function ComplexViewFloatToolbarOverlay({
  block,
  framePercent,
  transform,
}: Props) {
  const frame = framePercent ?? {
    x: block.frame.x,
    y: block.frame.y,
    w: block.frame.w,
    h: block.frame.h,
  };
  const wrapTransform =
    transform ?? buildBlockTransformCss(block.style) ?? undefined;
  const style = buildComplexViewFloatOverlayStyle({
    frame,
    modelZIndex: block.style?.zIndex,
    transform: wrapTransform,
  });

  return (
    <div
      className="td-composer__block-float"
      style={style}
      data-block-float=""
      data-block-id={block.id}
    >
      <ComplexViewFloatToolbar block={block} />
    </div>
  );
}
