import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  DesignViewportStage,
  NativeSlideView,
  PresentationStageControls,
  PresentationPlaybackProvider,
  MeetingAnnotationOverlay,
  applyRuntimeInputValue,
  emptyInputFilterContributions,
  hasInputFilterContributions,
  isComunicadoInputBlock,
  useMeetingAnnotations,
  usePresentationChromeVisibility,
  usePresentationEngine,
  useSessionPlaybackMode,
  buildPublicPresentationWsUrl,
  resolveSlideTransitionStyle,
  presentationSurfaceFromViewMode,
  presentationStageEntranceClass,
  resolvePresentationPlaybackClientId,
  ExternalSlideView,
  type ComunicadoBlock,
  type InputFilterContributions,
  type PresentationMeetingInkClearEvent,
  type PresentationMeetingInkStrokeEvent,
  type PresentationMeetingLaserEvent,
  type PresentationRealtimeEvent,
} from "@delpi/tv-dashboard-presentation";

import type { PublicPresentationPayload, PublicSlide } from "./api";
import { refreshPublicPresentation, sendPresentationHeartbeat } from "./api";

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

  const [livePlaylistMode, setLivePlaylistMode] = useState(
    () => initialPayload.playlist.playbackMode,
  );
  useEffect(() => {
    setLivePlaylistMode(initialPayload.playlist.playbackMode);
  }, [initialPayload.playlist.playbackMode]);

  const {
    playbackMode,
    setPlaybackMode,
    autoAdvance,
  } = useSessionPlaybackMode({
    scopeKey: token || initialPayload.playlist.id,
    playlistMode: livePlaylistMode,
  });

  const playbackClientId = useMemo(
    () => resolvePresentationPlaybackClientId(token || initialPayload.playlist.id),
    [token, initialPayload.playlist.id],
  );
  const meetingSendRef = useRef<((payload: Record<string, unknown>) => void) | null>(null);
  const meetingHandlersRef = useRef<{
    laser: (event: PresentationMeetingLaserEvent) => void;
    ink: (event: PresentationMeetingInkStrokeEvent) => void;
    clear: (event: PresentationMeetingInkClearEvent) => void;
  }>({
    laser: () => undefined,
    ink: () => undefined,
    clear: () => undefined,
  });

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
    autoAdvance,
    realtimeWsUrl:
      mode === "public" && token ? buildPublicPresentationWsUrl(token) : null,
    syncPlaybackCursor: playbackMode === "meeting",
    playbackClientId,
    syncMeetingAnnotations: playbackMode === "meeting",
    externalSendRef: meetingSendRef,
    onMeetingLaser: (event) => meetingHandlersRef.current.laser(event),
    onMeetingInk: (event) => meetingHandlersRef.current.ink(event),
    onMeetingInkClear: (event) => meetingHandlersRef.current.clear(event),
  });

  const currentSlideId = slides[index]?.id ?? "";
  const annotations = useMeetingAnnotations({
    enabled: playbackMode === "meeting",
    clientId: playbackClientId,
    slideId: currentSlideId,
    sendRef: meetingSendRef,
  });
  meetingHandlersRef.current = {
    laser: annotations.applyRemoteLaser,
    ink: annotations.applyRemoteInk,
    clear: annotations.applyRemoteInkClear,
  };

  useEffect(() => {
    setLivePlaylistMode(payload.playlist.playbackMode);
  }, [payload.playlist.playbackMode]);

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

  const surface = presentationSurfaceFromViewMode(mode);
  const stageClass = [
    "tdp-stage",
    surface === "kiosk" ? "tdp-stage--kiosk" : null,
    presentationStageEntranceClass(surface),
  ]
    .filter(Boolean)
    .join(" ");

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
          Pré-visualização · Modo {playbackMode === "meeting" ? "reunião" : "apresentação"} · ← →
          slides · Espaço {playbackMode === "meeting" ? "= próxima" : "pausa"}
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
                <ExternalSlideView
                  url={slide.external?.url}
                  title={slide.title}
                  sandbox={slide.external?.sandbox}
                  active={active}
                />
              )}
            </div>
          );
        })}
        <MeetingAnnotationOverlay
          ref={annotations.overlayRef}
          enabled={playbackMode === "meeting"}
          slideId={currentSlideId}
          clientId={playbackClientId}
          tool={annotations.tool}
          strokes={annotations.strokes}
          onLocalStroke={annotations.publishStroke}
          onLocalLaserNetwork={annotations.publishLaserNetwork}
        />
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
        playbackMode={playbackMode}
        onPlaybackModeChange={setPlaybackMode}
        annotationTool={annotations.tool}
        onAnnotationToolChange={annotations.setTool}
        onClearAnnotations={annotations.clearInk}
      />
      </div>
    </PresentationPlaybackProvider>
  );
}
