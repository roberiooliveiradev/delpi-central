import { useCallback, useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";

import { applySlideDraftToPayload } from "./applySlideDraftToPayload";
import {
  applyPlaybackCursorToIndex,
} from "./playbackCursor";
import type { PresentationPayloadLike, PresentationSlide } from "./types";
import {
  usePresentationRealtime,
  type PresentationMeetingInkClearEvent,
  type PresentationMeetingInkStrokeEvent,
  type PresentationMeetingLaserEvent,
  type PresentationPlaybackCursorEvent,
  type PresentationRealtimeEvent,
} from "./usePresentationRealtime";
import { resolveSlideTransitionStyle } from "./presentationTransition";

export type UsePresentationEngineOptions<T extends PresentationPayloadLike> = {
  initialPayload: T;
  /** Refresh completo (HTTP). Recebe o evento WS quando a origem for `presentation_updated`. */
  onRefresh?: (event?: PresentationRealtimeEvent) => Promise<T | null>;
  /** @deprecated Use `enableKeyboardControls` (Space + setas). */
  enableKeyboardPause?: boolean;
  /** Space = pausa (apresentação) ou próximo (reunião); ←/→ = slide anterior/próximo. */
  enableKeyboardControls?: boolean;
  enableHiddenPause?: boolean;
  refreshNativeSlidesOnly?: boolean;
  realtimeWsUrl?: string | null;
  /**
   * Quando false (modo reunião), o timer de duração não agenda.
   * Default true = modo apresentação (comportamento histórico).
   */
  autoAdvance?: boolean;
  /**
   * Modo reunião: publica/aplica `playback_cursor` via WS.
   * Requer `playbackClientId` estável por aba.
   */
  syncPlaybackCursor?: boolean;
  playbackClientId?: string | null;
  /** Modo reunião: retransmite caneta/laser (handlers no consumer). */
  syncMeetingAnnotations?: boolean;
  onMeetingLaser?: (event: PresentationMeetingLaserEvent) => void;
  onMeetingInk?: (event: PresentationMeetingInkStrokeEvent) => void;
  onMeetingInkClear?: (event: PresentationMeetingInkClearEvent) => void;
  /** Espelha o send do WS para o consumer (anotações). */
  externalSendRef?: MutableRefObject<((payload: Record<string, unknown>) => void) | null>;
};

export function usePresentationEngine<T extends PresentationPayloadLike>({
  initialPayload,
  onRefresh,
  enableKeyboardPause = false,
  enableKeyboardControls,
  enableHiddenPause = true,
  refreshNativeSlidesOnly = false,
  realtimeWsUrl = null,
  autoAdvance = true,
  syncPlaybackCursor = false,
  playbackClientId = null,
  syncMeetingAnnotations = false,
  onMeetingLaser,
  onMeetingInk,
  onMeetingInkClear,
  externalSendRef,
}: UsePresentationEngineOptions<T>) {
  const keyboardEnabled = enableKeyboardControls ?? enableKeyboardPause;
  const [payload, setPayload] = useState(initialPayload);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [hidden, setHidden] = useState(
    typeof document !== "undefined" ? document.visibilityState === "hidden" : false,
  );
  const sendRef = useRef<((payload: Record<string, unknown>) => void) | null>(null);
  const localNavRef = useRef(false);
  const slidesRef = useRef<T["slides"]>([] as T["slides"]);
  const clientIdRef = useRef(playbackClientId);
  clientIdRef.current = playbackClientId;
  const meetingLaserRef = useRef(onMeetingLaser);
  meetingLaserRef.current = onMeetingLaser;
  const meetingInkRef = useRef(onMeetingInk);
  meetingInkRef.current = onMeetingInk;
  const meetingInkClearRef = useRef(onMeetingInkClear);
  meetingInkClearRef.current = onMeetingInkClear;

  const slides = useMemo(
    () => [...(payload.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder) as T["slides"],
    [payload.slides],
  );
  slidesRef.current = slides;

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

  const publishCursor = useCallback(
    (nextIndex: number) => {
      if (!syncPlaybackCursor) return;
      const clientId = clientIdRef.current;
      const send = sendRef.current;
      const slide = slidesRef.current[nextIndex];
      if (!clientId || !send || !slide) return;
      send({
        type: "playback_cursor",
        clientId,
        slideId: slide.id,
        index: nextIndex,
      });
    },
    [syncPlaybackCursor],
  );

  const goPrevious = useCallback(() => {
    const len = slides.length;
    if (len <= 1) return;
    localNavRef.current = true;
    setIndex((prev) => {
      const next = (prev - 1 + len) % len;
      return next;
    });
  }, [slides.length]);

  const goNext = useCallback(() => {
    const len = slides.length;
    if (len <= 1) return;
    localNavRef.current = true;
    setIndex((prev) => (prev + 1) % len);
  }, [slides.length]);

  const goToIndex = useCallback(
    (nextIndex: number) => {
      if (!slides.length) return;
      const clamped = Math.max(0, Math.min(slides.length - 1, Math.floor(nextIndex)));
      localNavRef.current = true;
      setIndex(clamped);
    },
    [slides.length],
  );

  const goToSection = useCallback(
    (sectionId: string) => {
      const target = slides.findIndex((slide) => slide.sectionId === sectionId);
      if (target < 0) return;
      localNavRef.current = true;
      setIndex(target);
    },
    [slides],
  );

  useEffect(() => {
    if (!localNavRef.current) return;
    localNavRef.current = false;
    publishCursor(index);
  }, [index, publishCursor]);

  const reloadPayload = useCallback(
    async (event?: PresentationRealtimeEvent) => {
      if (!onRefresh) return;
      const next = await onRefresh(event);
      if (next) setPayload(next);
    },
    [onRefresh],
  );

  const onPlaybackCursor = useCallback(
    (event: PresentationPlaybackCursorEvent) => {
      if (!syncPlaybackCursor) return;
      const selfId = clientIdRef.current;
      if (selfId && event.clientId === selfId) return;
      const next = applyPlaybackCursorToIndex(slidesRef.current, event.slideId, event.index);
      if (next == null) return;
      localNavRef.current = false;
      setIndex(next);
    },
    [syncPlaybackCursor],
  );

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
    if (!autoAdvance || !slides.length || paused || (enableHiddenPause && hidden)) return;
    const baseSec = current?.durationSec ?? playlist.defaultDurationSec ?? 30;
    const durationMs = (nativeError ? nativeErrorAdvanceSec : baseSec) * 1000;
    const timer = window.setTimeout(() => {
      // Timer local — não publica cursor (só meeting sync via navegação manual).
      setIndex((prev: number) => (prev + 1) % slides.length);
    }, durationMs);
    return () => window.clearTimeout(timer);
  }, [
    autoAdvance,
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
    enabled: Boolean(
      realtimeWsUrl && (onRefresh || syncPlaybackCursor || syncMeetingAnnotations),
    ),
    wsUrl: realtimeWsUrl,
    sendRef,
    externalSendRef,
    onPresentationUpdated: onRefresh
      ? (event) => {
          void reloadPayload(event);
        }
      : undefined,
    onSlideDraft: (event) => {
      setPayload((prev) => applySlideDraftToPayload(prev, event.slideId, event.nativeConfig));
    },
    onPlaybackCursor: syncPlaybackCursor ? onPlaybackCursor : undefined,
    onMeetingLaser: syncMeetingAnnotations
      ? (event) => meetingLaserRef.current?.(event)
      : undefined,
    onMeetingInk: syncMeetingAnnotations
      ? (event) => meetingInkRef.current?.(event)
      : undefined,
    onMeetingInkClear: syncMeetingAnnotations
      ? (event) => meetingInkClearRef.current?.(event)
      : undefined,
  });

  useEffect(() => {
    if (!keyboardEnabled) return;
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest?.("input, textarea, select, [contenteditable='true']")) return;

      if (event.code === "Space") {
        event.preventDefault();
        if (autoAdvance) {
          setPaused((value: boolean) => !value);
        } else {
          goNext();
        }
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
  }, [keyboardEnabled, autoAdvance, goNext, goPrevious]);

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
    goToIndex,
    goToSection,
  };
}
