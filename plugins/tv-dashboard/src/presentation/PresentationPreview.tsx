import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  usePresentationEngine,
  useFullscreenStage,
  usePresentationChromeVisibility,
  PresentationStageControls,
  NativeSlideView,
  DesignViewportStage,
  buildAdminPresentationWsUrl,
  resolveSlideTransitionStyle,
  applyRuntimeInputValue,
  emptyInputFilterContributions,
  hasInputFilterContributions,
  isComunicadoInputBlock,
  type ComunicadoBlock,
  type InputFilterContributions,
} from "@delpi/tv-dashboard-presentation";

import type { PresentationPayload } from "../api/tvDashboardApi";
import { rewriteAdminMediaUrlsForBrowser } from "../api/browserSafeMediaUrl";
import { getAccessToken } from "../api/httpClient";
import { ExternalSlidePreview } from "./ExternalSlidePreview";
import "./presentation.css";

type Props = {
  payload: PresentationPayload;
  playlistId?: string;
  onClose?: () => void;
  onRefresh?: (filters?: InputFilterContributions | null) => Promise<PresentationPayload>;
};

function blocksFromNativeData(data: Record<string, unknown> | undefined): ComunicadoBlock[] {
  if (!data || typeof data !== "object") return [];
  const blocks = data.blocks;
  return Array.isArray(blocks) ? (blocks as ComunicadoBlock[]) : [];
}

function forBrowserDisplay(payload: PresentationPayload): PresentationPayload {
  return rewriteAdminMediaUrlsForBrowser(payload);
}

export function PresentationPreview({ payload: initial, playlistId, onRefresh }: Props) {
  const presenterMode = useMemo(
    () => new URLSearchParams(window.location.search).get("presenter") === "1",
    [],
  );
  const { ref, toggleFullscreen } = useFullscreenStage();
  const [booting, setBooting] = useState(true);
  const { visible: chromeVisible } = usePresentationChromeVisibility();
  const [runtimeOverrides, setRuntimeOverrides] = useState<InputFilterContributions>(() =>
    emptyInputFilterContributions(),
  );
  const [inputRuntimeValues, setInputRuntimeValues] = useState<
    Record<string, string | number | boolean | null>
  >({});
  const overridesRef = useRef(runtimeOverrides);
  overridesRef.current = runtimeOverrides;
  const debounceRef = useRef<number | null>(null);

  const wsUrl = useMemo(() => {
    if (!playlistId) return null;
    const token = getAccessToken();
    if (!token) return null;
    return buildAdminPresentationWsUrl(playlistId, token);
  }, [playlistId]);

  const reloadWithFilters = useCallback(async () => {
    if (!onRefresh) return null;
    const filters = hasInputFilterContributions(overridesRef.current)
      ? overridesRef.current
      : null;
    const next = await onRefresh(filters);
    return next ? forBrowserDisplay(next) : null;
  }, [onRefresh]);

  const {
    index,
    slides,
    viewport,
    payload,
    setPayload,
    paused,
    setPaused,
    goPrevious,
    goNext,
  } = usePresentationEngine({
    initialPayload: forBrowserDisplay(initial),
    onRefresh: onRefresh ? reloadWithFilters : undefined,
    enableHiddenPause: false,
    enableKeyboardControls: true,
    refreshNativeSlidesOnly: true,
    realtimeWsUrl: wsUrl,
  });

  // Primeiro paint: sem fade/entrada — evita flash ao abrir a prévia.
  useEffect(() => {
    setBooting(true);
    let inner = 0;
    const outer = window.requestAnimationFrame(() => {
      inner = window.requestAnimationFrame(() => setBooting(false));
    });
    return () => {
      window.cancelAnimationFrame(outer);
      window.cancelAnimationFrame(inner);
    };
  }, [playlistId, initial.playlist?.id]);

  useEffect(() => {
    return () => {
      if (debounceRef.current != null) window.clearTimeout(debounceRef.current);
    };
  }, []);

  const handleInputValueChange = useCallback(
    (blockId: string, value: string | number | boolean | null) => {
      const slide = slides[index];
      const block = blocksFromNativeData(
        slide?.native?.data as Record<string, unknown> | undefined,
      ).find((item) => item.id === blockId);
      if (!block || !isComunicadoInputBlock(block)) return;

      setInputRuntimeValues((prev) => ({ ...prev, [blockId]: value }));
      setRuntimeOverrides((prev) => {
        const next = applyRuntimeInputValue(prev, block, value);
        overridesRef.current = next;
        return next;
      });

      if (!onRefresh) return;
      if (debounceRef.current != null) window.clearTimeout(debounceRef.current);
      debounceRef.current = window.setTimeout(() => {
        void reloadWithFilters().then((next) => {
          if (next) setPayload(next);
        });
      }, 400);
    },
    [slides, index, onRefresh, reloadWithFilters, setPayload],
  );

  if (!slides.length) {
    return (
      <div className="tdp-stage" data-viewport={viewport}>
        <div className="tdp-empty">Nenhuma tela configurada.</div>
      </div>
    );
  }

  const currentSlide = slides[index];
  const notesSource = currentSlide?.native?.config ?? currentSlide?.native?.data;
  const speakerNotes =
    notesSource && typeof notesSource.speakerNotes === "string" ? notesSource.speakerNotes : "";
  const nextSlide = slides.length > 1 ? slides[(index + 1) % slides.length] : undefined;

  return (
    <div
      ref={ref}
      className={[
        "tdp-stage",
        "tdp-stage--preview-shell",
        presenterMode ? "tdp-stage--presenter" : null,
        booting ? "tdp-stage--boot" : null,
      ]
        .filter(Boolean)
        .join(" ")}
      data-viewport={viewport}
      onDoubleClick={() => void toggleFullscreen()}
    >
      <div
        className={[
          "tdp-preview-badge",
          chromeVisible ? null : "tdp-preview-badge--hidden",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        Pré-visualização · ← → slides · Espaço pausa · duplo-clique = tela cheia
      </div>
      <DesignViewportStage viewportProfile={viewport} className="tdp-stage__design" fit="contain">
        {slides.map((slide, slideIndex) => {
          const active = slideIndex === index;
          const slideTransition = resolveSlideTransitionStyle(slide, payload.playlist);
          return (
            <div
              key={slide.id}
              className={`tdp-slide tdp-slide--${slideTransition}${active ? " tdp-slide--active" : ""}`}
              aria-hidden={!active}
            >
              {slide.slideType === "native" && slide.native ? (
                <NativeSlideView
                  native={slide.native}
                  comunicadoFontScale={1}
                  inputsInteractive
                  inputRuntimeValues={active ? inputRuntimeValues : undefined}
                  onInputValueChange={active ? handleInputValueChange : undefined}
                />
              ) : (
                <ExternalSlidePreview
                  url={slide.external?.url}
                  title={slide.title}
                  sandbox={slide.external?.sandbox}
                  active={active}
                />
              )}
            </div>
          );
        })}
      </DesignViewportStage>
      <PresentationStageControls
        index={index}
        total={slides.length}
        paused={paused}
        visible={chromeVisible}
        onPauseToggle={() => setPaused(!paused)}
        onPrevious={goPrevious}
        onNext={goNext}
      />
      {presenterMode ? (
        <aside className="tdp-presenter-panel" aria-label="Notas do apresentador">
          <h2>Notas do apresentador</h2>
          <div className="tdp-presenter-panel__notes">
            {speakerNotes || "Sem notas para esta tela."}
          </div>
          <div className="tdp-presenter-panel__next">
            <span>Próxima tela</span>
            <strong>{nextSlide?.title ?? "—"}</strong>
          </div>
        </aside>
      ) : null}
    </div>
  );
}
