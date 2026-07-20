import { Grid3x3, Maximize2, Minus, Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useReactFlow, useStore } from "@xyflow/react";

import { NativeRangeControl } from "../forms/NativeRangeControl";
import { HintAction } from "../help/HintAction";
import type { FlowchartEditorLabels } from "./types/flowchartEditorLabels";
import { DIAGRAM_FIT_VIEW_OPTIONS, getDiagramFitNodes } from "./utils/diagramViewFit";

const ZOOM_MIN = 0.08;
const ZOOM_MAX = 3;

type Props = {
  labels: FlowchartEditorLabels;
  showGrid: boolean;
  onShowGridChange: (next: boolean) => void;
};

function clampZoom(zoom: number): number {
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, zoom));
}

/** Barra inferior do canvas — grade + zoom (inspirada no status bar do TV Dashboard). */
export function FlowchartEditorStatusBar({ labels, showGrid, onShowGridChange }: Props) {
  const { fitView, getNodes, setViewport, getViewport } = useReactFlow();
  const storeZoom = useStore((state) => state.transform[2]);
  const [zoom, setZoom] = useState(storeZoom);

  useEffect(() => {
    setZoom(storeZoom);
  }, [storeZoom]);

  const zoomPercent = Math.round(zoom * 100);

  const applyZoom = useCallback(
    (nextZoom: number) => {
      const clamped = clampZoom(nextZoom);
      const viewport = getViewport();
      void setViewport({ ...viewport, zoom: clamped });
      setZoom(clamped);
    },
    [getViewport, setViewport],
  );

  const fitToContent = useCallback(() => {
    const fitNodes = getDiagramFitNodes(getNodes());
    if (!fitNodes.length) return;
    void fitView({ ...DIAGRAM_FIT_VIEW_OPTIONS, nodes: fitNodes });
  }, [fitView, getNodes]);

  return (
    <div className="tm-diagram-editor__statusbar" role="toolbar" aria-label={labels.statusBarAriaLabel}>
      <div className="tm-diagram-editor__statusbar-toggles">
        <HintAction hint={labels.gridToggleHint} ariaLabel={labels.gridToggle}>
          <button
            type="button"
            className={[
              "tm-diagram-editor__statusbar-btn",
              showGrid ? "tm-diagram-editor__statusbar-btn--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-pressed={showGrid}
            onClick={() => onShowGridChange(!showGrid)}
          >
            <Grid3x3 size={14} aria-hidden="true" />
            <span>{labels.gridToggle}</span>
          </button>
        </HintAction>
      </div>

      <div className="tm-diagram-editor__statusbar-zoom">
        <HintAction hint={labels.zoomOutHint} ariaLabel={labels.zoomOut}>
          <button
            type="button"
            className="tm-diagram-editor__statusbar-btn"
            onClick={() => applyZoom(zoom - 0.1)}
            aria-label={labels.zoomOut}
          >
            <Minus size={14} aria-hidden="true" />
          </button>
        </HintAction>
        <NativeRangeControl
          className="tm-diagram-editor__statusbar-slider"
          min={Math.round(ZOOM_MIN * 100)}
          max={Math.round(ZOOM_MAX * 100)}
          step={5}
          value={zoomPercent}
          onChange={(value) => applyZoom(value / 100)}
          aria-label={labels.zoomLabel}
        />
        <HintAction hint={labels.zoomInHint} ariaLabel={labels.zoomIn}>
          <button
            type="button"
            className="tm-diagram-editor__statusbar-btn"
            onClick={() => applyZoom(zoom + 0.1)}
            aria-label={labels.zoomIn}
          >
            <Plus size={14} aria-hidden="true" />
          </button>
        </HintAction>
        <span className="tm-diagram-editor__statusbar-percent" aria-live="polite">
          {zoomPercent}%
        </span>
        <HintAction hint={labels.zoomFitHint} ariaLabel={labels.zoomFit}>
          <button
            type="button"
            className="tm-diagram-editor__statusbar-btn tm-diagram-editor__statusbar-btn--fit"
            onClick={fitToContent}
          >
            <Maximize2 size={14} aria-hidden="true" />
            <span>{labels.zoomFit}</span>
          </button>
        </HintAction>
      </div>
    </div>
  );
}
