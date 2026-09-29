import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchRunTimeline, type RunTimeline } from "./api";
import { serverClockOffsetMs, serverNowMs } from "./runTimeline";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";

/** Razões que alteram a timeline — `pieces_updated` propositalmente fora. */
const TIMELINE_REASONS = new Set([
  "run_started",
  "run_paused",
  "run_resumed",
  "run_stopped",
  "downtime_classified",
]);

type Options = {
  token: string;
  sessionToken: string | null;
  runId: string | null;
  branch?: string | null;
  workCenter?: string | null;
  runRealtimeEvent?: MachineLoadRealtimeEvent | null;
  realtimeConnected?: boolean;
};

/**
 * Timeline do run com reconciliação por WebSocket (single-flight):
 * no máximo um GET em voo; sinal novo durante fetch agenda uma reconciliação.
 */
export function useRunTimeline({
  token,
  sessionToken,
  runId,
  branch = null,
  workCenter = null,
  runRealtimeEvent = null,
  realtimeConnected = false,
}: Options) {
  const [timeline, setTimeline] = useState<RunTimeline | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);
  const pendingRef = useRef(false);
  const requestRef = useRef({ token, sessionToken, runId });

  useEffect(() => {
    requestRef.current = { token, sessionToken, runId };
  }, [token, sessionToken, runId]);

  const refresh = useCallback(async () => {
    if (inFlightRef.current) {
      pendingRef.current = true;
      return;
    }
    inFlightRef.current = true;
    try {
      do {
        pendingRef.current = false;
        const request = requestRef.current;
        if (!request.runId || !request.sessionToken) {
          setTimeline(null);
          continue;
        }
        try {
          const next = await fetchRunTimeline(
            request.token,
            request.sessionToken,
            request.runId,
          );
          const current = requestRef.current;
          if (
            current.runId === request.runId &&
            current.sessionToken === request.sessionToken
          ) {
            setTimeline(next);
            setError(null);
          }
        } catch (err) {
          setError(
            err instanceof Error ? err.message : "Linha do tempo indisponível.",
          );
        }
      } while (pendingRef.current);
    } finally {
      inFlightRef.current = false;
    }
  }, []);

  // Carga inicial / troca de run.
  useEffect(() => {
    void refresh();
  }, [refresh, runId, sessionToken]);

  // Eventos de lifecycle/classificação disparam reconciliação coalescida.
  useEffect(() => {
    const scoped =
      (!branch || !runRealtimeEvent?.branch || runRealtimeEvent.branch === branch) &&
      (!workCenter ||
        !runRealtimeEvent?.workCenter ||
        runRealtimeEvent.workCenter === workCenter) &&
      (!runRealtimeEvent?.runId || runRealtimeEvent.runId === runId);
    if (
      runRealtimeEvent?.type === "production_run_updated" &&
      TIMELINE_REASONS.has(runRealtimeEvent.reason) &&
      scoped
    ) {
      void refresh();
    }
  }, [runRealtimeEvent, runId, branch, workCenter, refresh]);

  // Reconexão do WS: uma reconciliação HTTP, mesmo princípio do run.
  const wasConnectedRef = useRef(realtimeConnected);
  useEffect(() => {
    const was = wasConnectedRef.current;
    wasConnectedRef.current = realtimeConnected;
    if (!was && realtimeConnected) void refresh();
  }, [realtimeConnected, refresh]);

  const offsetMs = useMemo(
    () => (timeline ? serverClockOffsetMs(timeline.referenceAt, Date.now()) : 0),
    [timeline],
  );

  const serverNow = useCallback(() => serverNowMs(Date.now(), offsetMs), [offsetMs]);

  return { timeline, error, refresh, serverNow, offsetMs };
}
