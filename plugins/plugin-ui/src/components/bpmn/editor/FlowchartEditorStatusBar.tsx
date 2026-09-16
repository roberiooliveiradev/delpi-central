import { Grid3x3, Lock, LockOpen } from "lucide-react";
import { useCallback, useEffect, useState, type PointerEvent, type ReactNode } from "react";
import { useReactFlow, useStore } from "@xyflow/react";

import { HintAction } from "../../help/HintAction";
import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import { DIAGRAM_FIT_VIEW_OPTIONS, getDiagramFitNodes } from "../layout/diagramViewFit";
import { clampDiagramZoom } from "../layout/diagramViewport";
import type { DiagramEditorAction } from "./flowchartEditorToolbar";
import { DiagramViewportControls } from "./DiagramViewportControls";
import { FlowchartEditorActionDock } from "./FlowchartEditorActionDock";

type Props = {
  labels: FlowchartEditorLabels;
  showGrid: boolean;
  onShowGridChange: (next: boolean) => void;
  nodesInteractive?: boolean;
  onNodesInteractiveChange?: (next: boolean) => void;
  readOnly?: boolean;
  selectionActions?: DiagramEditorAction[];
  clipboardReady?: boolean;
  onSelectionAction?: (actionId: DiagramEditorAction["id"]) => void;
  isSelectionActionDisabled?: (actionId: DiagramEditorAction["id"]) => boolean;
  onSelectionPointerDownCapture?: (event: PointerEvent<HTMLDivElement>) => void;
  leadingExtra?: ReactNode;
  onViewportIntent?: (intent: "fit" | "user") => void;
};

/**
 * Barra inferior do canvas — grade, lock, ações de seleção e zoom
 * (paridade visual com `td-stage-statusbar` do TV Dashboard).
 */
export function FlowchartEditorStatusBar({
  labels,
  showGrid,
  onShowGridChange,
  nodesInteractive = true,
  onNodesInteractiveChange,
  readOnly = false,
  selectionActions,
  clipboardReady = false,
  onSelectionAction,
  isSelectionActionDisabled,
  onSelectionPointerDownCapture,
  leadingExtra,
  onViewportIntent,
}: Props) {
  const { fitView, getNodes, zoomTo, getViewport, setViewport } = useReactFlow();
  const storeZoom = useStore((state) => state.transform[2]);
  const [zoom, setZoom] = useState(storeZoom);

  useEffect(() => {
    setZoom(storeZoom);
  }, [storeZoom]);

  const applyZoom = useCallback(
    (nextZoom: number) => {
      const clamped = clampDiagramZoom(nextZoom);
      onViewportIntent?.("user");
      void zoomTo(clamped);
      setZoom(clamped);
    },
    [onViewportIntent, zoomTo]
  );

  const fitToContent = useCallback(() => {
    const fitNodes = getDiagramFitNodes(getNodes());
    if (!fitNodes.length) return;
    onViewportIntent?.("fit");
    void fitView({ ...DIAGRAM_FIT_VIEW_OPTIONS, nodes: fitNodes });
  }, [fitView, getNodes, onViewportIntent]);

  const resetZoom = useCallback(() => {
    const viewport = getViewport();
    onViewportIntent?.("user");
    void setViewport({ ...viewport, zoom: 1 });
    setZoom(1);
  }, [getViewport, onViewportIntent, setViewport]);

  const showSelection =
    !readOnly &&
    Boolean(selectionActions?.length) &&
    Boolean(onSelectionAction) &&
    Boolean(isSelectionActionDisabled);

  return (
    <div
      className="delpi-ui-bpmn-editor__statusbar"
      role="toolbar"
      aria-label={labels.statusBarAriaLabel}
    >
      <div className="delpi-ui-bpmn-editor__statusbar-leading">
        <div className="delpi-ui-bpmn-editor__statusbar-toggles">
          <HintAction hint={labels.gridToggleHint} ariaLabel={labels.gridToggle}>
            <button
              type="button"
              className={[
                "delpi-ui-bpmn-editor__statusbar-btn",
                showGrid ? "delpi-ui-bpmn-editor__statusbar-btn--active" : "",
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
          {!readOnly && onNodesInteractiveChange ? (
            <HintAction
              hint={labels.nodesInteractiveHint}
              ariaLabel={
                nodesInteractive ? labels.nodesInteractiveOn : labels.nodesInteractiveOff
              }
            >
              <button
                type="button"
                className={[
                  "delpi-ui-bpmn-editor__statusbar-btn",
                  nodesInteractive ? "delpi-ui-bpmn-editor__statusbar-btn--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                aria-pressed={nodesInteractive}
                onClick={() => onNodesInteractiveChange(!nodesInteractive)}
              >
                {nodesInteractive ? (
                  <LockOpen size={14} aria-hidden="true" />
                ) : (
                  <Lock size={14} aria-hidden="true" />
                )}
                <span>
                  {nodesInteractive ? labels.nodesInteractiveOn : labels.nodesInteractiveOff}
                </span>
              </button>
            </HintAction>
          ) : null}
          {leadingExtra}
        </div>

        {showSelection ? (
          <FlowchartEditorActionDock
            labels={labels}
            selectionActions={selectionActions!}
            clipboardReady={clipboardReady}
            onSelectionAction={onSelectionAction!}
            isSelectionActionDisabled={isSelectionActionDisabled!}
            onPointerDownCapture={onSelectionPointerDownCapture}
            variant="statusbar"
          />
        ) : null}
      </div>

      <DiagramViewportControls
        labels={labels}
        zoom={zoom}
        onZoomChange={applyZoom}
        onFit={fitToContent}
        onReset={resetZoom}
      />
    </div>
  );
}
