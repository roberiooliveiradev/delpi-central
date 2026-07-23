import { useCallback, useEffect, useRef, useState } from "react";

import {
  getPlaylist as fetchPlaylist,
  listPlaylistHistory,
  restorePlaylistHistorySnapshot,
  type Playlist,
  type PlaylistHistoryPage,
} from "../api/tvDashboardApi";
import { HttpRequestError } from "../api/httpClient";
import type { DeckEditorSnapshot } from "../utils/deckEditorHistory";
import {
  clearDeckEditorHistory,
  DECK_EDITOR_HISTORY_POINTER_LIMIT,
  readDeckEditorHistory,
  writeDeckEditorHistory,
  type DeckEditorHistoryPointer,
} from "../utils/deckEditorHistoryPreferences";

type Options = {
  playlistId: string;
  getPlaylist: () => Playlist | null;
  getSelectedSlideId: () => string | null;
  getLiveComunicadoConfig: () => Record<string, unknown> | null;
  getComunicadoSlideId: () => string | null;
  applySnapshot: (snapshot: DeckEditorSnapshot) => void;
};

export function useDeckEditorHistory({
  playlistId,
  getSelectedSlideId,
  applySnapshot,
}: Options) {
  const pastRef = useRef<DeckEditorHistoryPointer[]>([]);
  const futureRef = useRef<DeckEditorHistoryPointer[]>([]);
  const currentRevisionRef = useRef<number | null>(null);
  const lastLocalRevisionRef = useRef<number | null>(null);
  const pendingRef = useRef(false);
  const restoringRef = useRef(false);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [historyEpoch, setHistoryEpoch] = useState(0);
  const [historyPage, setHistoryPage] = useState<PlaylistHistoryPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshAvailability = useCallback(() => {
    setCanUndo(pastRef.current.length > 0);
    setCanRedo(futureRef.current.length > 0);
  }, []);

  const persistStacks = useCallback(() => {
    if (!playlistId) return;
    if (pastRef.current.length === 0 && futureRef.current.length === 0) {
      clearDeckEditorHistory(playlistId);
      return;
    }
    writeDeckEditorHistory(playlistId, pastRef.current, futureRef.current);
  }, [playlistId]);

  const bumpHistoryEpoch = useCallback(() => {
    setHistoryEpoch((epoch) => epoch + 1);
  }, []);

  const loadHistory = useCallback(
    async (page = 1) => {
      setLoading(true);
      setError(null);
      try {
        const result = await listPlaylistHistory(playlistId, { page, pageSize: 10 });
        setHistoryPage(result);
        if (page === 1) {
          currentRevisionRef.current = result.currentRevision;
        }
        return result;
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Erro ao carregar histórico.");
        return null;
      } finally {
        setLoading(false);
      }
    },
    [playlistId],
  );

  useEffect(() => {
    const stored = readDeckEditorHistory(playlistId);
    pastRef.current = stored?.past ?? [];
    futureRef.current = stored?.future ?? [];
    pendingRef.current = false;
    refreshAvailability();
    void loadHistory(1);
  }, [loadHistory, playlistId, refreshAvailability]);

  const recordBeforeChange = useCallback(
    (_liveComunicadoOverride?: Record<string, unknown> | null) => {
      pendingRef.current = true;
    },
    [],
  );

  const confirmChange = useCallback(async () => {
    const pending = pendingRef.current;
    pendingRef.current = false;
    const refreshed = await loadHistory(1);
    if (!refreshed) return;
    lastLocalRevisionRef.current = refreshed.currentRevision;
    const captured = refreshed.items[0];
    if (pending && captured) {
      pastRef.current = [
        ...pastRef.current.slice(-(DECK_EDITOR_HISTORY_POINTER_LIMIT - 1)),
        { snapshotId: captured.snapshotId, revision: captured.revision },
      ];
      futureRef.current = [];
      refreshAvailability();
      persistStacks();
    }
  }, [loadHistory, persistStacks, refreshAvailability]);

  const cancelChange = useCallback(() => {
    pendingRef.current = false;
  }, []);

  const applyRestoredPlaylist = useCallback(
    (restoredPlaylist: Playlist) => {
      const currentSelection = getSelectedSlideId();
      const slides = restoredPlaylist.slides ?? [];
      const selectedSlideId =
        currentSelection && slides.some((slide) => slide.id === currentSelection)
          ? currentSelection
          : slides[0]?.id ?? null;
      applySnapshot({ playlist: restoredPlaylist, selectedSlideId });
      currentRevisionRef.current =
        restoredPlaylist.revision ?? restoredPlaylist.currentRevision ?? currentRevisionRef.current;
      bumpHistoryEpoch();
    },
    [applySnapshot, bumpHistoryEpoch, getSelectedSlideId],
  );

  const recoverFromConflict = useCallback(async () => {
    const remote = await fetchPlaylist(playlistId);
    const selected = getSelectedSlideId();
    applySnapshot({
      playlist: remote,
      selectedSlideId:
        selected && remote.slides?.some((slide) => slide.id === selected)
          ? selected
          : remote.slides?.[0]?.id ?? null,
    });
    pastRef.current = [];
    futureRef.current = [];
    pendingRef.current = false;
    refreshAvailability();
    persistStacks();
    await loadHistory(1);
    bumpHistoryEpoch();
  }, [
    applySnapshot,
    bumpHistoryEpoch,
    getSelectedSlideId,
    loadHistory,
    persistStacks,
    playlistId,
    refreshAvailability,
  ]);

  const restorePointer = useCallback(
    async (target: DeckEditorHistoryPointer) => {
      if (restoringRef.current) return null;
      const expectedRevision = currentRevisionRef.current ?? historyPage?.currentRevision;
      if (expectedRevision == null) {
        setError("A revisão atual ainda não foi carregada.");
        return null;
      }
      restoringRef.current = true;
      setRestoring(true);
      setError(null);
      try {
        const restoredPlaylist = await restorePlaylistHistorySnapshot(
          playlistId,
          target.snapshotId,
          expectedRevision,
        );
        applyRestoredPlaylist(restoredPlaylist);
        const refreshed = await loadHistory(1);
        lastLocalRevisionRef.current = refreshed?.currentRevision ?? null;
        const captured = refreshed?.items[0];
        return captured
          ? { snapshotId: captured.snapshotId, revision: captured.revision }
          : null;
      } catch (caught) {
        if (caught instanceof HttpRequestError && caught.status === 409) {
          await recoverFromConflict();
          setError("A programação foi atualizada por outra pessoa. A versão mais recente foi carregada.");
          return null;
        }
        setError(caught instanceof Error ? caught.message : "Erro ao restaurar revisão.");
        return null;
      } finally {
        restoringRef.current = false;
        setRestoring(false);
      }
    },
    [applyRestoredPlaylist, historyPage?.currentRevision, loadHistory, playlistId, recoverFromConflict],
  );

  const undo = useCallback(async () => {
    const previous = pastRef.current[pastRef.current.length - 1];
    if (!previous) return;
    const redoPointer = await restorePointer(previous);
    if (!redoPointer) return;
    pastRef.current.pop();
    futureRef.current.push(redoPointer);
    refreshAvailability();
    persistStacks();
  }, [persistStacks, refreshAvailability, restorePointer]);

  const redo = useCallback(async () => {
    const next = futureRef.current[futureRef.current.length - 1];
    if (!next) return;
    const undoPointer = await restorePointer(next);
    if (!undoPointer) return;
    futureRef.current.pop();
    pastRef.current = [
      ...pastRef.current.slice(-(DECK_EDITOR_HISTORY_POINTER_LIMIT - 1)),
      undoPointer,
    ];
    refreshAvailability();
    persistStacks();
  }, [persistStacks, refreshAvailability, restorePointer]);

  const restoreRevision = useCallback(
    async (snapshotId: string, revision: number) => {
      const undoPointer = await restorePointer({ snapshotId, revision });
      if (!undoPointer) return false;
      pastRef.current = [
        ...pastRef.current.slice(-(DECK_EDITOR_HISTORY_POINTER_LIMIT - 1)),
        undoPointer,
      ];
      futureRef.current = [];
      refreshAvailability();
      persistStacks();
      return true;
    },
    [persistStacks, refreshAvailability, restorePointer],
  );

  const handleRemoteUpdate = useCallback(async () => {
    const refreshed = await loadHistory(1);
    if (refreshed?.currentRevision == null) return;
    /*
     * Nunca zerar ponteiros de undo no eco WS / revisão alheia.
     * Apagar a pilha aqui fazia o histórico “sumir” após save ou sync —
     * o Ctrl+Z do slide já é local (`useComunicadoEditorHistory`).
     */
    if (pendingRef.current) {
      lastLocalRevisionRef.current = refreshed.currentRevision;
    }
  }, [loadHistory]);

  const reset = useCallback(() => {
    pastRef.current = [];
    futureRef.current = [];
    pendingRef.current = false;
    refreshAvailability();
    clearDeckEditorHistory(playlistId);
  }, [playlistId, refreshAvailability]);

  return {
    recordBeforeChange,
    confirmChange,
    cancelChange,
    undo,
    redo,
    canUndo,
    canRedo,
    historyEpoch,
    historyPage,
    loading,
    restoring,
    error,
    loadHistory,
    restoreRevision,
    handleRemoteUpdate,
    reset,
  };
}
