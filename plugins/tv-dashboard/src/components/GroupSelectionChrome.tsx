import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "./useCanvasBlockInteraction";
import { BLOCK_RESIZE_HANDLES } from "./BlockSelectionChrome";
import { SelectionMoveHitFrame } from "./SelectionMoveHitFrame";

type Props = {
  frame: ComunicadoFrame;
  /** Rotação do GroupTransform (CSS no overlay = mesmo ângulo dos membros bakeados). */
  rotation?: number;
  /** Bloco âncora (id) — frame/style do hit espelham o chrome do grupo. */
  anchorBlock: ComunicadoBlock;
  allowResize?: boolean;
  onPointerDown: (
    event: ReactPointerEvent<HTMLElement>,
    block: ComunicadoBlock,
    mode: BlockDragMode,
  ) => void;
};

/**
 * Chrome de seleção pai do grupo — GroupTransform (frame + rotation).
 * Mesmo contrato visual do bloco individual: layout box + CSS rotate.
 */
export function GroupSelectionChrome({
  frame,
  rotation = 0,
  anchorBlock,
  allowResize = true,
  onPointerDown,
}: Props) {
  /** Hit usa frame/rotação do grupo; id do âncora para multi-drag. */
  const hitBlock: ComunicadoBlock = {
    ...anchorBlock,
    frame,
    style: { ...anchorBlock.style, rotation },
  };

  return (
    <div
      className="td-composer__group-chrome"
      style={{
        left: `${frame.x}%`,
        top: `${frame.y}%`,
        width: `${frame.w}%`,
        height: `${frame.h}%`,
        transform: rotation ? `rotate(${rotation}deg)` : undefined,
        transformOrigin: "center center",
      }}
      data-group-chrome=""
      data-block-id={anchorBlock.id}
      aria-label="Seleção do grupo"
    >
      <div className="td-composer__block-handles">
        <SelectionMoveHitFrame
          block={hitBlock}
          onMovePointerDown={(event) => onPointerDown(event, hitBlock, "move")}
        />
        <button
          type="button"
          className="td-composer__rotate"
          aria-label="Girar grupo"
          onPointerDown={(event) => onPointerDown(event, hitBlock, "rotate")}
        />
        {allowResize
          ? BLOCK_RESIZE_HANDLES.map(({ mode, position, label }) => (
              <button
                key={mode}
                type="button"
                className={`td-composer__resize td-composer__resize--${position}`}
                aria-label={label}
                onPointerDown={(event) => onPointerDown(event, hitBlock, mode)}
              />
            ))
          : null}
      </div>
    </div>
  );
}
