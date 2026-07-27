import type { PointerEvent as ReactPointerEvent, CSSProperties } from "react";
import {
  shapeBlockAllowsResize,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { buildBlockTransformCss } from "../utils/comunicadoTransform";
import { resolveSelectionChromeOverlayZIndex } from "../utils/resolveBlockWrapStackZIndex";
import { BlockSelectionChrome } from "./BlockSelectionChrome";
import type { BlockDragMode } from "./useCanvasBlockInteraction";

type Props = {
  block: ComunicadoBlock;
  designWidth: number;
  designHeight: number;
  isPrimarySelection: boolean;
  onPointerDown: (
    event: ReactPointerEvent<HTMLElement>,
    block: ComunicadoBlock,
    mode: BlockDragMode,
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
  isPrimarySelection,
  onPointerDown,
}: Props) {
  const wrapTransform = buildBlockTransformCss(block.style);
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
        designShortSidePx={Math.min(
          (block.frame.w / 100) * designWidth,
          (block.frame.h / 100) * designHeight,
        )}
        allowResize={block.type === "shape" ? shapeBlockAllowsResize(block) : true}
        onPointerDown={onPointerDown}
      />
    </div>
  );
}
