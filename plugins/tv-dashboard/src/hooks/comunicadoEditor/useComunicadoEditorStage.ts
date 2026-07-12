import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import { computeFitStageZoom } from "../../utils/stageViewport";

/**
 * Estado de UI do palco (zoom, réguas, grade, guias, snap) + fit à viewport.
 * O ref do canvas de interação é ligado depois via `bindCanvasRef`.
 */
export function useComunicadoEditorStage() {
  const [stageZoom, setStageZoom] = useState(1);
  const [showStageRulers, setShowStageRulers] = useState(true);
  const [showStageGrid, setShowStageGrid] = useState(false);
  const [showStageGuides, setShowStageGuides] = useState(true);
  const canvasWrapRef = useRef<HTMLDivElement | null>(null);
  const [snapEnabled, setSnapEnabled] = useState(true);
  const snapEnabledRef = useRef(true);
  const interactionCanvasRefSlot = useRef<RefObject<HTMLElement | null> | null>(null);

  useEffect(() => {
    snapEnabledRef.current = snapEnabled;
  }, [snapEnabled]);

  const bindCanvasRef = useCallback((ref: RefObject<HTMLElement | null>) => {
    interactionCanvasRefSlot.current = ref;
  }, []);

  const fitStageToView = useCallback(() => {
    const wrap = canvasWrapRef.current;
    const canvas = interactionCanvasRefSlot.current?.current ?? null;
    if (!wrap || !canvas) return;
    setStageZoom(computeFitStageZoom(wrap, canvas));
  }, []);

  return {
    stageZoom,
    setStageZoom,
    showStageRulers,
    setShowStageRulers,
    showStageGrid,
    setShowStageGrid,
    showStageGuides,
    setShowStageGuides,
    snapEnabled,
    setSnapEnabled,
    snapEnabledRef,
    canvasWrapRef,
    fitStageToView,
    bindCanvasRef,
  };
}
