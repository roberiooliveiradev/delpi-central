import { useMemo } from "react";
import {
  usePresentationEngine,
  useFullscreenStage,
  NativeSlideView,
  buildAdminPresentationWsUrl,
  usePresentationRealtime,
} from "@delpi/tv-dashboard-presentation";

import type { PresentationPayload } from "../api/tvDashboardApi";
import { getAccessToken } from "../api/httpClient";
import { ExternalSlidePreview } from "./ExternalSlidePreview";
import { PreviewControls } from "./PreviewControls";
import "./presentation.css";

type Props = {
  payload: PresentationPayload;
  playlistId?: string;
  onClose?: () => void;
  onRefresh?: () => Promise<PresentationPayload>;
};

export function PresentationPreview({ payload: initial, playlistId, onRefresh }: Props) {
  const { ref, toggleFullscreen } = useFullscreenStage();
  const {
    index,
    slides,
    viewport,
    transition,
    paused,
    setPaused,
    setIndex,
    setPayload,
  } = usePresentationEngine({
    initialPayload: initial,
    onRefresh,
    enableHiddenPause: false,
    enableKeyboardPause: true,
    refreshNativeSlidesOnly: true,
  });

  const wsUrl = useMemo(() => {
    if (!playlistId) return null;
    const token = getAccessToken();
    if (!token) return null;
    return buildAdminPresentationWsUrl(playlistId, token);
  }, [playlistId]);

  usePresentationRealtime({
    enabled: Boolean(playlistId && onRefresh),
    wsUrl,
    onPresentationUpdated: () => {
      if (!onRefresh) return;
      void onRefresh().then((next) => {
        if (next) setPayload(next);
      });
    },
  });

  if (!slides.length) {
    return (
      <div className="tdp-stage" data-viewport={viewport}>
        <div className="tdp-empty">Nenhuma tela configurada.</div>
      </div>
    );
  }

  return (
    <div
      ref={ref}
      className="tdp-stage tdp-stage--preview-shell"
      data-viewport={viewport}
      onDoubleClick={() => void toggleFullscreen()}
    >
      <div className="tdp-preview-badge">Pré-visualização · duplo-clique = tela cheia · Espaço = pausar</div>
      {slides.map((slide, slideIndex) => {
        const active = slideIndex === index;
        return (
          <div
            key={slide.id}
            className={`tdp-slide tdp-slide--${transition}${active ? " tdp-slide--active" : ""}`}
            aria-hidden={!active}
          >
            {slide.slideType === "native" && slide.native ? (
              <NativeSlideView native={slide.native} />
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
      <PreviewControls
        index={index}
        total={slides.length}
        paused={paused}
        onPauseToggle={() => setPaused(!paused)}
        onPrevious={() => setIndex((index - 1 + slides.length) % slides.length)}
        onNext={() => setIndex((index + 1) % slides.length)}
      />
    </div>
  );
}
