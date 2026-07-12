import { useCallback, useRef, useState, type MutableRefObject } from "react";

import {
  parseComunicadoConfig,
  serializeComunicadoConfig,
  type ComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import type { DeckEditorHistoryContextValue } from "../../context/deckEditorHistoryContext";

export const COMUNICADO_EDITOR_HISTORY_LIMIT = 50;

export function snapshotConfig(config: ComunicadoConfig): ComunicadoConfig {
  return parseComunicadoConfig(serializeComunicadoConfig(config));
}

type Options = {
  configRef: MutableRefObject<ComunicadoConfig>;
  applyConfig: (next: ComunicadoConfig) => void;
  deckHistory: DeckEditorHistoryContextValue | null;
};

export function useComunicadoEditorHistory({
  configRef,
  applyConfig,
  deckHistory,
}: Options) {
  const [historyTick, setHistoryTick] = useState(0);
  const pastRef = useRef<ComunicadoConfig[]>([]);
  const futureRef = useRef<ComunicadoConfig[]>([]);

  const pushPast = useCallback((snapshot: ComunicadoConfig) => {
    pastRef.current = [
      ...pastRef.current.slice(-(COMUNICADO_EDITOR_HISTORY_LIMIT - 1)),
      snapshot,
    ];
    futureRef.current = [];
    setHistoryTick((tick) => tick + 1);
  }, []);

  const commitWithHistory = useCallback(
    (next: ComunicadoConfig) => {
      if (deckHistory) {
        deckHistory.recordBeforeChange();
      } else {
        pushPast(snapshotConfig(configRef.current));
      }
      applyConfig(next);
    },
    [applyConfig, configRef, deckHistory, pushPast],
  );

  const undo = useCallback(() => {
    if (deckHistory) {
      deckHistory.undo();
      return;
    }
    const previous = pastRef.current.pop();
    if (!previous) return;
    futureRef.current.push(snapshotConfig(configRef.current));
    applyConfig(previous);
    setHistoryTick((tick) => tick + 1);
  }, [applyConfig, configRef, deckHistory]);

  const redo = useCallback(() => {
    if (deckHistory) {
      deckHistory.redo();
      return;
    }
    const next = futureRef.current.pop();
    if (!next) return;
    pastRef.current.push(snapshotConfig(configRef.current));
    applyConfig(next);
    setHistoryTick((tick) => tick + 1);
  }, [applyConfig, configRef, deckHistory]);

  const resetLocalHistory = useCallback(() => {
    pastRef.current = [];
    futureRef.current = [];
    setHistoryTick((tick) => tick + 1);
  }, []);

  const canUndo = deckHistory ? deckHistory.canUndo : pastRef.current.length > 0;
  const canRedo = deckHistory ? deckHistory.canRedo : futureRef.current.length > 0;
  void historyTick;

  return {
    pastRef,
    futureRef,
    historyTick,
    setHistoryTick,
    pushPast,
    commitWithHistory,
    undo,
    redo,
    canUndo,
    canRedo,
    resetLocalHistory,
    snapshotConfig,
  };
}
