import type { PresentationPayload, Playlist, Slide } from "../api/tvDashboardApi";

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

function mergeLiveBlocksOntoServerData(
  liveConfig: Record<string, unknown>,
  serverData: Record<string, unknown>,
): Record<string, unknown> {
  const liveBlocks = Array.isArray(liveConfig.blocks) ? liveConfig.blocks : null;
  const serverBlocks = Array.isArray(serverData.blocks) ? serverData.blocks : [];
  const serverById = new Map<string, Record<string, unknown>>();
  for (const block of serverBlocks) {
    if (isRecord(block) && typeof block.id === "string") {
      serverById.set(block.id, block);
    }
  }

  const mergedBlocks = liveBlocks
    ? liveBlocks.map((block) => {
        if (!isRecord(block) || typeof block.id !== "string") return block;
        const server = serverById.get(block.id);
        if (!server) return block;
        return {
          ...server,
          ...block,
          // Live manda layout/binding; resolved do servidor se o live ainda não tem.
          resolved: block.resolved ?? server.resolved,
        };
      })
    : serverBlocks;

  return {
    ...serverData,
    ...liveConfig,
    blocks: mergedBlocks,
    // Master enriquecido (URLs) do servidor se o live não trouxer.
    master: liveConfig.master ?? serverData.master,
  };
}

/**
 * Sobreposição do nativeConfig local (shell do editor) no preview-payload do servidor.
 * Mesma regra do filmstrip: durante a edição o servidor fica stale.
 */
export function overlayLiveCustomMessageSlidesOnPreviewPayload(
  payload: PresentationPayload,
  livePlaylist: Playlist | null | undefined,
): PresentationPayload {
  if (!livePlaylist?.slides?.length || !payload.slides?.length) return payload;

  const byId = new Map<string, Slide>();
  for (const slide of livePlaylist.slides) {
    byId.set(slide.id, slide);
  }

  let changed = false;
  const slides = payload.slides.map((previewSlide) => {
    const live = byId.get(previewSlide.id);
    if (!live || live.nativeScreenKey !== "custom_message") return previewSlide;
    if (previewSlide.slideType !== "native" || !previewSlide.native) return previewSlide;

    const liveConfig = (live.nativeConfig ?? {}) as Record<string, unknown>;
    const serverData = (previewSlide.native.data ?? {}) as Record<string, unknown>;
    const nextData = mergeLiveBlocksOntoServerData(liveConfig, serverData);
    changed = true;
    return {
      ...previewSlide,
      title: live.title ?? previewSlide.title,
      native: {
        ...previewSlide.native,
        config: liveConfig,
        data: nextData,
        screenKey: "custom_message" as const,
      },
    };
  });

  return changed ? { ...payload, slides } : payload;
}
