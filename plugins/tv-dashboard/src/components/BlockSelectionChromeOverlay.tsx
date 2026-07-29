import type { PointerEvent as ReactPointerEvent, CSSProperties } from "react";
import {
  shapeBlockAllowsResize,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { buildBlockTransformCss } from "../utils/comunicadoTransform";
import { resolveSelectionChromeOverlayZIndex } from "../utils/resolveBlockWrapStackZIndex";
import { resolveSelectionChromeMetrics } from "../utils/selectionChromeMetrics";
import { BlockSelectionChrome } from "./BlockSelectionChrome";
import type { BlockDragMode } from "./useCanvasBlockInteraction";

type Props = {
  block: ComunicadoBlock;
  designWidth: number;
  designHeight: number;
  stageZoom?: number;
  isPrimarySelection: boolean;
  onPointerDown: (
    event: ReactPointerEvent<HTMLElement>,
    block: ComunicadoBlock,
    mode: BlockDragMode,
  ) => void;
  onResizeHandleDoubleClick?: (
    event: ReactPointerEvent<HTMLElement>,
    block: ComunicadoBlock,
    mode: Extract<BlockDragMode, `resize-${string}`>,
  ) => void;
};

/**
 * Chrome de seleção no palco (irmão dos wraps) — handles/outline acima do
 * conteúdo sem elevar o z-index do bloco (ordem de camadas do modelo).
 */
export function BlockSelectionChromeOverlay({
  block,
  designWidth,
  designHeight,
  stageZoom = 1,
  isPrimarySelection,
  onPointerDown,
  onResizeHandleDoubleClick,
}: Props) {
  const wrapTransform = buildBlockTransformCss(block.style);
  const frameW = Math.max(1, (block.frame.w / 100) * designWidth);
  const frameH = Math.max(1, (block.frame.h / 100) * designHeight);
  const metrics = resolveSelectionChromeMetrics(stageZoom);
  const style: CSSProperties = {
    left: `${block.frame.x}%`,
    top: `${block.frame.y}%`,
    width: `${block.frame.w}%`,
    height: `${block.frame.h}%`,
    zIndex: resolveSelectionChromeOverlayZIndex({
      isPrimarySelection,
      modelZIndex: block.style?.zIndex,
    }),
    ...(wrapTransform
      ? { transform: wrapTransform, transformOrigin: "center center" }
      : {}),
  };

  return (
    <div
      className={[
        "td-composer__block-chrome",
        isPrimarySelection ? "" : "td-composer__block-chrome--multi",
      ]
        .filter(Boolean)
        .join(" ")}
      style={style}
      data-block-chrome=""
      data-block-id={block.id}
      aria-hidden="true"
    >
      <BlockSelectionChrome
        block={block}
        designShortSidePx={Math.min(frameW, frameH)}
        designWidthPx={frameW}
        designHeightPx={frameH}
        handleSizePx={metrics.handleSize}
        adjustSizePx={metrics.adjustSize}
        rotateStemPx={metrics.rotateStem}
        allowResize={block.type === "shape" ? shapeBlockAllowsResize(block) : true}
        onPointerDown={onPointerDown}
        onResizeHandleDoubleClick={onResizeHandleDoubleClick}
      />
    </div>
  );
}
