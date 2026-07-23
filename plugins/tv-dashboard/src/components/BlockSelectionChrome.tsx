import type { PointerEvent as ReactPointerEvent } from "react";
import {
  adjustmentHandleCssPosition,
  blockShapeChromeAdjustmentSpecs,
  blockSupportsShapeChromeHandles,
  resolveBlockShapeChromeAdjustmentValues,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "./useCanvasBlockInteraction";
import { SelectionMoveHitFrame } from "./SelectionMoveHitFrame";

export const BLOCK_RESIZE_HANDLES: Array<{
  mode: Exclude<BlockDragMode, "move" | `adjust-${number}`>;
  position: string;
  label: string;
}> = [
  { mode: "resize-nw", position: "nw", label: "Redimensionar canto superior esquerdo" },
  { mode: "resize-n", position: "n", label: "Redimensionar borda superior" },
  { mode: "resize-ne", position: "ne", label: "Redimensionar canto superior direito" },
  { mode: "resize-w", position: "w", label: "Redimensionar borda esquerda" },
  { mode: "resize-e", position: "e", label: "Redimensionar borda direita" },
  { mode: "resize-sw", position: "sw", label: "Redimensionar canto inferior esquerdo" },
  { mode: "resize-s", position: "s", label: "Redimensionar borda inferior" },
  { mode: "resize-se", position: "se", label: "Redimensionar canto inferior direito" },
];

type Props = {
  block: ComunicadoBlock;
  /** Lado curto do frame em px de design (handles de ajuste). */
  designShortSidePx: number;
  allowResize: boolean;
  onPointerDown: (
    event: ReactPointerEvent<HTMLElement>,
    block: ComunicadoBlock,
    mode: BlockDragMode,
  ) => void;
};

/**
 * Chrome de seleção único do palco (caixa visual texto/forma, ícone, views…):
 * anel de move, resize, giro e losango de ajuste quando suportado.
 */
export function BlockSelectionChrome({
  block,
  designShortSidePx,
  allowResize,
  onPointerDown,
}: Props) {
  /* KPI incluso — `comunicadoBlockShapeChrome` já resolve cantos da parte `card`. */
  const showAdjust = blockSupportsShapeChromeHandles(block);

  return (
    <div className="td-composer__block-handles">
      <SelectionMoveHitFrame
        block={block}
        onMovePointerDown={(event) => onPointerDown(event, block, "move")}
      />
      <button
        type="button"
        className="td-composer__rotate"
        aria-label="Girar elemento"
        onPointerDown={(event) => onPointerDown(event, block, "rotate")}
      />
      {allowResize
        ? BLOCK_RESIZE_HANDLES.map(({ mode, position, label }) => (
            <button
              key={mode}
              type="button"
              className={`td-composer__resize td-composer__resize--${position}`}
              aria-label={label}
              onPointerDown={(event) => onPointerDown(event, block, mode)}
            />
          ))
        : null}
      {showAdjust
        ? blockShapeChromeAdjustmentSpecs(block).map((spec) => {
            const values = resolveBlockShapeChromeAdjustmentValues(block, designShortSidePx);
            const pos = adjustmentHandleCssPosition(spec, values);
            return (
              <button
                key={`adj-${spec.index}`}
                type="button"
                className="td-composer__adjust"
                style={{ left: pos.left, top: pos.top }}
                aria-label={`Ajustar ${spec.label}`}
                title={spec.label}
                onPointerDown={(event) =>
                  onPointerDown(event, block, `adjust-${spec.index}`)
                }
              />
            );
          })
        : null}
    </div>
  );
}
