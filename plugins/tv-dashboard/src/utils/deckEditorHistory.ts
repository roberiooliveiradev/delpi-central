import type { Playlist } from "../api/tvDashboardApi";

export type DeckEditorSnapshot = {
  playlist: Playlist;
  selectedSlideId: string | null;
};

const HISTORY_LIMIT = 50;

/** Cópia profunda de nativeConfig — shallow permitia mutar o passado ao editar blocks/style. */
export function cloneNativeConfig(
  nativeConfig: Record<string, unknown> | null | undefined,
): Record<string, unknown> | null | undefined {
  if (nativeConfig == null) return nativeConfig;
  return JSON.parse(JSON.stringify(nativeConfig)) as Record<string, unknown>;
}

export function cloneDeckEditorSnapshot(snapshot: DeckEditorSnapshot): DeckEditorSnapshot {
  return {
    selectedSlideId: snapshot.selectedSlideId,
    playlist: {
      ...snapshot.playlist,
      slides: (snapshot.playlist.slides ?? []).map((slide) => ({
        ...slide,
        nativeConfig: cloneNativeConfig(slide.nativeConfig) ?? undefined,
      })),
    },
  };
}

export function buildDeckEditorSnapshot(
  playlist: Playlist,
  selectedSlideId: string | null,
  liveComunicadoConfig?: Record<string, unknown> | null,
  comunicadoSlideId?: string | null,
): DeckEditorSnapshot {
  const slides = (playlist.slides ?? []).map((slide) => {
    if (liveComunicadoConfig && comunicadoSlideId && slide.id === comunicadoSlideId) {
      return { ...slide, nativeConfig: cloneNativeConfig(liveComunicadoConfig) ?? {} };
    }
    return {
      ...slide,
      nativeConfig: cloneNativeConfig(slide.nativeConfig) ?? undefined,
    };
  });
  return {
    selectedSlideId,
    playlist: { ...playlist, slides },
  };
}

/**
 * Mutação vinda do servidor (copiloto/outro editor) deve virar passo de undo:
 * o snapshot capturado pelo BFF é o estado ANTES da mutação, então restaurá-lo
 * desfaz a alteração remota — vale para qualquer rota CRUD, não só canvas.
 * Eco do próprio save (revisão já conhecida) e restore em curso não empilham.
 */
export function shouldStackRemoteDeckUndo(params: {
  previousRevision: number | null;
  currentRevision: number;
  lastLocalRevision: number | null;
  pendingLocalChanges: number;
  restoring: boolean;
}): boolean {
  const {
    previousRevision,
    currentRevision,
    lastLocalRevision,
    pendingLocalChanges,
    restoring,
  } = params;
  if (restoring || pendingLocalChanges > 0) return false;
  if (previousRevision == null) return false;
  if (currentRevision <= previousRevision) return false;
  if (lastLocalRevision != null && currentRevision <= lastLocalRevision) return false;
  return true;
}

/**
 * Ponteiro de undo para uma mutação remota: prefere o snapshot da revisão que o
 * usuário via (desfaz o turno inteiro da IA, mesmo com várias ops) e cai na
 * entrada mais recente quando esse baseline não está na página do histórico.
 */
export function pickRemoteUndoPointer<T extends { snapshotId: string; revision: number }>(
  items: readonly T[],
  previousRevision: number | null,
): { snapshotId: string; revision: number } | null {
  if (items.length === 0) return null;
  const baseline =
    previousRevision == null
      ? undefined
      : items.find((item) => item.revision === previousRevision);
  const chosen = baseline ?? items[0];
  return { snapshotId: chosen.snapshotId, revision: chosen.revision };
}

export function pushDeckHistory(
  past: DeckEditorSnapshot[],
  entry: DeckEditorSnapshot,
): DeckEditorSnapshot[] {
  return [...past.slice(-(HISTORY_LIMIT - 1)), cloneDeckEditorSnapshot(entry)];
}
