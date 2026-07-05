import { useCallback, useEffect, useMemo, useState } from "react";

import type { PublicPresentationPayload } from "./api";
import { refreshPublicPresentation, sendPresentationHeartbeat } from "./api";
import { ExternalSlideView } from "./ExternalSlideView";
import { NativeSlideView } from "./NativeScreens";
import "./native-screens.css";

type PresentationViewProps = {
  payload: PublicPresentationPayload;
  token?: string;
  mode?: "public" | "preview";
  onRefresh?: () => Promise<PublicPresentationPayload | null>;
};

const HEARTBEAT_INTERVAL_SEC = 60;

export function PresentationView({
  payload: initialPayload,
  token,
  mode = "public",
  onRefresh,
}: PresentationViewProps) {
  const [payload, setPayload] = useState(initialPayload);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [hidden, setHidden] = useState(
    typeof document !== "undefined" ? document.visibilityState === "hidden" : false,
  );

  const slides = useMemo(
    () => [...(payload.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder),
    [payload.slides],
  );

  const playlist = payload.playlist;
  const viewport = playlist.viewportProfile || "1080p";
  const refreshSec = playlist.globalRefreshSec || 300;
  const transition = playlist.transitionStyle || "fade";
  const nativeErrorAdvanceSec = payload.presentationMeta?.nativeErrorAdvanceSec ?? 10;
  const heartbeatIntervalSec = payload.presentationMeta?.heartbeatIntervalSec ?? HEARTBEAT_INTERVAL_SEC;

  const current = slides[index];
  const nativeError =
    current?.slideType === "native" &&
    current.native?.data &&
    (current.native.data as { error?: boolean }).error === true;

  useEffect(() => {
    const onVisibility = () => setHidden(document.visibilityState === "hidden");
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  const reloadPayload = useCallback(async () => {
    if (onRefresh) {
      const next = await onRefresh();
      if (next) setPayload(next);
      return;
    }
    if (!token) return;
    const next = await refreshPublicPresentation(token);
    if (next) setPayload(next);
  }, [onRefresh, token]);

  useEffect(() => {
    setPayload(initialPayload);
  }, [initialPayload]);

  useEffect(() => {
    if (slides.length === 0) return;
    if (index >= slides.length) setIndex(0);
  }, [slides.length, index]);

  useEffect(() => {
    if (!slides.length || paused || hidden) return;
    const baseSec = current?.durationSec ?? playlist.defaultDurationSec ?? 30;
    const durationMs = (nativeError ? nativeErrorAdvanceSec : baseSec) * 1000;
    const timer = window.setTimeout(() => {
      setIndex((prev) => (prev + 1) % slides.length);
    }, durationMs);
    return () => window.clearTimeout(timer);
  }, [
    slides.length,
    index,
    current,
    paused,
    hidden,
    nativeError,
    nativeErrorAdvanceSec,
    playlist.defaultDurationSec,
  ]);

  useEffect(() => {
    if (!refreshSec) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      void reloadPayload();
    }, refreshSec * 1000);
    return () => window.clearInterval(timer);
  }, [refreshSec, reloadPayload]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.code === "Space") {
        event.preventDefault();
        setPaused((value) => !value);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

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
              <ExternalSlideView slide={slide} active={active} />
            )}
          </div>
        );
      })}
    </div>
  );
}
