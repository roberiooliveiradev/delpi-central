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

export function pushDeckHistory(
  past: DeckEditorSnapshot[],
  entry: DeckEditorSnapshot,
): DeckEditorSnapshot[] {
  return [...past.slice(-(HISTORY_LIMIT - 1)), cloneDeckEditorSnapshot(entry)];
}
