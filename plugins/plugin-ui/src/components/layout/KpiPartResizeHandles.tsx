import type { CSSProperties, PointerEvent as ReactPointerEvent } from "react";

import {
  KPI_PART_RESIZE_HANDLES,
  type KpiPartResizeHandle,
} from "./kpiCardParts";

const HANDLE_LABELS: Record<KpiPartResizeHandle, string> = {
  nw: "Redimensionar canto superior esquerdo",
  n: "Redimensionar borda superior",
  ne: "Redimensionar canto superior direito",
  e: "Redimensionar borda direita",
  se: "Redimensionar canto inferior direito",
  s: "Redimensionar borda inferior",
  sw: "Redimensionar canto inferior esquerdo",
  w: "Redimensionar borda esquerda",
};

export type KpiPartResizeHandlesProps = {
  visible: boolean;
  onResizePointerDown: (handle: KpiPartResizeHandle, event: ReactPointerEvent) => void;
  /** Handle amarelo de raio (paridade com chrome do bloco). */
  showCornerAdjust?: boolean;
  /** left/top % — acompanha o raio (mesmo track do bloco). */
  cornerAdjustStyle?: CSSProperties;
  onCornerAdjustPointerDown?: (event: ReactPointerEvent) => void;
};

/**
 * Handles de resize (+ raio) — mesmas classes do chrome de bloco (`td-composer__*`)
 * para paridade visual pai/filho (complexo ≡ agrupado).
 */
export function KpiPartResizeHandles({
  visible,
  onResizePointerDown,
  showCornerAdjust = false,
  cornerAdjustStyle,
  onCornerAdjustPointerDown,
}: KpiPartResizeHandlesProps) {
  if (!visible) return null;

  return (
    <div className="td-composer__block-handles delpi-kpi-part-handles" data-kpi-part-chrome="">
      {KPI_PART_RESIZE_HANDLES.map((handle) => (
        <button
          key={handle}
          type="button"
          className={`td-composer__resize td-composer__resize--${handle} delpi-kpi-part-resize delpi-kpi-part-resize--${handle}`}
          aria-label={HANDLE_LABELS[handle]}
          onPointerDown={(event) => {
            event.stopPropagation();
            event.preventDefault();
            onResizePointerDown(handle, event);
          }}
        />
      ))}
      {showCornerAdjust && onCornerAdjustPointerDown ? (
        <button
          type="button"
          className="td-composer__adjust delpi-kpi-part-adjust"
          style={cornerAdjustStyle}
          aria-label="Ajustar raio dos cantos"
          title="Raio"
          onPointerDown={(event) => {
            event.stopPropagation();
            event.preventDefault();
            onCornerAdjustPointerDown(event);
          }}
        />
      ) : null}
    </div>
  );
}
