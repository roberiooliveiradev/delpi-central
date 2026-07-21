import { useCallback, useEffect, useLayoutEffect, useRef, useState, type RefObject } from "react";

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

const STAGE_VIEW_FIT_MAX_ATTEMPTS = 60;
/** Passes de recentralização após o zoom pintar (scrollWidth precisa do layout novo). */
const STAGE_VIEW_FIT_CENTER_PASSES = 3;

/**
 * Estado de UI do palco (zoom, réguas, grade, guias, snap, posição) + fit à viewport.
 * Preferências persistem em localStorage (sobrevivem ao refresh).
 * O ref do canvas de interação é ligado depois via `bindCanvasRef`.
 *
 * Sem âncora / ao montar: bootstrap = sempre Ajustar (fit).
 * Com âncora: resize do wrap preserva o ponto sob o centro (não no load).
 */
export function useComunicadoEditorStage() {
  const [prefs, setPrefs] = useState<StageDisplayPreferences>(() => readStageDisplayPreferences());
  /** Ferramenta pan (mão) — sessão; não persiste em localStorage. */
  const [stagePanMode, setStagePanModeState] = useState(false);
  /** false durante bootstrap — Composer não deve compensar gutter sobre o restore. */
  const [stageViewReady, setStageViewReady] = useState(false);
  const canvasWrapRef = useRef<HTMLDivElement | null>(null);
  const snapToGridRef = useRef(prefs.snapToGrid);
  const snapToObjectsRef = useRef(prefs.snapToObjects);
  const showStageGuidesRef = useRef(prefs.showStageGuides);
  const stageGridSizePercentRef = useRef(prefs.stageGridSizePercent);
  const interactionCanvasRefSlot = useRef<RefObject<HTMLElement | null> | null>(null);
  const prefsRef = useRef(prefs);
  prefsRef.current = prefs;
  const persistViewTimerRef = useRef<number | null>(null);
  /**
   * Bloqueia persist até restore/fit do bootstrap — evita gravar 0,0 no gutter
   * antes do canvas existir.
   */
  const suppressViewPersistRef = useRef(true);
  const viewBootstrappedRef = useRef(false);
  /** Geração do fit em curso — invalida centers atrasados de um fit anterior. */
  const fitGenerationRef = useRef(0);
  /** Após patch de zoom, centraliza no layout effect (DOM já com o novo scale). */
  const pendingFitCenterRef = useRef(false);

  useEffect(() => {
    snapToGridRef.current = prefs.snapToGrid;
  }, [prefs.snapToGrid]);

  useEffect(() => {
    snapToObjectsRef.current = prefs.snapToObjects;
  }, [prefs.snapToObjects]);

  useEffect(() => {
    showStageGuidesRef.current = prefs.showStageGuides;
  }, [prefs.showStageGuides]);

  useEffect(() => {
    stageGridSizePercentRef.current = prefs.stageGridSizePercent;
  }, [prefs.stageGridSizePercent]);

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

  const markViewBootstrapped = useCallback(() => {
    viewBootstrappedRef.current = true;
    suppressViewPersistRef.current = false;
    setStageViewReady(true);
  }, []);

  const persistStageViewPosition = useCallback(
    (options?: { immediate?: boolean }) => {
      if (suppressViewPersistRef.current || !viewBootstrappedRef.current) return;
      const wrap = canvasWrapRef.current;
      if (!wrap) return;

      const commit = () => {
        if (suppressViewPersistRef.current || !viewBootstrappedRef.current) return;
        const el = canvasWrapRef.current;
        if (!el) return;
        const anchor = captureStageViewAnchor(el);
        const current = prefsRef.current;
        if (
          current.stageViewAnchorSaved &&
          current.stageViewAnchorX === anchor.x &&
          current.stageViewAnchorY === anchor.y &&
          current.stageScrollLeft === el.scrollLeft &&
          current.stageScrollTop === el.scrollTop
        ) {
          return;
        }
        patchPrefs({
          stageViewAnchorX: anchor.x,
          stageViewAnchorY: anchor.y,
          stageScrollLeft: el.scrollLeft,
          stageScrollTop: el.scrollTop,
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

  const applySavedViewToWrap = useCallback(() => {
    const wrap = canvasWrapRef.current;
    const current = prefsRef.current;
    if (!wrap || !current.stageViewAnchorSaved) return false;
    if (wrap.clientWidth <= 0 || wrap.clientHeight <= 0) return false;

    suppressViewPersistRef.current = true;

    // Prefer scroll absoluto (mesmo zoom/janela); âncora cobre resize do wrap.
    const hasScroll =
      Number.isFinite(current.stageScrollLeft) && Number.isFinite(current.stageScrollTop);
    if (hasScroll) {
      wrap.scrollLeft = current.stageScrollLeft;
      wrap.scrollTop = current.stageScrollTop;
    } else {
      applyStageViewAnchor(wrap, {
        x: current.stageViewAnchorX,
        y: current.stageViewAnchorY,
      });
    }
    return true;
  }, []);

  const restoreStageViewPosition = useCallback(() => {
    if (!applySavedViewToWrap()) return false;
    // Reaplica após paint (zoom/gutter) para não perder para o ResizeObserver.
    window.requestAnimationFrame(() => {
      applySavedViewToWrap();
      window.requestAnimationFrame(() => {
        applySavedViewToWrap();
        markViewBootstrapped();
        persistStageViewPosition({ immediate: true });
      });
    });
    return true;
  }, [applySavedViewToWrap, markViewBootstrapped, persistStageViewPosition]);

  const finishFitCenter = useCallback(
    (generation: number, pass: number) => {
      if (generation !== fitGenerationRef.current) return;
      const wrap = canvasWrapRef.current;
      if (!wrap || wrap.clientWidth <= 0 || wrap.clientHeight <= 0) {
        if (pass >= STAGE_VIEW_FIT_MAX_ATTEMPTS) {
          pendingFitCenterRef.current = false;
          markViewBootstrapped();
          return;
        }
        window.requestAnimationFrame(() => finishFitCenter(generation, pass + 1));
        return;
      }

      applyCenteredStageScroll(wrap);

      if (pass < STAGE_VIEW_FIT_CENTER_PASSES) {
        window.requestAnimationFrame(() => finishFitCenter(generation, pass + 1));
        return;
      }

      if (generation !== fitGenerationRef.current) return;
      pendingFitCenterRef.current = false;
      const anchor = captureStageViewAnchor(wrap);
      patchPrefs({
        stageViewAnchorX: anchor.x,
        stageViewAnchorY: anchor.y,
        stageScrollLeft: wrap.scrollLeft,
        stageScrollTop: wrap.scrollTop,
        stageViewAnchorSaved: true,
      });
      markViewBootstrapped();
    },
    [markViewBootstrapped, patchPrefs],
  );

  /**
   * Centraliza depois que o React aplica o novo `stageZoom` no DOM.
   * Sem isso, o scroll usava o zoom antigo do localStorage e a página
   * voltava deslocada (réguas em ~1000/600 no canto aparente).
   */
  useLayoutEffect(() => {
    if (!pendingFitCenterRef.current) return;
    const generation = fitGenerationRef.current;
    finishFitCenter(generation, 0);
  }, [prefs.stageZoom, finishFitCenter]);

  /** Ajustar: fit + grava âncora (primeira posição ou clique do usuário). */
  const fitStageToView = useCallback(() => {
    const generation = ++fitGenerationRef.current;
    pendingFitCenterRef.current = false;
    suppressViewPersistRef.current = true;

    const attemptFit = (attempt: number) => {
      if (generation !== fitGenerationRef.current) return;
      const wrap = canvasWrapRef.current;
      const canvas = interactionCanvasRefSlot.current?.current ?? null;
      if (
        !wrap ||
        !canvas ||
        wrap.clientWidth <= 0 ||
        wrap.clientHeight <= 0 ||
        canvas.offsetWidth <= 0 ||
        canvas.offsetHeight <= 0
      ) {
        if (attempt >= STAGE_VIEW_FIT_MAX_ATTEMPTS) {
          markViewBootstrapped();
          return;
        }
        window.requestAnimationFrame(() => attemptFit(attempt + 1));
        return;
      }

      const nextZoom = computeFitStageZoom(wrap, canvas);
      const zoomUnchanged = Math.abs(prefsRef.current.stageZoom - nextZoom) < 0.005;
      pendingFitCenterRef.current = true;
      if (zoomUnchanged) {
        // Mesmo zoom: layout effect não reexecuta — centraliza na sequência de frames.
        window.requestAnimationFrame(() => finishFitCenter(generation, 0));
        return;
      }
      patchPrefs({ stageZoom: nextZoom });
    };

    attemptFit(0);
  }, [finishFitCenter, markViewBootstrapped, patchPrefs]);

  /**
   * Ao abrir o editor: sempre Ajustar (fit).
   * Restaurar scroll/zoom do localStorage deslocava o slide (canto da viewport)
   * entre sessões / tamanhos de painel diferentes.
   */
  const bootstrapStageViewPosition = useCallback(() => {
    suppressViewPersistRef.current = true;
    viewBootstrappedRef.current = false;
    setStageViewReady(false);
    fitStageToView();
  }, [fitStageToView]);

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
    stageGridSizePercent: prefs.stageGridSizePercent,
    setStageGridSizePercent: (value: number | ((prev: number) => number)) => {
      const raw =
        typeof value === "function" ? value(prefsRef.current.stageGridSizePercent) : value;
      patchPrefs({ stageGridSizePercent: raw });
    },
    stageGridSizePercentRef,
    showStageGuides: prefs.showStageGuides,
    setShowStageGuides: (value: boolean | ((prev: boolean) => boolean)) => {
      const next = typeof value === "function" ? value(prefsRef.current.showStageGuides) : value;
      patchPrefs({ showStageGuides: next });
    },
    showStageGuidesRef,
    snapToGrid: prefs.snapToGrid,
    setSnapToGrid: (value: boolean | ((prev: boolean) => boolean)) => {
      const next = typeof value === "function" ? value(prefsRef.current.snapToGrid) : value;
      patchPrefs({ snapToGrid: next });
    },
    snapToGridRef,
    snapToObjects: prefs.snapToObjects,
    setSnapToObjects: (value: boolean | ((prev: boolean) => boolean)) => {
      const next = typeof value === "function" ? value(prefsRef.current.snapToObjects) : value;
      patchPrefs({ snapToObjects: next });
    },
    snapToObjectsRef,
    stageViewAnchorSaved: prefs.stageViewAnchorSaved,
    stageViewReady,
    canvasWrapRef,
    fitStageToView,
    restoreStageViewPosition,
    bootstrapStageViewPosition,
    persistStageViewPosition,
    bindCanvasRef,
    stagePanMode,
    setStagePanMode: (enabled: boolean) => {
      setStagePanModeState(enabled);
    },
  };
}
