import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "./useCanvasBlockInteraction";
import { BLOCK_RESIZE_HANDLES } from "./BlockSelectionChrome";
import { SelectionMoveHitFrame } from "./SelectionMoveHitFrame";

type Props = {
  /** Frame do grupo em % do slide (hit / startFrame do drag). */
  frame: ComunicadoFrame;
  /**
   * Rotação do GroupTransform.
   * Com `fillParent`, o ângulo fica no `GroupTransformLayer` — não repetir aqui.
   */
  rotation?: number;
  /** Preenche o layer pai (inset 0); um só rotate no container. */
  fillParent?: boolean;
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
 * Chrome de seleção pai do grupo.
 * Preferir `fillParent` dentro de `GroupTransformLayer` (rotate único no container).
 */
export function GroupSelectionChrome({
  frame,
  rotation = 0,
  fillParent = false,
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
      style={
        fillParent
          ? {
              left: 0,
              top: 0,
              width: "100%",
              height: "100%",
            }
          : {
              left: `${frame.x}%`,
              top: `${frame.y}%`,
              width: `${frame.w}%`,
              height: `${frame.h}%`,
              transform: rotation ? `rotate(${rotation}deg)` : undefined,
              transformOrigin: "center center",
            }
      }
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
