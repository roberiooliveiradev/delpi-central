import type { PointerEvent as ReactPointerEvent } from "react";
import {
  adjustmentHandleCssPosition,
  blockShapeChromeAdjustmentSpecs,
  blockSupportsShapeChromeHandles,
  geometryBoundingFrame,
  isLineShapeKind,
  resolveBlockShapeChromeAdjustmentValues,
  resolveLineEndpoints,
  resolveShapeGeometry,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "./useCanvasBlockInteraction";
import { SelectionMoveHitFrame } from "./SelectionMoveHitFrame";

export const BLOCK_RESIZE_HANDLES: Array<{
  mode: Exclude<BlockDragMode, "move" | "rotate" | `adjust-${number}` | `endpoint-${0 | 1}`>;
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

function lineEndpointLocalPercent(
  block: Extract<ComunicadoBlock, { type: "shape" }>,
  endpointIndex: 0 | 1,
): { left: string; top: string } {
  const [a, b] = resolveLineEndpoints(block);
  const point = endpointIndex === 0 ? a : b;
  const bbox = geometryBoundingFrame(resolveShapeGeometry(block));
  const left = bbox.w > 0 ? ((point.x - bbox.x) / bbox.w) * 100 : 50;
  const top = bbox.h > 0 ? ((point.y - bbox.y) / bbox.h) * 100 : 50;
  return { left: `${left}%`, top: `${top}%` };
}

/**
 * Chrome de seleção único do palco (caixa visual texto/forma, ícone, views…):
 * anel de move, resize, giro, endpoints de linha e losango de ajuste quando suportado.
 */
export function BlockSelectionChrome({
  block,
  designShortSidePx,
  allowResize,
  onPointerDown,
}: Props) {
  /* KPI incluso — `comunicadoBlockShapeChrome` já resolve cantos da parte `card`. */
  const showAdjust = blockSupportsShapeChromeHandles(block);
  const isLine = block.type === "shape" && isLineShapeKind(block.shape);

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
      {isLine && block.type === "shape"
        ? ([0, 1] as const).map((endpointIndex) => {
            const pos = lineEndpointLocalPercent(block, endpointIndex);
            return (
              <button
                key={`endpoint-${endpointIndex}`}
                type="button"
                className={`td-composer__endpoint td-composer__endpoint--${endpointIndex === 0 ? "start" : "end"}`}
                style={{ left: pos.left, top: pos.top }}
                aria-label={
                  endpointIndex === 0 ? "Mover início da linha" : "Mover fim da linha"
                }
                title={endpointIndex === 0 ? "Início" : "Fim"}
                onPointerDown={(event) =>
                  onPointerDown(event, block, `endpoint-${endpointIndex}`)
                }
              />
            );
          })
        : null}
      {!isLine && allowResize
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
