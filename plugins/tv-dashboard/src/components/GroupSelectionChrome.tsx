import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "./useCanvasBlockInteraction";
import { SelectionMoveHitFrame } from "./SelectionMoveHitFrame";

const GROUP_RESIZE_HANDLES: Array<{
  mode: Exclude<BlockDragMode, "move" | "rotate" | `adjust-${number}`>;
  position: string;
  label: string;
}> = [
  { mode: "resize-nw", position: "nw", label: "Redimensionar grupo (canto superior esquerdo)" },
  { mode: "resize-n", position: "n", label: "Redimensionar grupo (borda superior)" },
  { mode: "resize-ne", position: "ne", label: "Redimensionar grupo (canto superior direito)" },
  { mode: "resize-w", position: "w", label: "Redimensionar grupo (borda esquerda)" },
  { mode: "resize-e", position: "e", label: "Redimensionar grupo (borda direita)" },
  { mode: "resize-sw", position: "sw", label: "Redimensionar grupo (canto inferior esquerdo)" },
  { mode: "resize-s", position: "s", label: "Redimensionar grupo (borda inferior)" },
  { mode: "resize-se", position: "se", label: "Redimensionar grupo (canto inferior direito)" },
];

type Props = {
  frame: ComunicadoFrame;
  /** Bloco âncora para startDrag (primário do grupo). */
  anchorBlock: ComunicadoBlock;
  onPointerDown: (
    event: ReactPointerEvent<HTMLElement>,
    block: ComunicadoBlock,
    mode: BlockDragMode,
  ) => void;
};

/**
 * Chrome de seleção pai do grupo — um bbox unificado (como moldura de KPI),
 * em vez de outline/handles em cada membro.
 */
export function GroupSelectionChrome({ frame, anchorBlock, onPointerDown }: Props) {
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
      aria-label="Seleção do grupo"
    >
      <div className="td-composer__block-handles">
        <SelectionMoveHitFrame
          block={hitBlock}
          onMovePointerDown={(event) => onPointerDown(event, anchorBlock, "move")}
        />
      </div>
    </div>
  );
}
