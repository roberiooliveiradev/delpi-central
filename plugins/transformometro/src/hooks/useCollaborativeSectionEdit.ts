import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  acquireCollaborationLock,
  fetchCollaborationPresence,
  releaseCollaborationLock,
  sendCollaborationHeartbeat,
  type CollaborationEntityType,
  type CollaborationPresencePayload,
} from "../data/api/transformometroCollaborationApi";
import { useSectionEdit } from "./useSectionEdit";
import { useTransformometroRealtime } from "./useTransformometroRealtime";
import { COLLABORATION_SECTION_LABELS } from "../constants/collaborationSections";
import type { TransformometroEntityUpdatedEvent } from "../constants/realtime";
import { getUserIdFromToken } from "../utils/jwt";
import { isMatchingPresencePayload, presencePayloadEquals } from "../utils/collaborationPresence";
import { resolveCollaborativeEntityUpdate } from "../utils/collaborativeEntityUpdate";

const POLL_FALLBACK_MS = 30_000;
const RESYNC_FALLBACK_MS = 90_000;
const LOCK_HEARTBEAT_MS = 20_000;
const VIEW_HEARTBEAT_MS = 30_000;

type Options = {
  entityType: CollaborationEntityType;
  entityId: string;
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  onResync?: () => void;
};

export function useCollaborativeSectionEdit({
  entityType,
  entityId,
  getAccessToken,
  enabled = true,
  onResync,
}: Options) {
  const sectionEdit = useSectionEdit();
  const [presence, setPresence] = useState<CollaborationPresencePayload | null>(null);
  const [lockError, setLockError] = useState<string | null>(null);
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [resyncVersion, setResyncVersion] = useState(0);
  const [realtimeNotice, setRealtimeNotice] = useState<string | null>(null);
  const editingSectionRef = useRef<string | null>(null);
  const onResyncRef = useRef(onResync);
  const getAccessTokenRef = useRef(getAccessToken);

  useEffect(() => {
    onResyncRef.current = onResync;
  }, [onResync]);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const refreshPresence = useCallback(async () => {
    if (!enabled || !entityId) return;
    try {
      const data = await fetchCollaborationPresence(entityType, entityId, () =>
        getAccessTokenRef.current?.()
      );
      setPresence((current) => (presencePayloadEquals(current, data) ? current : data));
    } catch {
      /* mantém presença anterior em falha transitória de polling */
    }
  }, [enabled, entityId, entityType]);

  const applyPresencePayload = useCallback((payload: CollaborationPresencePayload) => {
    setPresence((current) => (presencePayloadEquals(current, payload) ? current : payload));
  }, []);

  const handlePresenceUpdated = useCallback(
    (payload: CollaborationPresencePayload) => {
      if (!isMatchingPresencePayload(payload, entityType, entityId)) {
        return;
      }
      applyPresencePayload(payload);
    },
    [applyPresencePayload, entityId, entityType]
  );

  const handleEntityUpdated = useCallback((event: TransformometroEntityUpdatedEvent) => {
    const token = getAccessTokenRef.current?.();
    const myUserId = getUserIdFromToken(token);
    const updatedSectionKey = event.sectionKey ?? null;
    const updatedSectionLabel = updatedSectionKey
      ? COLLABORATION_SECTION_LABELS[updatedSectionKey] ?? updatedSectionKey
      : null;

    const decision = resolveCollaborativeEntityUpdate({
      editingSectionKey: editingSectionRef.current,
      updatedSectionKey,
      updatedSectionLabel,
      actorUserId: event.actorUserId,
      myUserId,
    });

    if (decision.kind === "ignore_own") {
      return;
    }

    if (decision.kind === "block_editing_conflict") {
      setRealtimeNotice(decision.notice);
      return;
    }

    setResyncVersion((value) => value + 1);
    setRealtimeNotice(decision.notice);
    onResyncRef.current?.();
  }, []);

  const {
    connected: wsConnected,
    connectionError: wsConnectionError,
    requestPresence,
    sendHeartbeat,
    acquireLock: acquireLockViaWs,
    releaseLock: releaseLockViaWs,
    clearPresence,
  } = useTransformometroRealtime({
    entityType,
    entityId,
    getAccessToken,
    enabled,
    onPresenceUpdated: handlePresenceUpdated,
    onEntityUpdated: handleEntityUpdated,
    onRealtimeError: (message) => setLockError(message),
  });

  useEffect(() => {
    if (!enabled || !entityId) {
      setPresence(null);
      return;
    }
    if (wsConnected) {
      requestPresence();
      return;
    }
    void refreshPresence();
  }, [enabled, entityId, refreshPresence, requestPresence, wsConnected]);

  useEffect(() => {
    if (!enabled || !entityId || wsConnected) return;
    const timer = window.setInterval(() => void refreshPresence(), POLL_FALLBACK_MS);
    return () => window.clearInterval(timer);
  }, [enabled, entityId, refreshPresence, wsConnected]);

  useEffect(() => {
    if (!enabled || !entityId || wsConnected || !onResync) return;
    const timer = window.setInterval(() => {
      if (editingSectionRef.current) return;
      onResyncRef.current?.();
    }, RESYNC_FALLBACK_MS);
    return () => window.clearInterval(timer);
  }, [enabled, entityId, onResync, wsConnected]);

  const sendViewHeartbeat = useCallback(async () => {
    if (!enabled || !entityId) return;
    if (wsConnected) {
      sendHeartbeat("", "viewing");
      return;
    }
    await sendCollaborationHeartbeat(
      {
        entity_type: entityType,
        entity_id: entityId,
        section_key: "",
        mode: "viewing",
      },
      () => getAccessTokenRef.current?.()
    );
  }, [enabled, entityId, entityType, sendHeartbeat, wsConnected]);

  const sendEditHeartbeat = useCallback(
    async (sectionKey: string) => {
      if (!enabled || !entityId) return;
      if (wsConnected) {
        sendHeartbeat(sectionKey, "editing");
        return;
      }
      await sendCollaborationHeartbeat(
        {
          entity_type: entityType,
          entity_id: entityId,
          section_key: sectionKey,
          mode: "editing",
        },
        () => getAccessTokenRef.current?.()
      );
    },
    [enabled, entityId, entityType, sendHeartbeat, wsConnected]
  );

  useEffect(() => {
    if (!enabled || !entityId || editingSection) return;
    void sendViewHeartbeat();
    const timer = window.setInterval(() => {
      void sendViewHeartbeat();
    }, VIEW_HEARTBEAT_MS);
    return () => window.clearInterval(timer);
  }, [enabled, entityId, editingSection, sendViewHeartbeat]);

  useEffect(() => {
    if (!enabled || !entityId || !editingSection) return;
    void sendEditHeartbeat(editingSection);
    const timer = window.setInterval(() => {
      void sendEditHeartbeat(editingSection);
    }, LOCK_HEARTBEAT_MS);
    return () => window.clearInterval(timer);
  }, [enabled, entityId, editingSection, sendEditHeartbeat]);

  const releaseCurrentLock = useCallback(async () => {
    const section = editingSectionRef.current;
    if (!section || !entityId) return;
    editingSectionRef.current = null;
    setEditingSection(null);
    try {
      if (wsConnected) {
        releaseLockViaWs(section);
      } else {
        await releaseCollaborationLock(
          { entity_type: entityType, entity_id: entityId, section_key: section },
          () => getAccessTokenRef.current?.()
        );
      }
    } catch {
      /* noop */
    }
    if (!wsConnected) {
      void refreshPresence();
    }
  }, [entityId, entityType, refreshPresence, releaseLockViaWs, wsConnected]);

  const startEdit = useCallback(
    async (key: string) => {
      setLockError(null);
      if (!enabled || !entityId) {
        sectionEdit.startEdit(key);
        return true;
      }
      try {
        let acquired = false;

        if (wsConnected) {
          const result = await acquireLockViaWs(key);
          if (result == null) {
            const httpResult = await acquireCollaborationLock(
              { entity_type: entityType, entity_id: entityId, section_key: key },
              () => getAccessTokenRef.current?.()
            );
            acquired = httpResult.acquired !== false;
          } else {
            acquired = result.acquired !== false;
          }
        } else {
          const httpResult = await acquireCollaborationLock(
            { entity_type: entityType, entity_id: entityId, section_key: key },
            () => getAccessTokenRef.current?.()
          );
          acquired = httpResult.acquired !== false;
        }

        if (!acquired) {
          setLockError("Outro usuário está editando esta seção agora.");
          if (!wsConnected) {
            void refreshPresence();
          } else {
            requestPresence();
          }
          return false;
        }

        editingSectionRef.current = key;
        setEditingSection(key);
        sectionEdit.startEdit(key);
        if (!wsConnected) {
          void refreshPresence();
        } else {
          sendHeartbeat(key, "editing");
        }
        return true;
      } catch (err) {
        setLockError(err instanceof Error ? err.message : "Não foi possível travar a seção.");
        return false;
      }
    },
    [
      acquireLockViaWs,
      enabled,
      entityId,
      entityType,
      refreshPresence,
      requestPresence,
      sectionEdit,
      sendHeartbeat,
      wsConnected,
    ]
  );

  const cancelEdit = useCallback(
    (key: string) => {
      sectionEdit.cancelEdit(key);
      if (editingSectionRef.current === key) {
        void releaseCurrentLock();
      }
    },
    [releaseCurrentLock, sectionEdit]
  );

  const stopEdit = useCallback(
    (key: string) => {
      sectionEdit.stopEdit(key);
      if (editingSectionRef.current === key) {
        void releaseCurrentLock();
      }
    },
    [releaseCurrentLock, sectionEdit]
  );

  useEffect(() => {
    return () => {
      clearPresence();
      void releaseCurrentLock();
    };
  }, [clearPresence, releaseCurrentLock]);

  const presenceSummary = useMemo(() => {
    if (!presence) return null;
    const editors = presence.editors.filter((item) => item.lock_active);
    const viewers = presence.viewers.filter((item) => item.mode === "viewing");
    return { editors, viewers };
  }, [presence]);

  return useMemo(
    () => ({
      ...sectionEdit,
      startEdit,
      cancelEdit,
      stopEdit,
      presence,
      presenceSummary,
      lockError,
      clearLockError: () => setLockError(null),
      refreshPresence,
      wsConnected,
      wsConnectionError,
      resyncVersion,
      realtimeNotice,
      clearRealtimeNotice: () => setRealtimeNotice(null),
      handleRemoteEntityUpdate: handleEntityUpdated,
    }),
    [
      cancelEdit,
      lockError,
      presence,
      presenceSummary,
      realtimeNotice,
      refreshPresence,
      resyncVersion,
      sectionEdit,
      startEdit,
      stopEdit,
      handleEntityUpdated,
      wsConnected,
      wsConnectionError,
    ]
  );
}
