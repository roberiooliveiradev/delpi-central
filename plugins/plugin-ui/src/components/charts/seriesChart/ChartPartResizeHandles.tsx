import type { PointerEvent as ReactPointerEvent } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  CHART_PART_RESIZE_HANDLES,
  type ChartPartResizeHandle,
} from "../seriesChartParts";

const HANDLE_LABELS: Record<ChartPartResizeHandle, string> = {
  nw: "Redimensionar canto superior esquerdo",
  n: "Redimensionar borda superior",
  ne: "Redimensionar canto superior direito",
  e: "Redimensionar borda direita",
  se: "Redimensionar canto inferior direito",
  s: "Redimensionar borda inferior",
  sw: "Redimensionar canto inferior esquerdo",
  w: "Redimensionar borda esquerda",
};

export type ChartPartResizeHandlesProps = {
  visible: boolean;
  onResizePointerDown: (handle: ChartPartResizeHandle, event: ReactPointerEvent) => void;
};

/** Handles de resize no bbox da parte (paridade com o grupo chart_view). */
export function ChartPartResizeHandles({ visible, onResizePointerDown }: ChartPartResizeHandlesProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  return (
    <>
      {CHART_PART_RESIZE_HANDLES.map((handle) => (
        <button
          key={handle}
          type="button"
          className={`${cn.root}__part-resize ${cn.root}__part-resize--${handle}`}
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
