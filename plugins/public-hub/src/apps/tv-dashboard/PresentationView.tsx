import { useCallback, useEffect } from "react";

import type { PublicPresentationPayload, PublicSlide } from "./api";
import { refreshPublicPresentation, sendPresentationHeartbeat } from "./api";
import { ExternalSlideView } from "./ExternalSlideView";
import { NativeSlideView } from "./NativeScreens";
import { usePresentationEngine } from "@delpi/tv-dashboard-presentation";
import "./native-screens.css";

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

  const {
    payload,
    index,
    slides,
    viewport,
    transition,
  } = usePresentationEngine<PublicPresentationPayload>({
    initialPayload,
    onRefresh: onRefresh || token ? reloadPayload : undefined,
    enableKeyboardPause: true,
    enableHiddenPause: true,
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

  if (!slides.length) {
    return (
      <div className="tdp-stage" data-viewport={viewport}>
        <div className="tdp-empty">Nenhuma tela configurada nesta programação.</div>
      </div>
    );
  }

  return (
    <div className="tdp-stage" data-viewport={viewport}>
      {mode === "preview" ? (
        <div className="tdp-preview-badge">Pré-visualização</div>
      ) : null}
      {(slides as PublicSlide[]).map((slide: PublicSlide, slideIndex: number) => {
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
              <ExternalSlideView slide={slide} active={active} />
            )}
          </div>
        );
      })}
    </div>
  );
}
