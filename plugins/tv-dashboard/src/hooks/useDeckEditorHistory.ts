import { useCallback, useEffect, useRef, useState } from "react";

import type { Playlist } from "../api/tvDashboardApi";
import {
  buildDeckEditorSnapshot,
  cloneDeckEditorSnapshot,
  pushDeckHistory,
  syncPlaylistToSnapshot,
  type DeckEditorSnapshot,
} from "../utils/deckEditorHistory";
import {
  clearDeckEditorHistory,
  readDeckEditorHistory,
  writeDeckEditorHistory,
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
  getPlaylist,
  getSelectedSlideId,
  getLiveComunicadoConfig,
  getComunicadoSlideId,
  applySnapshot,
}: Options) {
  const pastRef = useRef<DeckEditorSnapshot[]>([]);
  const futureRef = useRef<DeckEditorSnapshot[]>([]);
  const syncingRef = useRef(false);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [historyEpoch, setHistoryEpoch] = useState(0);

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

  useEffect(() => {
    const stored = readDeckEditorHistory(playlistId);
    pastRef.current = stored?.past ?? [];
    futureRef.current = stored?.future ?? [];
    refreshAvailability();
  }, [playlistId, refreshAvailability]);

  const captureCurrent = useCallback((): DeckEditorSnapshot | null => {
    const playlist = getPlaylist();
    if (!playlist) return null;
    return buildDeckEditorSnapshot(
      playlist,
      getSelectedSlideId(),
      getLiveComunicadoConfig(),
      getComunicadoSlideId(),
    );
  }, [getComunicadoSlideId, getLiveComunicadoConfig, getPlaylist, getSelectedSlideId]);

  const recordBeforeChange = useCallback(
    (liveComunicadoOverride?: Record<string, unknown> | null) => {
      if (syncingRef.current) return;
      const playlist = getPlaylist();
      if (!playlist) return;
      const snapshot = buildDeckEditorSnapshot(
        playlist,
        getSelectedSlideId(),
        liveComunicadoOverride ?? getLiveComunicadoConfig(),
        getComunicadoSlideId(),
      );
      pastRef.current = pushDeckHistory(pastRef.current, snapshot);
      futureRef.current = [];
      refreshAvailability();
      persistStacks();
    },
    [
      getComunicadoSlideId,
      getLiveComunicadoConfig,
      getPlaylist,
      getSelectedSlideId,
      persistStacks,
      refreshAvailability,
    ],
  );

  const applyWithSync = useCallback(
    async (snapshot: DeckEditorSnapshot) => {
      const current = getPlaylist();
      if (!current) return;
      syncingRef.current = true;
      try {
        const result = await syncPlaylistToSnapshot(playlistId, current, snapshot);
        applySnapshot({
          playlist: result.playlist,
          selectedSlideId: result.selectedSlideId,
        });
        // Epoch depois do snapshot: o editor aceita o value restaurado no mesmo ciclo.
        bumpHistoryEpoch();
      } finally {
        syncingRef.current = false;
      }
    },
    [applySnapshot, bumpHistoryEpoch, getPlaylist, playlistId],
  );

  const undo = useCallback(() => {
    const previous = pastRef.current.pop();
    if (!previous) return;
    const current = captureCurrent();
    if (current) {
      futureRef.current.push(cloneDeckEditorSnapshot(current));
    }
    void applyWithSync(previous);
    refreshAvailability();
    persistStacks();
  }, [applyWithSync, captureCurrent, persistStacks, refreshAvailability]);

  const redo = useCallback(() => {
    const next = futureRef.current.pop();
    if (!next) return;
    const current = captureCurrent();
    if (current) {
      pastRef.current = pushDeckHistory(pastRef.current, current);
    }
    void applyWithSync(next);
    refreshAvailability();
    persistStacks();
  }, [applyWithSync, captureCurrent, persistStacks, refreshAvailability]);

  const reset = useCallback(() => {
    pastRef.current = [];
    futureRef.current = [];
    refreshAvailability();
    clearDeckEditorHistory(playlistId);
  }, [playlistId, refreshAvailability]);

  return {
    recordBeforeChange,
    undo,
    redo,
    canUndo,
    canRedo,
    historyEpoch,
    reset,
  };
}
