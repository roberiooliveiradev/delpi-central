import { useCallback, useEffect, useRef, useState, type MutableRefObject } from "react";

import type { MeetingAnnotationOverlayHandle } from "./MeetingAnnotationOverlay";
import type {
  MeetingAnnotationTool,
  MeetingInkStroke,
  MeetingNormPoint,
} from "./meetingAnnotationTypes";
import {
  applyMeetingInkStrokeEvent,
  clearMeetingInkForSlide,
} from "./meetingInkModel";
import type {
  PresentationMeetingInkClearEvent,
  PresentationMeetingInkStrokeEvent,
  PresentationMeetingLaserEvent,
} from "./usePresentationRealtime";

type RealtimeSend = (payload: Record<string, unknown>) => void;

export type UseMeetingAnnotationsOptions = {
  enabled: boolean;
  clientId: string | null;
  slideId: string;
  sendRef: MutableRefObject<RealtimeSend | null>;
};

/**
 * Estado efêmero de caneta/laser no modo reunião (só memória React).
 * Laser: paint no overlay (DOM/rAF); hook só publica WS throttled.
 * F5 limpa; late join não restaura ink.
 */
export function useMeetingAnnotations({
  enabled,
  clientId,
  slideId,
  sendRef,
}: UseMeetingAnnotationsOptions) {
  const [tool, setToolState] = useState<MeetingAnnotationTool>("none");
  const [strokes, setStrokes] = useState<MeetingInkStroke[]>([]);
  const overlayRef = useRef<MeetingAnnotationOverlayHandle>(null);

  const setTool = useCallback(
    (next: MeetingAnnotationTool) => {
      if (!enabled) {
        setToolState("none");
        return;
      }
      setToolState(next);
    },
    [enabled],
  );

  useEffect(() => {
    if (!enabled) setToolState("none");
  }, [enabled]);

  const applyRemoteLaser = useCallback(
    (event: PresentationMeetingLaserEvent) => {
      if (!enabled) return;
      if (clientId && event.clientId === clientId) return;
      overlayRef.current?.paintRemoteLaser({
        clientId: event.clientId,
        slideId: event.slideId,
        x: event.x,
        y: event.y,
        visible: event.visible,
      });
    },
    [clientId, enabled],
  );

  const applyRemoteInk = useCallback(
    (event: PresentationMeetingInkStrokeEvent) => {
      if (!enabled) return;
      if (clientId && event.clientId === clientId) return;
      setStrokes((prev) =>
        applyMeetingInkStrokeEvent(prev, {
          strokeId: event.strokeId,
          clientId: event.clientId,
          slideId: event.slideId,
          phase: event.phase,
          points: event.points,
        }),
      );
    },
    [clientId, enabled],
  );

  const applyRemoteInkClear = useCallback(
    (event: PresentationMeetingInkClearEvent) => {
      if (!enabled) return;
      setStrokes((prev) => clearMeetingInkForSlide(prev, event.slideId));
      overlayRef.current?.clearLasersForSlide(event.slideId);
    },
    [enabled],
  );

  /** Network-only laser publish (throttled in overlay). No React state update. */
  const publishLaserNetwork = useCallback(
    (event: { x: number; y: number; visible: boolean }) => {
      if (!enabled || !clientId || !slideId) return;
      sendRef.current?.({
        type: "meeting_laser",
        clientId,
        slideId,
        x: event.x,
        y: event.y,
        visible: event.visible,
      });
    },
    [clientId, enabled, sendRef, slideId],
  );

  const publishStroke = useCallback(
    (event: {
      strokeId: string;
      phase: "start" | "move" | "end";
      points: MeetingNormPoint[];
    }) => {
      if (!enabled || !clientId || !slideId) return;
      setStrokes((prev) =>
        applyMeetingInkStrokeEvent(prev, {
          strokeId: event.strokeId,
          clientId,
          slideId,
          phase: event.phase,
          points: event.points,
        }),
      );
      sendRef.current?.({
        type: "meeting_ink_stroke",
        clientId,
        slideId,
        strokeId: event.strokeId,
        phase: event.phase,
        points: event.points,
      });
    },
    [clientId, enabled, sendRef, slideId],
  );

  const clearInk = useCallback(() => {
    if (!enabled || !clientId || !slideId) return;
    setStrokes((prev) => clearMeetingInkForSlide(prev, slideId));
    overlayRef.current?.clearLasersForSlide(slideId);
    sendRef.current?.({
      type: "meeting_ink_clear",
      clientId,
      slideId,
    });
  }, [clientId, enabled, sendRef, slideId]);

  return {
    tool,
    setTool,
    strokes,
    overlayRef,
    clearInk,
    publishStroke,
    publishLaserNetwork,
    applyRemoteLaser,
    applyRemoteInk,
    applyRemoteInkClear,
  };
}
