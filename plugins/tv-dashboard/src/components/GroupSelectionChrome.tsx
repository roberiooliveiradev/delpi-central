import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "./useCanvasBlockInteraction";
import { BLOCK_RESIZE_HANDLES } from "./BlockSelectionChrome";
import { SelectionMoveHitFrame } from "./SelectionMoveHitFrame";

type Props = {
  frame: ComunicadoFrame;
  /** Bloco âncora para startDrag (primário do grupo). */
  anchorBlock: ComunicadoBlock;
  allowResize?: boolean;
  onPointerDown: (
    event: ReactPointerEvent<HTMLElement>,
    block: ComunicadoBlock,
    mode: BlockDragMode,
  ) => void;
};

/**
 * Chrome de seleção pai do grupo — bbox unificado com move + resize + giro
 * (paridade com bloco individual / moldura de KPI).
 */
export function GroupSelectionChrome({
  frame,
  anchorBlock,
  allowResize = true,
  onPointerDown,
}: Props) {
  /** Frame do grupo — centro do giro e bbox dos handles. */
  const hitBlock: ComunicadoBlock = {
    ...anchorBlock,
    frame,
  };

  return (
    <div
      className="td-composer__group-chrome"
      style={{
        left: `${frame.x}%`,
        top: `${frame.y}%`,
        width: `${frame.w}%`,
        height: `${frame.h}%`,
      }}
      data-group-chrome=""
      data-block-id={anchorBlock.id}
      aria-label="Seleção do grupo"
    >
      <div className="td-composer__block-handles">
        <SelectionMoveHitFrame
          block={hitBlock}
          onMovePointerDown={(event) => onPointerDown(event, anchorBlock, "move")}
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
                onPointerDown={(event) => onPointerDown(event, anchorBlock, mode)}
              />
            ))
          : null}
      </div>
    </div>
  );
}
