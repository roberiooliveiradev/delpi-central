import type { PointerEvent as ReactPointerEvent } from "react";

import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "./useCanvasBlockInteraction";

const SELECTION_MOVE_EDGES = [
  { position: "n", label: "Mover pela borda superior" },
  { position: "e", label: "Mover pela borda direita" },
  { position: "s", label: "Mover pela borda inferior" },
  { position: "w", label: "Mover pela borda esquerda" },
] as const;

type Props = {
  block: ComunicadoBlock;
  onMovePointerDown: (
    event: ReactPointerEvent<HTMLButtonElement>,
    block: ComunicadoBlock,
    mode: Extract<BlockDragMode, "move">,
  ) => void;
};

/**
 * Anel de hit alinhado ao outline global (`outline-offset`).
 * CSS `outline` não recebe pointer events — sem isto, a linha pontilhada
 * não inicia arraste (só os pickers de resize, que são DOM real).
 */
export function SelectionMoveHitFrame({ block, onMovePointerDown }: Props) {
  return (
    <div className="td-composer__selection-move-hit" aria-hidden="true">
      {SELECTION_MOVE_EDGES.map(({ position, label }) => (
        <button
          key={position}
          type="button"
          className={`td-composer__selection-move-edge td-composer__selection-move-edge--${position}`}
          aria-label={label}
          tabIndex={-1}
          onPointerDown={(event) => {
            event.preventDefault();
            event.stopPropagation();
            onMovePointerDown(event, block, "move");
          }}
        />
      ))}
    </div>
  );
}
