import { useCallback, useEffect, useMemo, useState } from "react";

import type { PresentationPayloadLike, PresentationSlide } from "./types";
import { usePresentationRealtime } from "./usePresentationRealtime";
import { resolveSlideTransitionStyle } from "./presentationTransition";

export type UsePresentationEngineOptions<T extends PresentationPayloadLike> = {
  initialPayload: T;
  onRefresh?: () => Promise<T | null>;
  /** @deprecated Use `enableKeyboardControls` (Space + setas). */
  enableKeyboardPause?: boolean;
  /** Space = pausa; ←/→ = slide anterior/próximo. */
  enableKeyboardControls?: boolean;
  enableHiddenPause?: boolean;
  refreshNativeSlidesOnly?: boolean;
  realtimeWsUrl?: string | null;
};

export function usePresentationEngine<T extends PresentationPayloadLike>({
  initialPayload,
  onRefresh,
  enableKeyboardPause = false,
  enableKeyboardControls,
  enableHiddenPause = true,
  refreshNativeSlidesOnly = false,
  realtimeWsUrl = null,
}: UsePresentationEngineOptions<T>) {
  const keyboardEnabled = enableKeyboardControls ?? enableKeyboardPause;
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
  const refreshSec = playlist.globalRefreshSec || 300;
  const nativeErrorAdvanceSec = payload.presentationMeta?.nativeErrorAdvanceSec ?? 10;
  const current: PresentationSlide | undefined = slides[index];
  const transition = resolveSlideTransitionStyle(current, playlist);

  const nativeError =
    current?.slideType === "native" &&
    current.native?.data &&
    current.native.data.error === true;

  const goPrevious = useCallback(() => {
    setIndex((prev) => {
      const len = slides.length;
      if (len <= 1) return prev;
      return (prev - 1 + len) % len;
    });
  }, [slides.length]);

  const goNext = useCallback(() => {
    setIndex((prev) => {
      const len = slides.length;
      if (len <= 1) return prev;
      return (prev + 1) % len;
    });
  }, [slides.length]);

  const reloadPayload = useCallback(async () => {
    if (!onRefresh) return;
    const next = await onRefresh();
    if (next) setPayload(next);
  }, [onRefresh]);

  /*
   * Re-seed quando o pai troca o payload (ex.: fetch da prévia).
   * O pai DEVE memoizar `initialPayload` — referência nova a cada render
   * (ex.: clone em forBrowserDisplay) + setBooting → React #185.
   */
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
    if (!keyboardEnabled) return;
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest?.("input, textarea, select, [contenteditable='true']")) return;

      if (event.code === "Space") {
        event.preventDefault();
        setPaused((value: boolean) => !value);
        return;
      }
      if (event.code === "ArrowLeft") {
        event.preventDefault();
        goPrevious();
        return;
      }
      if (event.code === "ArrowRight") {
        event.preventDefault();
        goNext();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [keyboardEnabled, goNext, goPrevious]);

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
    goPrevious,
    goNext,
  };
}
