import type { PointerEvent as ReactPointerEvent } from "react";

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
};

/** Handles de resize no bbox da parte KPI (paridade com chart_view). */
export function KpiPartResizeHandles({ visible, onResizePointerDown }: KpiPartResizeHandlesProps) {
  if (!visible) return null;

  return (
    <>
      {KPI_PART_RESIZE_HANDLES.map((handle) => (
        <button
          key={handle}
          type="button"
          className={`delpi-kpi-part-resize delpi-kpi-part-resize--${handle}`}
          aria-label={HANDLE_LABELS[handle]}
          onPointerDown={(event) => {
            event.stopPropagation();
            event.preventDefault();
            onResizePointerDown(handle, event);
          }}
        />
      ))}
    </>
  );
}
