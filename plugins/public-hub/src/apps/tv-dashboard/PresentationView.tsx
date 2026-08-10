import { useCallback, useEffect, useRef, useState } from "react";

import {
  DesignViewportStage,
  NativeSlideView,
  PresentationStageControls,
  PresentationPlaybackProvider,
  applyRuntimeInputValue,
  emptyInputFilterContributions,
  hasInputFilterContributions,
  isComunicadoInputBlock,
  usePresentationChromeVisibility,
  usePresentationEngine,
  buildPublicPresentationWsUrl,
  resolveSlideTransitionStyle,
  presentationSurfaceFromViewMode,
  type ComunicadoBlock,
  type InputFilterContributions,
  type PresentationRealtimeEvent,
} from "@delpi/tv-dashboard-presentation";

import type { PublicPresentationPayload, PublicSlide } from "./api";
import { refreshPublicPresentation, sendPresentationHeartbeat } from "./api";
import { ExternalSlideView } from "./ExternalSlideView";

/**
 * Viewer puro da programação TV.
 * Sem lógica de agregação/encoding/filtro de dados — só playback + render do
 * `NativeSlideView` / `RichComunicadoStage` com o payload já enriquecido pela API
 * (`SlideDataResolutionService`, mesmo caminho do preview do editor).
 */
type PresentationViewProps = {
  payload: PublicPresentationPayload;
  token?: string;
  mode?: "public" | "preview";
  onRefresh?: (filters?: InputFilterContributions | null) => Promise<PublicPresentationPayload | null>;
};

function blocksFromSlide(slide: PublicSlide | undefined): ComunicadoBlock[] {
  const data = slide?.native?.data;
  if (!data || typeof data !== "object") return [];
  const blocks = (data as { blocks?: unknown }).blocks;
  return Array.isArray(blocks) ? (blocks as ComunicadoBlock[]) : [];
}

export function PresentationView({
  payload: initialPayload,
  token,
  mode = "public",
  onRefresh,
}: PresentationViewProps) {
  const [runtimeOverrides, setRuntimeOverrides] = useState<InputFilterContributions>(() =>
    emptyInputFilterContributions(),
  );
  const [inputRuntimeValues, setInputRuntimeValues] = useState<
    Record<string, string | number | boolean | null>
  >({});
  const overridesRef = useRef(runtimeOverrides);
  overridesRef.current = runtimeOverrides;
  const debounceRef = useRef<number | null>(null);

  const reloadPayload = useCallback(
    async (event?: PresentationRealtimeEvent) => {
      const filters = hasInputFilterContributions(overridesRef.current)
        ? overridesRef.current
        : null;
      if (onRefresh) return onRefresh(filters);
      if (!token) return null;
      return refreshPublicPresentation(token, filters, event?.revision ?? null);
    },
    [onRefresh, token],
  );

  const { visible: chromeVisible } = usePresentationChromeVisibility();

  const {
    payload,
    setPayload,
    index,
    slides,
    viewport,
    paused,
    setPaused,
    goPrevious,
    goNext,
    goToSection,
  } = usePresentationEngine<PublicPresentationPayload>({
    initialPayload,
    onRefresh: onRefresh || token ? reloadPayload : undefined,
    enableKeyboardControls: true,
    enableHiddenPause: true,
    refreshNativeSlidesOnly: true,
    realtimeWsUrl:
      mode === "public" && token ? buildPublicPresentationWsUrl(token) : null,
  });

  const heartbeatIntervalSec =
    payload.presentationMeta?.heartbeatIntervalSec ?? 60;

  useEffect(() => {
    if (mode !== "public" || !token) return;
    const send = () => {
      if (document.visibilityState === "hidden") return;
      void sendPresentationHeartbeat(token).catch(() => undefined);
    };
    send();
    const timer = window.setInterval(send, heartbeatIntervalSec * 1000);
    return () => window.clearInterval(timer);
  }, [mode, token, heartbeatIntervalSec]);

  useEffect(() => {
    return () => {
      if (debounceRef.current != null) window.clearTimeout(debounceRef.current);
    };
  }, []);

  const handleInputValueChange = useCallback(
    (blockId: string, value: string | number | boolean | null) => {
      const slide = slides[index] as PublicSlide | undefined;
      const block = blocksFromSlide(slide).find((item) => item.id === blockId);
      if (!block || !isComunicadoInputBlock(block)) return;

      setInputRuntimeValues((prev) => ({ ...prev, [blockId]: value }));
      setRuntimeOverrides((prev) => {
        const next = applyRuntimeInputValue(prev, block, value);
        overridesRef.current = next;
        return next;
      });

      if (debounceRef.current != null) window.clearTimeout(debounceRef.current);
      debounceRef.current = window.setTimeout(() => {
        void reloadPayload().then((next) => {
          if (next) setPayload(next);
        });
      }, 400);
    },
    [slides, index, reloadPayload, setPayload],
  );

  const stageClass =
    mode === "public" ? "tdp-stage tdp-stage--kiosk" : "tdp-stage";

  if (!slides.length) {
    return (
      <div className={stageClass} data-viewport={viewport}>
        <div className="tdp-empty">Nenhuma tela configurada nesta programação.</div>
      </div>
    );
  }

  return (
    <PresentationPlaybackProvider deckPaused={paused}>
      <div className={stageClass} data-viewport={viewport}>
      {mode === "preview" ? (
        <div
          className={[
            "tdp-preview-badge",
            chromeVisible ? null : "tdp-preview-badge--hidden",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          Pré-visualização · ← → slides · Espaço pausa
        </div>
      ) : null}
      <DesignViewportStage
        viewportProfile={viewport}
        viewportWidth={payload.playlist.viewportWidth}
        viewportHeight={payload.playlist.viewportHeight}
        className="tdp-stage__design"
        surface={presentationSurfaceFromViewMode(mode)}
        fit="auto"
      >
        {(slides as PublicSlide[]).map((slide: PublicSlide, slideIndex: number) => {
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
                <ExternalSlideView slide={slide} active={active} />
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
        sections={payload.sections}
        onJumpToSection={goToSection}
      />
      </div>
    </PresentationPlaybackProvider>
  );
}
