import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import {
  readStageDisplayPreferences,
  writeStageDisplayPreferences,
  type StageDisplayPreferences,
} from "../../utils/stageDisplayPreferences";
import {
  applyCenteredStageScroll,
  applyStageViewAnchor,
  captureStageViewAnchor,
} from "../../utils/stagePan";
import { computeFitStageZoom, clampStageZoom } from "../../utils/stageViewport";

/**
 * Estado de UI do palco (zoom, réguas, grade, guias, snap, posição) + fit à viewport.
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
  const persistViewTimerRef = useRef<number | null>(null);
  /** Evita gravar âncora enquanto restauramos/ajustamos programaticamente. */
  const suppressViewPersistRef = useRef(false);

  useEffect(() => {
    snapEnabledRef.current = prefs.snapEnabled;
  }, [prefs.snapEnabled]);

  useEffect(() => {
    stageGridSizePxRef.current = prefs.stageGridSizePx;
  }, [prefs.stageGridSizePx]);

  useEffect(() => {
    writeStageDisplayPreferences(prefs);
  }, [prefs]);

  useEffect(() => {
    return () => {
      if (persistViewTimerRef.current != null) {
        window.clearTimeout(persistViewTimerRef.current);
      }
    };
  }, []);

  const patchPrefs = useCallback((patch: Partial<StageDisplayPreferences>) => {
    setPrefs((current) => ({ ...current, ...patch }));
  }, []);

  const bindCanvasRef = useCallback((ref: RefObject<HTMLElement | null>) => {
    interactionCanvasRefSlot.current = ref;
  }, []);

  const persistStageViewPosition = useCallback(
    (options?: { immediate?: boolean }) => {
      if (suppressViewPersistRef.current) return;
      const wrap = canvasWrapRef.current;
      if (!wrap) return;

      const commit = () => {
        if (suppressViewPersistRef.current) return;
        const el = canvasWrapRef.current;
        if (!el) return;
        const anchor = captureStageViewAnchor(el);
        const current = prefsRef.current;
        if (
          current.stageViewAnchorSaved &&
          current.stageViewAnchorX === anchor.x &&
          current.stageViewAnchorY === anchor.y
        ) {
          return;
        }
        patchPrefs({
          stageViewAnchorX: anchor.x,
          stageViewAnchorY: anchor.y,
          stageViewAnchorSaved: true,
        });
      };

      if (options?.immediate) {
        if (persistViewTimerRef.current != null) {
          window.clearTimeout(persistViewTimerRef.current);
          persistViewTimerRef.current = null;
        }
        commit();
        return;
      }

      if (persistViewTimerRef.current != null) {
        window.clearTimeout(persistViewTimerRef.current);
      }
      persistViewTimerRef.current = window.setTimeout(() => {
        persistViewTimerRef.current = null;
        commit();
      }, 120);
    },
    [patchPrefs],
  );

  const restoreStageViewPosition = useCallback(() => {
    const wrap = canvasWrapRef.current;
    const current = prefsRef.current;
    if (!wrap || !current.stageViewAnchorSaved) return false;
    suppressViewPersistRef.current = true;
    applyStageViewAnchor(wrap, {
      x: current.stageViewAnchorX,
      y: current.stageViewAnchorY,
    });
    window.requestAnimationFrame(() => {
      suppressViewPersistRef.current = false;
    });
    return true;
  }, []);

  const fitStageToView = useCallback(() => {
    const wrap = canvasWrapRef.current;
    const canvas = interactionCanvasRefSlot.current?.current ?? null;
    if (!wrap || !canvas) return;
    suppressViewPersistRef.current = true;
    patchPrefs({ stageZoom: computeFitStageZoom(wrap, canvas) });
    window.requestAnimationFrame(() => {
      applyCenteredStageScroll(wrap);
      const anchor = captureStageViewAnchor(wrap);
      patchPrefs({
        stageViewAnchorX: anchor.x,
        stageViewAnchorY: anchor.y,
        stageViewAnchorSaved: true,
      });
      suppressViewPersistRef.current = false;
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
    stageViewAnchorSaved: prefs.stageViewAnchorSaved,
    canvasWrapRef,
    fitStageToView,
    restoreStageViewPosition,
    persistStageViewPosition,
    bindCanvasRef,
    stagePanMode,
    setStagePanMode: (enabled: boolean) => {
      setStagePanModeState(enabled);
    },
  };
}
