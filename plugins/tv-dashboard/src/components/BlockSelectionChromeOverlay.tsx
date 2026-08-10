import type { PointerEvent as ReactPointerEvent, CSSProperties } from "react";
import {
  EFFICIENCY_PIN_HIT_SIZE_PCT,
  ensureEfficiencyPinResizableFrame,
  isEfficiencyPinBlock,
  resolveBlockHitFrame,
  shapeBlockAllowsResize,
  type ComunicadoBlock,
  type ComunicadoShapeBlock,
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
  /* Pin CT legado (w/h≈0): frame migrado no chrome E no startFrame do drag. */
  const chromeBlock: ComunicadoBlock = isEfficiencyPinBlock(block)
    ? ensureEfficiencyPinResizableFrame(block as ComunicadoShapeBlock, {
        x: block.frame.x,
        y: block.frame.y,
        w: EFFICIENCY_PIN_HIT_SIZE_PCT,
        h: EFFICIENCY_PIN_HIT_SIZE_PCT,
      })
    : block;
  const hitFrame = resolveBlockHitFrame(chromeBlock);
  const wrapTransform = buildBlockTransformCss(chromeBlock.style);
  const frameW = Math.max(1, (hitFrame.w / 100) * designWidth);
  const frameH = Math.max(1, (hitFrame.h / 100) * designHeight);
  const metrics = resolveSelectionChromeMetrics(stageZoom);
  const style: CSSProperties = {
    left: `${hitFrame.x}%`,
    top: `${hitFrame.y}%`,
    width: `${hitFrame.w}%`,
    height: `${hitFrame.h}%`,
    zIndex: resolveSelectionChromeOverlayZIndex({
      isPrimarySelection,
      modelZIndex: chromeBlock.style?.zIndex,
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
        block={chromeBlock}
        designShortSidePx={Math.min(frameW, frameH)}
        designWidthPx={frameW}
        designHeightPx={frameH}
        handleSizePx={metrics.handleSize}
        adjustSizePx={metrics.adjustSize}
        rotateStemPx={metrics.rotateStem}
        allowResize={chromeBlock.type === "shape" ? shapeBlockAllowsResize(chromeBlock) : true}
        onPointerDown={onPointerDown}
        onResizeHandleDoubleClick={
          isEfficiencyPinBlock(chromeBlock) ? undefined : onResizeHandleDoubleClick
        }
      />
    </div>
  );
}
