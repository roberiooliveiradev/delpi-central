import { useCallback, useEffect } from "react";

import {
  DesignViewportStage,
  NativeSlideView,
  PresentationStageControls,
  usePresentationChromeVisibility,
  usePresentationEngine,
  buildPublicPresentationWsUrl,
  resolveSlideTransitionStyle,
} from "@delpi/tv-dashboard-presentation";

import type { PublicPresentationPayload, PublicSlide } from "./api";
import { refreshPublicPresentation, sendPresentationHeartbeat } from "./api";
import { ExternalSlideView } from "./ExternalSlideView";

type PresentationViewProps = {
  payload: PublicPresentationPayload;
  token?: string;
  mode?: "public" | "preview";
  onRefresh?: () => Promise<PublicPresentationPayload | null>;
};

export function PresentationView({
  payload: initialPayload,
  token,
  mode = "public",
  onRefresh,
}: PresentationViewProps) {
  const reloadPayload = useCallback(async () => {
    if (onRefresh) return onRefresh();
    if (!token) return null;
    return refreshPublicPresentation(token);
  }, [onRefresh, token]);

  const { visible: chromeVisible } = usePresentationChromeVisibility();

  const {
    payload,
    index,
    slides,
    viewport,
    paused,
    setPaused,
    goPrevious,
    goNext,
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
      <DesignViewportStage viewportProfile={viewport} className="tdp-stage__design" fit="contain">
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
                <NativeSlideView native={slide.native} comunicadoFontScale={1} />
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
      />
    </div>
  );
}
