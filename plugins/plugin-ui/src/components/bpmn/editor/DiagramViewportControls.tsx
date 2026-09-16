import { Maximize2, Minus, Plus } from "lucide-react";
import type { ReactNode } from "react";

import { NativeRangeControl } from "../../forms/NativeRangeControl";
import { HintAction } from "../../help/HintAction";
import { DIAGRAM_ZOOM_MAX, DIAGRAM_ZOOM_MIN } from "../layout/diagramViewport";

export type DiagramViewportControlLabels = {
  zoomLabel: string;
  zoomIn: string;
  zoomOut: string;
  zoomInHint: string;
  zoomOutHint: string;
  zoomFit: string;
  zoomFitHint: string;
  zoomReset: string;
  zoomResetHint: string;
};

type Props = {
  labels: DiagramViewportControlLabels;
  zoom: number;
  onZoomChange: (nextZoom: number) => void;
  onFit: () => void;
  onReset: () => void;
  className?: string;
  extra?: ReactNode;
};

export function DiagramViewportControls({
  labels,
  zoom,
  onZoomChange,
  onFit,
  onReset,
  className,
  extra,
}: Props) {
  const zoomPercent = Math.round(zoom * 100);
  const classes = ["delpi-ui-bpmn-editor__statusbar-zoom", className].filter(Boolean).join(" ");

  return (
    <div className={classes} role="group" aria-label={labels.zoomLabel}>
      <HintAction hint={labels.zoomOutHint} ariaLabel={labels.zoomOut}>
        <button
          type="button"
          className="delpi-ui-bpmn-editor__statusbar-btn"
          onClick={() => onZoomChange(zoom - 0.1)}
          aria-label={labels.zoomOut}
        >
          <Minus size={14} aria-hidden="true" />
        </button>
      </HintAction>
      <NativeRangeControl
        className="delpi-ui-bpmn-editor__statusbar-slider"
        min={Math.round(DIAGRAM_ZOOM_MIN * 100)}
        max={Math.round(DIAGRAM_ZOOM_MAX * 100)}
        step={5}
        value={zoomPercent}
        onChange={(value) => onZoomChange(value / 100)}
        aria-label={labels.zoomLabel}
      />
      <HintAction hint={labels.zoomInHint} ariaLabel={labels.zoomIn}>
        <button
          type="button"
          className="delpi-ui-bpmn-editor__statusbar-btn"
          onClick={() => onZoomChange(zoom + 0.1)}
          aria-label={labels.zoomIn}
        >
          <Plus size={14} aria-hidden="true" />
        </button>
      </HintAction>
      <span className="delpi-ui-bpmn-editor__statusbar-percent" aria-live="polite">
        {zoomPercent}%
      </span>
      <HintAction hint={labels.zoomFitHint} ariaLabel={labels.zoomFit}>
        <button
          type="button"
          className="delpi-ui-bpmn-editor__statusbar-btn delpi-ui-bpmn-editor__statusbar-btn--fit"
          onClick={onFit}
        >
          <Maximize2 size={14} aria-hidden="true" />
          <span>{labels.zoomFit}</span>
        </button>
      </HintAction>
      <HintAction hint={labels.zoomResetHint} ariaLabel={labels.zoomReset}>
        <button
          type="button"
          className="delpi-ui-bpmn-editor__statusbar-btn delpi-ui-bpmn-editor__statusbar-btn--reset"
          onClick={onReset}
        >
          <span>{labels.zoomReset}</span>
        </button>
      </HintAction>
      {extra}
    </div>
  );
}
