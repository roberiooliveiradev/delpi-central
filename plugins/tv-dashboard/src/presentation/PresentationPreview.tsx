import { useEffect, useMemo, useState } from "react";
import {
  usePresentationEngine,
  useFullscreenStage,
  usePresentationChromeVisibility,
  PresentationStageControls,
  NativeSlideView,
  DesignViewportStage,
  buildAdminPresentationWsUrl,
  resolveSlideTransitionStyle,
} from "@delpi/tv-dashboard-presentation";

import type { PresentationPayload } from "../api/tvDashboardApi";
import { getAccessToken } from "../api/httpClient";
import { ExternalSlidePreview } from "./ExternalSlidePreview";
import "./presentation.css";

type Props = {
  payload: PresentationPayload;
  playlistId?: string;
  onClose?: () => void;
  onRefresh?: () => Promise<PresentationPayload>;
};

export function PresentationPreview({ payload: initial, playlistId, onRefresh }: Props) {
  const presenterMode = useMemo(
    () => new URLSearchParams(window.location.search).get("presenter") === "1",
    [],
  );
  const { ref, toggleFullscreen } = useFullscreenStage();
  const [booting, setBooting] = useState(true);
  const { visible: chromeVisible } = usePresentationChromeVisibility();
  const wsUrl = useMemo(() => {
    if (!playlistId) return null;
    const token = getAccessToken();
    if (!token) return null;
    return buildAdminPresentationWsUrl(playlistId, token);
  }, [playlistId]);
  const {
    index,
    slides,
    viewport,
    payload,
    paused,
    setPaused,
    goPrevious,
    goNext,
  } = usePresentationEngine({
    initialPayload: initial,
    onRefresh,
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
      <DesignViewportStage viewportProfile={viewport} className="tdp-stage__design">
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
                <NativeSlideView native={slide.native} comunicadoFontScale={1} />
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
