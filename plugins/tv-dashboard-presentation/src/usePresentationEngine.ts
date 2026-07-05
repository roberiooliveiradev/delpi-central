import { useCallback, useEffect, useMemo, useState } from "react";

import type { PresentationPayloadLike, PresentationSlide } from "./types";
import { usePresentationRealtime } from "./usePresentationRealtime";

export type UsePresentationEngineOptions<T extends PresentationPayloadLike> = {
  initialPayload: T;
  onRefresh?: () => Promise<T | null>;
  enableKeyboardPause?: boolean;
  enableHiddenPause?: boolean;
  refreshNativeSlidesOnly?: boolean;
  realtimeWsUrl?: string | null;
};

export function usePresentationEngine<T extends PresentationPayloadLike>({
  initialPayload,
  onRefresh,
  enableKeyboardPause = false,
  enableHiddenPause = true,
  refreshNativeSlidesOnly = false,
  realtimeWsUrl = null,
}: UsePresentationEngineOptions<T>) {
  const [payload, setPayload] = useState(initialPayload);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [hidden, setHidden] = useState(
    typeof document !== "undefined" ? document.visibilityState === "hidden" : false,
  );

  const slides = useMemo(
    () => [...(payload.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder) as T["slides"],
    [payload.slides],
  );

  const playlist = payload.playlist;
  const viewport = playlist.viewportProfile || "1080p";
  const transition = playlist.transitionStyle || "fade";
  const refreshSec = playlist.globalRefreshSec || 300;
  const nativeErrorAdvanceSec = payload.presentationMeta?.nativeErrorAdvanceSec ?? 10;
  const current: PresentationSlide | undefined = slides[index];

  const nativeError =
    current?.slideType === "native" &&
    current.native?.data &&
    current.native.data.error === true;

  const reloadPayload = useCallback(async () => {
    if (!onRefresh) return;
    const next = await onRefresh();
    if (next) setPayload(next);
  }, [onRefresh]);

  useEffect(() => {
    setPayload(initialPayload);
  }, [initialPayload]);

  useEffect(() => {
    if (!enableHiddenPause) return;
    const onVisibility = () => setHidden(document.visibilityState === "hidden");
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [enableHiddenPause]);

  useEffect(() => {
    if (slides.length === 0) return;
    if (index >= slides.length) setIndex(0);
  }, [slides.length, index]);

  useEffect(() => {
    if (!slides.length || paused || (enableHiddenPause && hidden)) return;
    const baseSec = current?.durationSec ?? playlist.defaultDurationSec ?? 30;
    const durationMs = (nativeError ? nativeErrorAdvanceSec : baseSec) * 1000;
    const timer = window.setTimeout(() => {
      setIndex((prev: number) => (prev + 1) % slides.length);
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
    enableHiddenPause,
  ]);

  useEffect(() => {
    if (!refreshSec || !onRefresh) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      if (refreshNativeSlidesOnly && current?.slideType !== "native") return;
      void reloadPayload();
    }, refreshSec * 1000);
    return () => window.clearInterval(timer);
  }, [refreshSec, reloadPayload, onRefresh, refreshNativeSlidesOnly, current?.slideType]);

  usePresentationRealtime({
    enabled: Boolean(realtimeWsUrl && onRefresh),
    wsUrl: realtimeWsUrl,
    onPresentationUpdated: () => {
      void reloadPayload();
    },
  });

  useEffect(() => {
    if (!enableKeyboardPause) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.code === "Space") {
        event.preventDefault();
        setPaused((value: boolean) => !value);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [enableKeyboardPause]);

  return {
    payload,
    setPayload,
    index,
    setIndex,
    slides,
    current,
    paused,
    setPaused,
    hidden,
    viewport,
    transition,
    refreshSec,
    nativeErrorAdvanceSec,
    nativeError,
  };
}
