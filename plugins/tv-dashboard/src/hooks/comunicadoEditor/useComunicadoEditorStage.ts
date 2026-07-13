import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import {
  readStageDisplayPreferences,
  stageViewNeedsInitialFit,
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

/**
 * Estado de UI do palco (zoom, réguas, grade, guias, snap, posição) + fit à viewport.
 * Preferências persistem em localStorage (sobrevivem ao refresh).
 * O ref do canvas de interação é ligado depois via `bindCanvasRef`.
 *
 * Sem âncora salva: bootstrap = Ajustar (fit) e grava a primeira posição.
 * Com âncora: restaura — nunca chama fit (evita apagar a vista do usuário).
 */
export function useComunicadoEditorStage() {
  const [prefs, setPrefs] = useState<StageDisplayPreferences>(() => readStageDisplayPreferences());
  /** Ferramenta pan (mão) — sessão; não persiste em localStorage. */
  const [stagePanMode, setStagePanModeState] = useState(false);
  /** false durante bootstrap — Composer não deve compensar gutter sobre o restore. */
  const [stageViewReady, setStageViewReady] = useState(false);
  const canvasWrapRef = useRef<HTMLDivElement | null>(null);
  const snapEnabledRef = useRef(prefs.snapEnabled);
  const stageGridSizePxRef = useRef(prefs.stageGridSizePx);
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

  /** Ajustar: fit + grava âncora (primeira posição ou clique do usuário). */
  const fitStageToView = useCallback(() => {
    const attemptFit = (attempt: number) => {
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

      suppressViewPersistRef.current = true;
      patchPrefs({ stageZoom: computeFitStageZoom(wrap, canvas) });
      window.requestAnimationFrame(() => {
        applyCenteredStageScroll(wrap);
        const anchor = captureStageViewAnchor(wrap);
        patchPrefs({
          stageViewAnchorX: anchor.x,
          stageViewAnchorY: anchor.y,
          stageScrollLeft: wrap.scrollLeft,
          stageScrollTop: wrap.scrollTop,
          stageViewAnchorSaved: true,
        });
        markViewBootstrapped();
      });
    };

    attemptFit(0);
  }, [markViewBootstrapped, patchPrefs]);

  /**
   * No load: restaura âncora/scroll salvos; se não houver, usa Ajustar.
   * Nunca faz fit quando já existe posição salva (senão apaga a vista do usuário).
   */
  const bootstrapStageViewPosition = useCallback(() => {
    suppressViewPersistRef.current = true;
    viewBootstrappedRef.current = false;
    setStageViewReady(false);

    const tryRestore = (attempt: number) => {
      if (stageViewNeedsInitialFit(prefsRef.current)) {
        fitStageToView();
        return;
      }
      if (restoreStageViewPosition()) return;
      if (attempt < STAGE_VIEW_FIT_MAX_ATTEMPTS) {
        window.requestAnimationFrame(() => tryRestore(attempt + 1));
        return;
      }
      // Ainda sem layout — libera persist e tenta restore uma última vez sem fit.
      markViewBootstrapped();
      window.requestAnimationFrame(() => {
        applySavedViewToWrap();
      });
    };

    tryRestore(0);
  }, [applySavedViewToWrap, fitStageToView, markViewBootstrapped, restoreStageViewPosition]);

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
