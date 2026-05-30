import { useCallback, useEffect, useRef, useState } from "react";
import { io, type Socket } from "socket.io-client";

import { getAccessToken } from "../api/httpClient";
import type { AuditDetail } from "../api/audit5sApi";
import {
  AUDIT_5S_SOCKET_PATH,
  type AuditObservationTypingUpdatedEvent,
  type AuditPresenceUpdatedEvent,
  type AuditPresenceUser,
  type AuditResponseUpdatedEvent,
  type AuditTypingUser,
  type AuditUpdatedEvent,
} from "../constants/realtime";
import { getClientId } from "../utils/clientId";
import { getUserIdFromToken } from "../utils/jwt";
import { formatPersonName } from "../utils/formatPersonName";

type RealtimeNotice = {
  id: number;
  message: string;
  tone: "info" | "warning";
};

type Options = {
  auditId: string | null;
  enabled: boolean;
  onAuditSync: (audit: AuditDetail) => void;
  onResync: () => void;
};

const TYPING_REFRESH_MS = 2500;

export function useAudit5sRealtime({
  auditId,
  enabled,
  onAuditSync,
  onResync,
}: Options) {
  const socketRef = useRef<Socket | null>(null);
  const joinedAuditRef = useRef<string | null>(null);
  const activeTypingCriterionRef = useRef<string | null>(null);
  const typingRefreshTimerRef = useRef<number | null>(null);
  const auditIdRef = useRef<string | null>(auditId);
  const clientIdRef = useRef(getClientId());

  const [connected, setConnected] = useState(false);
  const [presence, setPresence] = useState<AuditPresenceUser[]>([]);
  const [observationTyping, setObservationTyping] = useState<
    Record<string, AuditTypingUser[]>
  >({});
  const [notice, setNotice] = useState<RealtimeNotice | null>(null);

  const onAuditSyncRef = useRef(onAuditSync);
  const onResyncRef = useRef(onResync);

  useEffect(() => {
    onAuditSyncRef.current = onAuditSync;
  }, [onAuditSync]);

  useEffect(() => {
    onResyncRef.current = onResync;
  }, [onResync]);

  useEffect(() => {
    auditIdRef.current = auditId;
  }, [auditId]);

  const clearTypingRefreshTimer = () => {
    if (typingRefreshTimerRef.current != null) {
      window.clearTimeout(typingRefreshTimerRef.current);
      typingRefreshTimerRef.current = null;
    }
  };

  const buildTypingPayload = (criterionId: string, auditIdValue: string) => ({
    auditId: auditIdValue,
    criterionId,
    clientId: clientIdRef.current,
  });

  const stopObservationTyping = useCallback((criterionId?: string) => {
    clearTypingRefreshTimer();

    const target = criterionId ?? activeTypingCriterionRef.current;
    const socket = socketRef.current;
    const currentAuditId = joinedAuditRef.current;

    if (socket?.connected && currentAuditId && target) {
      socket.emit("audit5s.observation.typing.stop", buildTypingPayload(target, currentAuditId));
    }

    activeTypingCriterionRef.current = null;
  }, []);

  const scheduleTypingRefresh = (criterionId: string) => {
    clearTypingRefreshTimer();
    typingRefreshTimerRef.current = window.setTimeout(() => {
      const socket = socketRef.current;
      const currentAuditId = joinedAuditRef.current;

      if (
        !socket?.connected ||
        !currentAuditId ||
        activeTypingCriterionRef.current !== criterionId
      ) {
        return;
      }

      socket.emit("audit5s.observation.typing", buildTypingPayload(criterionId, currentAuditId));
      scheduleTypingRefresh(criterionId);
    }, TYPING_REFRESH_MS);
  };

  const signalObservationTyping = useCallback((criterionId: string) => {
    const socket = socketRef.current;
    const currentAuditId = joinedAuditRef.current;
    if (!socket?.connected || !currentAuditId) return;

    if (
      activeTypingCriterionRef.current &&
      activeTypingCriterionRef.current !== criterionId
    ) {
      socket.emit(
        "audit5s.observation.typing.stop",
        buildTypingPayload(activeTypingCriterionRef.current, currentAuditId),
      );
    }

    activeTypingCriterionRef.current = criterionId;
    socket.emit("audit5s.observation.typing", buildTypingPayload(criterionId, currentAuditId));
    scheduleTypingRefresh(criterionId);
  }, []);

  const pushNotice = useCallback((message: string, tone: RealtimeNotice["tone"] = "info") => {
    setNotice({ id: Date.now(), message, tone });
  }, []);

  useEffect(() => {
    if (!enabled) {
      clearTypingRefreshTimer();
      activeTypingCriterionRef.current = null;
      setConnected(false);
      setPresence([]);
      setObservationTyping({});
      return;
    }

    const token = getAccessToken();
    if (!token) return;

    const socket = io(window.location.origin, {
      path: AUDIT_5S_SOCKET_PATH,
      transports: ["websocket", "polling"],
      reconnection: true,
      autoConnect: true,
      auth: { token },
    });

    socketRef.current = socket;

    const joinCurrentAudit = () => {
      const currentAuditId = auditIdRef.current;
      if (!currentAuditId) return;
      socket.emit("audit5s.join", { auditId: currentAuditId });
      joinedAuditRef.current = currentAuditId;
    };

    const handleConnect = () => {
      setConnected(true);
      joinCurrentAudit();
      onResyncRef.current();
    };

    const handleDisconnect = () => {
      setConnected(false);
      setPresence([]);
      setObservationTyping({});
      activeTypingCriterionRef.current = null;
      clearTypingRefreshTimer();
    };

    const handleResponseUpdated = (payload: AuditResponseUpdatedEvent) => {
      const currentAuditId = joinedAuditRef.current;
      if (!payload?.audit || !currentAuditId || payload.audit_id !== currentAuditId) {
        return;
      }

      onAuditSyncRef.current(payload.audit);

      const selfId = getUserIdFromToken(getAccessToken());
      if (selfId && payload.actor_user_id === selfId) {
        return;
      }

      pushNotice(
        `${formatPersonName(payload.actor_display_name) || payload.actor_display_name} atualizou um critério.`,
        "info",
      );
    };

    const handleAuditUpdated = (payload: AuditUpdatedEvent) => {
      const currentAuditId = joinedAuditRef.current;
      if (!payload?.audit || !currentAuditId || payload.audit_id !== currentAuditId) {
        return;
      }

      onAuditSyncRef.current(payload.audit);

      const selfId = getUserIdFromToken(getAccessToken());
      if (selfId && payload.actor_user_id === selfId) {
        return;
      }

      const labels: Record<string, string> = {
        evaluation_complete: "concluiu a avaliação",
        nc_created: "registrou uma NC",
        closed: "encerrou a auditoria",
      };
      const action = labels[payload.event_type] ?? "atualizou a auditoria";
      pushNotice(
        `${formatPersonName(payload.actor_display_name) || payload.actor_display_name} ${action}.`,
        "warning",
      );
    };

    const handlePresenceUpdated = (payload: AuditPresenceUpdatedEvent) => {
      const currentAuditId = joinedAuditRef.current;
      if (!currentAuditId || payload.audit_id !== currentAuditId) return;
      setPresence(payload.users ?? []);
    };

    const handleObservationTypingUpdated = (payload: AuditObservationTypingUpdatedEvent) => {
      const currentAuditId = joinedAuditRef.current;
      if (!currentAuditId || payload.audit_id !== currentAuditId) return;

      setObservationTyping((prev) => ({
        ...prev,
        [payload.criterion_id]: payload.users ?? [],
      }));
    };

    socket.on("connect", handleConnect);
    socket.on("disconnect", handleDisconnect);
    socket.on("audit5s.response.updated", handleResponseUpdated);
    socket.on("audit5s.audit.updated", handleAuditUpdated);
    socket.on("audit5s.presence.updated", handlePresenceUpdated);
    socket.on("audit5s.observation.typing.updated", handleObservationTypingUpdated);

    return () => {
      clearTypingRefreshTimer();
      activeTypingCriterionRef.current = null;

      if (joinedAuditRef.current) {
        socket.emit("audit5s.leave", { auditId: joinedAuditRef.current });
        joinedAuditRef.current = null;
      }

      socket.removeAllListeners();
      socket.disconnect();
      socketRef.current = null;
      setConnected(false);
      setPresence([]);
      setObservationTyping({});
    };
  }, [enabled, pushNotice]);

  useEffect(() => {
    const socket = socketRef.current;
    if (!socket || !enabled || !socket.connected || !auditId) return;

    if (joinedAuditRef.current === auditId) return;

    if (joinedAuditRef.current) {
      stopObservationTyping();
      socket.emit("audit5s.leave", { auditId: joinedAuditRef.current });
      setPresence([]);
      setObservationTyping({});
    }

    socket.emit("audit5s.join", { auditId });
    joinedAuditRef.current = auditId;
  }, [auditId, connected, enabled, stopObservationTyping]);

  const dismissNotice = useCallback(() => {
    setNotice(null);
  }, []);

  return {
    connected,
    presence,
    observationTyping,
    notice,
    dismissNotice,
    signalObservationTyping,
    stopObservationTyping,
  };
};
