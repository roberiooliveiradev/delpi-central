import {
  addSlide,
  deleteSlide,
  reorderSlides,
  updateSlide,
  type Playlist,
  type Slide,
} from "../api/tvDashboardApi";

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

function slidePayloadFromSlide(slide: Slide) {
  return {
    slideType: slide.slideType,
    title: slide.title,
    durationSec: slide.durationSec ?? undefined,
    nativeScreenKey: slide.nativeScreenKey ?? undefined,
    nativeConfig: slide.nativeConfig,
    externalUrl: slide.externalUrl ?? undefined,
    transitionStyle: slide.transitionStyle ?? undefined,
  };
}

function slidesNeedPatch(current: Slide, target: Slide): boolean {
  return (
    current.title !== target.title ||
    (current.durationSec ?? null) !== (target.durationSec ?? null) ||
    (current.nativeScreenKey ?? null) !== (target.nativeScreenKey ?? null) ||
    (current.externalUrl ?? null) !== (target.externalUrl ?? null) ||
    (current.transitionStyle ?? null) !== (target.transitionStyle ?? null) ||
    current.isActive !== target.isActive ||
    JSON.stringify(current.nativeConfig ?? {}) !== JSON.stringify(target.nativeConfig ?? {})
  );
}

/** Sincroniza API com o snapshot alvo e devolve playlist atualizada + seleção mapeada. */
export async function syncPlaylistToSnapshot(
  playlistId: string,
  current: Playlist,
  target: DeckEditorSnapshot,
): Promise<{ playlist: Playlist; selectedSlideId: string | null }> {
  const targetSlides = [...(target.playlist.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder);
  const currentSlides = [...(current.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder);
  const currentById = new Map(currentSlides.map((slide) => [slide.id, slide]));
  const idMap = new Map<string, string>();

  let workingSlides = [...currentSlides];

  for (const slide of workingSlides) {
    if (!targetSlides.some((item) => item.id === slide.id)) {
      await deleteSlide(playlistId, slide.id);
      workingSlides = workingSlides.filter((item) => item.id !== slide.id);
    }
  }

  for (const targetSlide of targetSlides) {
    if (currentById.has(targetSlide.id)) {
      idMap.set(targetSlide.id, targetSlide.id);
      const currentSlide = currentById.get(targetSlide.id)!;
      if (slidesNeedPatch(currentSlide, targetSlide)) {
        const updated = await updateSlide(playlistId, targetSlide.id, {
          title: targetSlide.title,
          durationSec: targetSlide.durationSec ?? undefined,
          nativeConfig: targetSlide.nativeConfig,
          externalUrl: targetSlide.externalUrl ?? undefined,
          isActive: targetSlide.isActive,
          transitionStyle: targetSlide.transitionStyle ?? undefined,
        });
        workingSlides = workingSlides.map((item) => (item.id === updated.id ? updated : item));
      }
      continue;
    }

    const created = await addSlide(playlistId, slidePayloadFromSlide(targetSlide));
    let restored = created;
    if (targetSlide.isActive !== created.isActive) {
      restored = await updateSlide(playlistId, created.id, { isActive: targetSlide.isActive });
    }
    idMap.set(targetSlide.id, restored.id);
    workingSlides.push(restored);
  }

  const reorderItems = targetSlides.map((slide, index) => ({
    id: idMap.get(slide.id) ?? slide.id,
    sortOrder: index,
  }));
  const reordered =
    reorderItems.length > 0
      ? await reorderSlides(playlistId, reorderItems)
      : { slides: [] as Slide[] };

  const mappedSelected = target.selectedSlideId
    ? idMap.get(target.selectedSlideId) ?? target.selectedSlideId
    : null;

  return {
    playlist: { ...target.playlist, slides: reordered.slides },
    selectedSlideId: mappedSelected,
  };
}
