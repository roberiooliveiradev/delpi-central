import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import {
  readStageDisplayPreferences,
  writeStageDisplayPreferences,
  type StageDisplayPreferences,
} from "../../utils/stageDisplayPreferences";
import { applyCenteredStageScroll } from "../../utils/stagePan";
import { computeFitStageZoom, clampStageZoom } from "../../utils/stageViewport";

/**
 * Estado de UI do palco (zoom, réguas, grade, guias, snap) + fit à viewport.
 * Preferências persistem em localStorage (sobrevivem ao refresh).
 * O ref do canvas de interação é ligado depois via `bindCanvasRef`.
 */
export function useComunicadoEditorStage() {
  const [prefs, setPrefs] = useState<StageDisplayPreferences>(() => readStageDisplayPreferences());
  /** Ferramenta pan (mão) — sessão; não persiste em localStorage. */
  const [stagePanMode, setStagePanModeState] = useState(false);
  const canvasWrapRef = useRef<HTMLDivElement | null>(null);
  const snapEnabledRef = useRef(prefs.snapEnabled);
  const stageGridSizePxRef = useRef(prefs.stageGridSizePx);
  const interactionCanvasRefSlot = useRef<RefObject<HTMLElement | null> | null>(null);
  const prefsRef = useRef(prefs);
  prefsRef.current = prefs;

  useEffect(() => {
    snapEnabledRef.current = prefs.snapEnabled;
  }, [prefs.snapEnabled]);

  useEffect(() => {
    stageGridSizePxRef.current = prefs.stageGridSizePx;
  }, [prefs.stageGridSizePx]);

  useEffect(() => {
    writeStageDisplayPreferences(prefs);
  }, [prefs]);

  const patchPrefs = useCallback((patch: Partial<StageDisplayPreferences>) => {
    setPrefs((current) => ({ ...current, ...patch }));
  }, []);

  const bindCanvasRef = useCallback((ref: RefObject<HTMLElement | null>) => {
    interactionCanvasRefSlot.current = ref;
  }, []);

  const fitStageToView = useCallback(() => {
    const wrap = canvasWrapRef.current;
    const canvas = interactionCanvasRefSlot.current?.current ?? null;
    if (!wrap || !canvas) return;
    patchPrefs({ stageZoom: computeFitStageZoom(wrap, canvas) });
    window.requestAnimationFrame(() => {
      applyCenteredStageScroll(wrap);
    });
  }, [patchPrefs]);

  return {
    stageZoom: prefs.stageZoom,
    setStageZoom: (zoom: number | ((prev: number) => number)) => {
      const next = typeof zoom === "function" ? zoom(prefsRef.current.stageZoom) : zoom;
      patchPrefs({ stageZoom: clampStageZoom(next) });
    },
    showStageRulers: prefs.showStageRulers,
    setShowStageRulers: (value: boolean | ((prev: boolean) => boolean)) => {
      const next = typeof value === "function" ? value(prefsRef.current.showStageRulers) : value;
      patchPrefs({ showStageRulers: next });
    },
    showStageGrid: prefs.showStageGrid,
    setShowStageGrid: (value: boolean | ((prev: boolean) => boolean)) => {
      const next = typeof value === "function" ? value(prefsRef.current.showStageGrid) : value;
      patchPrefs({ showStageGrid: next });
    },
    stageGridSizePx: prefs.stageGridSizePx,
    setStageGridSizePx: (value: number | ((prev: number) => number)) => {
      const raw = typeof value === "function" ? value(prefsRef.current.stageGridSizePx) : value;
      patchPrefs({ stageGridSizePx: raw });
    },
    stageGridSizePxRef,
    showStageGuides: prefs.showStageGuides,
    setShowStageGuides: (value: boolean | ((prev: boolean) => boolean)) => {
      const next = typeof value === "function" ? value(prefsRef.current.showStageGuides) : value;
      patchPrefs({ showStageGuides: next });
    },
    snapEnabled: prefs.snapEnabled,
    setSnapEnabled: (value: boolean | ((prev: boolean) => boolean)) => {
      const next = typeof value === "function" ? value(prefsRef.current.snapEnabled) : value;
      patchPrefs({ snapEnabled: next });
    },
    snapEnabledRef,
    canvasWrapRef,
    fitStageToView,
    bindCanvasRef,
    stagePanMode,
    setStagePanMode: (enabled: boolean) => {
      setStagePanModeState(enabled);
    },
  };
}
