import { useCallback, useRef, useState, type MutableRefObject } from "react";

import {
  parseComunicadoConfig,
  serializeComunicadoConfig,
  type ComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import type { DeckEditorHistoryContextValue } from "../../context/deckEditorHistoryContext";
import { fingerprintComunicadoValue } from "./comunicadoEditorValueSync";

export const COMUNICADO_EDITOR_HISTORY_LIMIT = 50;

export function snapshotConfig(config: ComunicadoConfig): ComunicadoConfig {
  return parseComunicadoConfig(serializeComunicadoConfig(config));
}

/**
 * Runtime-only presentation state is intentionally excluded from persisted snapshots,
 * but a backend PresentationMutation ack may refresh it without changing authoring.
 * Keep a narrow fingerprint so those acks are not mistaken for no-op history commits.
 */
export function fingerprintComunicadoRuntime(config: ComunicadoConfig): string {
  const blocks = (config.blocks ?? []).map((block) => {
    const runtime = block as unknown as Record<string, unknown>;
    return {
      id: block.id,
      resolved: runtime.resolved ?? null,
      resolvedBySourceId: runtime.resolvedBySourceId ?? null,
      serverCanvasTableProjectionApplied:
        runtime.serverCanvasTableProjectionApplied ?? null,
      serverProjectionApplied: runtime.serverProjectionApplied ?? null,
      serverDisplayApplied: runtime.serverDisplayApplied ?? null,
      presentationStale: runtime.presentationStale ?? null,
    };
  });
  return JSON.stringify(blocks);
}

type Options = {
  configRef: MutableRefObject<ComunicadoConfig>;
  applyConfig: (next: ComunicadoConfig, options?: { persist?: boolean }) => void;
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

  /**
   * Undo/redo do slide é sempre local e imediato.
   * `deckHistory` só registra ponteiro de revisão no servidor (painel / eco);
   * não pode bloquear Ctrl+Z até o save nem apagar a pilha no WS.
   *
   * Authoring e runtime são deliberadamente separados:
   * - history/persist usam snapshot serializado (sem `resolved`);
   * - o editor aplica o `next` original para preservar display* materializado
   *   pelo backend.
   *
   * Um ack pode ter o mesmo authoring do preview otimista e ainda trazer um
   * `resolved` novo. Esse caso NÃO é no-op: aplica runtime sem criar undo nem
   * disparar autosave.
   */
  const commitWithHistory = useCallback(
    (next: ComunicadoConfig) => {
      const before = snapshotConfig(configRef.current);
      const after = snapshotConfig(next);
      const beforeAuthoring = fingerprintComunicadoValue(
        serializeComunicadoConfig(before),
      );
      const afterAuthoring = fingerprintComunicadoValue(
        serializeComunicadoConfig(after),
      );

      if (beforeAuthoring === afterAuthoring) {
        if (
          fingerprintComunicadoRuntime(configRef.current) !==
          fingerprintComunicadoRuntime(next)
        ) {
          applyConfig(next, { persist: false });
        }
        return;
      }

      pushPast(before);
      deckHistory?.recordBeforeChange();
      // Preserve ephemeral backend materialization on the live editor model.
      // applyConfig serializes before onChange, so runtime fields are still not persisted.
      applyConfig(next);
    },
    [applyConfig, configRef, deckHistory, pushPast],
  );

  const undo = useCallback(() => {
    const previous = pastRef.current.pop();
    if (!previous) return;
    futureRef.current.push(snapshotConfig(configRef.current));
    applyConfig(previous);
    setHistoryTick((tick) => tick + 1);
  }, [applyConfig, configRef]);

  const redo = useCallback(() => {
    const next = futureRef.current.pop();
    if (!next) return;
    pastRef.current.push(snapshotConfig(configRef.current));
    applyConfig(next);
    setHistoryTick((tick) => tick + 1);
  }, [applyConfig, configRef]);

  const resetLocalHistory = useCallback(() => {
    pastRef.current = [];
    futureRef.current = [];
    setHistoryTick((tick) => tick + 1);
  }, []);

  const canUndo = pastRef.current.length > 0;
  const canRedo = futureRef.current.length > 0;
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
