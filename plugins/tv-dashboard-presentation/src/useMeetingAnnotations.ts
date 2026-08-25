import { useCallback, useEffect, useState, type MutableRefObject } from "react";

import type {
  MeetingAnnotationTool,
  MeetingInkStroke,
  MeetingLaserState,
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
  const [lasers, setLasers] = useState<MeetingLaserState[]>([]);

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

  useEffect(() => {
    // Troca de slide: ink/laser são efêmeros por tela (sem restore).
    setStrokes([]);
    setLasers([]);
  }, [slideId]);

  const applyRemoteLaser = useCallback(
    (event: PresentationMeetingLaserEvent) => {
      if (!enabled) return;
      if (clientId && event.clientId === clientId) return;
      setLasers((prev) => {
        const without = prev.filter((laser) => laser.clientId !== event.clientId);
        if (!event.visible) return without;
        return [
          ...without,
          {
            clientId: event.clientId,
            slideId: event.slideId,
            x: event.x,
            y: event.y,
            visible: true,
          },
        ];
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
      setLasers((prev) =>
        prev.filter((laser) => !(laser.slideId === event.slideId && laser.visible)),
      );
    },
    [enabled],
  );

  const publishLaser = useCallback(
    (event: { x: number; y: number; visible: boolean }) => {
      if (!enabled || !clientId || !slideId) return;
      setLasers((prev) => {
        const without = prev.filter((laser) => laser.clientId !== clientId);
        if (!event.visible) return without;
        return [
          ...without,
          {
            clientId,
            slideId,
            x: event.x,
            y: event.y,
            visible: true,
          },
        ];
      });
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
    setLasers((prev) => prev.filter((laser) => laser.slideId !== slideId));
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
    lasers,
    clearInk,
    publishStroke,
    publishLaser,
    applyRemoteLaser,
    applyRemoteInk,
    applyRemoteInkClear,
  };
}
