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
    event: ReactPointerEvent<HTMLElement>,
    block: ComunicadoBlock,
    mode: Extract<BlockDragMode, "move">,
  ) => void;
};

/**
 * Anel de hit alinhado ao outline global (`outline-offset`).
 * Usa `div` (não `button`) — o portal estiliza `button:hover` com fundo/borda
 * e essa regra vence o reset local (borda preta no hover).
 */
export function SelectionMoveHitFrame({ block, onMovePointerDown }: Props) {
  return (
    <div className="td-composer__selection-move-hit" aria-hidden="true">
      {SELECTION_MOVE_EDGES.map(({ position, label }) => (
        <div
          key={position}
          role="presentation"
          className={`td-composer__selection-move-edge td-composer__selection-move-edge--${position}`}
          aria-label={label}
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
