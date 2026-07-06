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
import { getUserIdFromToken } from "../utils/jwt";

const POLL_MS = 12_000;
const LOCK_HEARTBEAT_MS = 20_000;
const VIEW_HEARTBEAT_MS = 30_000;
const RESYNC_FALLBACK_MS = 60_000;

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

  useEffect(() => {
    onResyncRef.current = onResync;
  }, [onResync]);

  const refreshPresence = useCallback(async () => {
    if (!enabled || !entityId) return;
    try {
      const data = await fetchCollaborationPresence(entityType, entityId, getAccessToken);
      setPresence(data);
    } catch {
      setPresence(null);
    }
  }, [enabled, entityId, entityType, getAccessToken]);

  const handleEntityUpdated = useCallback(
    (event: { actorUserId?: string | null; sectionKey?: string | null }) => {
      const token = getAccessToken?.();
      const myUserId = getUserIdFromToken(token);
      if (event.actorUserId && myUserId && event.actorUserId === myUserId) {
        return;
      }

      if (editingSectionRef.current) {
        setRealtimeNotice(
          "Outro usuário alterou dados desta entidade. Salve ou cancele a edição e recarregue para ver as mudanças."
        );
        return;
      }

      setResyncVersion((value) => value + 1);
      setRealtimeNotice("Dados atualizados por outro usuário.");
      onResyncRef.current?.();
    },
    [getAccessToken]
  );

  const { connected: wsConnected, connectionError: wsConnectionError } = useTransformometroRealtime({
    entityType,
    entityId,
    getAccessToken,
    enabled,
    onPresenceUpdated: setPresence,
    onEntityUpdated: handleEntityUpdated,
  });

  useEffect(() => {
    if (!enabled || !entityId || wsConnected) return;
    void refreshPresence();
    const timer = window.setInterval(() => void refreshPresence(), POLL_MS);
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

  useEffect(() => {
    if (!enabled || !entityId || editingSection) return;
    void sendCollaborationHeartbeat(
      {
        entity_type: entityType,
        entity_id: entityId,
        section_key: "",
        mode: "viewing",
      },
      getAccessToken
    );
    const timer = window.setInterval(() => {
      void sendCollaborationHeartbeat(
        {
          entity_type: entityType,
          entity_id: entityId,
          section_key: "",
          mode: "viewing",
        },
        getAccessToken
      );
    }, VIEW_HEARTBEAT_MS);
    return () => window.clearInterval(timer);
  }, [enabled, entityId, entityType, editingSection, getAccessToken]);

  useEffect(() => {
    if (!enabled || !entityId || !editingSection) return;
    void sendCollaborationHeartbeat(
      {
        entity_type: entityType,
        entity_id: entityId,
        section_key: editingSection,
        mode: "editing",
      },
      getAccessToken
    );
    const timer = window.setInterval(() => {
      void sendCollaborationHeartbeat(
        {
          entity_type: entityType,
          entity_id: entityId,
          section_key: editingSection,
          mode: "editing",
        },
        getAccessToken
      );
    }, LOCK_HEARTBEAT_MS);
    return () => window.clearInterval(timer);
  }, [enabled, entityId, entityType, editingSection, getAccessToken]);

  const releaseCurrentLock = useCallback(async () => {
    const section = editingSectionRef.current;
    if (!section || !entityId) return;
    editingSectionRef.current = null;
    setEditingSection(null);
    try {
      await releaseCollaborationLock(
        { entity_type: entityType, entity_id: entityId, section_key: section },
        getAccessToken
      );
    } catch {
      /* noop */
    }
    void refreshPresence();
  }, [entityId, entityType, getAccessToken, refreshPresence]);

  const startEdit = useCallback(
    async (key: string) => {
      setLockError(null);
      if (!enabled || !entityId) {
        sectionEdit.startEdit(key);
        return true;
      }
      try {
        const result = await acquireCollaborationLock(
          { entity_type: entityType, entity_id: entityId, section_key: key },
          getAccessToken
        );
        if (result.acquired === false) {
          setLockError("Outro usuário está editando esta seção agora.");
          void refreshPresence();
          return false;
        }
        editingSectionRef.current = key;
        setEditingSection(key);
        sectionEdit.startEdit(key);
        void refreshPresence();
        return true;
      } catch (err) {
        setLockError(err instanceof Error ? err.message : "Não foi possível travar a seção.");
        return false;
      }
    },
    [enabled, entityId, entityType, getAccessToken, refreshPresence, sectionEdit]
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
      void releaseCurrentLock();
    };
  }, [releaseCurrentLock]);

  const presenceSummary = useMemo(() => {
    if (!presence) return null;
    const editors = presence.editors.filter((item) => item.lock_active);
    const viewers = presence.viewers.filter((item) => item.mode === "viewing");
    return { editors, viewers };
  }, [presence]);

  return {
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
  };
}
