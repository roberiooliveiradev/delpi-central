import type { PresentationPayload, Playlist, Slide } from "../api/tvDashboardApi";

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

/** URL de mídia do link público — carregável sem JWT no browser. */
export function isPublicPresentMediaUrl(url: string): boolean {
  return /\/public\/present\/[^/]+\/media\//i.test(url.trim());
}

/**
 * Preferir URL pública do servidor (prévia ≡ present).
 * Live do editor pode trazer URL admin, blob temporário ou omitir `url`.
 */
export function pickPreviewMediaUrl(liveUrl: unknown, serverUrl: unknown): string | undefined {
  const live = typeof liveUrl === "string" ? liveUrl.trim() : "";
  const server = typeof serverUrl === "string" ? serverUrl.trim() : "";
  if (server && isPublicPresentMediaUrl(server)) return server;
  if (live && !live.startsWith("blob:") && !isPublicPresentMediaUrl(live)) {
    // Admin / data URL do live — só se o servidor ainda não entregou pública.
    if (!server) return live;
  }
  if (live && isPublicPresentMediaUrl(live)) return live;
  if (server) return server;
  if (live && !live.startsWith("blob:")) return live;
  return undefined;
}

function mergeMediaFields(
  live: Record<string, unknown>,
  server: Record<string, unknown>,
): Record<string, unknown> {
  const url = pickPreviewMediaUrl(live.url, server.url);
  const out: Record<string, unknown> = { ...server, ...live };
  if (url) out.url = url;
  else delete out.url;
  return out;
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
        const type = typeof block.type === "string" ? block.type : server.type;
        const base =
          type === "image" || type === "video"
            ? mergeMediaFields(block, server)
            : { ...server, ...block };
        return {
          ...base,
          // Live manda layout/binding; resolved do servidor se o live ainda não tem.
          resolved: block.resolved ?? server.resolved,
        };
      })
    : serverBlocks;

  const liveBackground = isRecord(liveConfig.background) ? liveConfig.background : null;
  const serverBackground = isRecord(serverData.background) ? serverData.background : null;
  let background: Record<string, unknown> | undefined;
  if (liveBackground && serverBackground) {
    background =
      liveBackground.type === "image" || serverBackground.type === "image"
        ? mergeMediaFields(liveBackground, serverBackground)
        : { ...serverBackground, ...liveBackground };
  } else if (liveBackground) {
    background = liveBackground;
  } else if (serverBackground) {
    background = serverBackground;
  }

  const liveMaster = isRecord(liveConfig.master) ? liveConfig.master : null;
  const serverMaster = isRecord(serverData.master) ? serverData.master : null;
  let master: Record<string, unknown> | undefined;
  if (liveMaster || serverMaster) {
    master = mergeMasterForPreview(liveMaster, serverMaster);
  }

  return {
    ...serverData,
    ...liveConfig,
    blocks: mergedBlocks,
    ...(background ? { background } : {}),
    // Master enriquecido (URLs públicas) do servidor; live só layout/assetId.
    ...(master ? { master } : { master: liveConfig.master ?? serverData.master }),
  };
}

function mergeMasterForPreview(
  live: Record<string, unknown> | null,
  server: Record<string, unknown> | null,
): Record<string, unknown> | undefined {
  if (!live && !server) return undefined;
  const enabled = Boolean(live?.enabled ?? server?.enabled);
  if (!enabled) return undefined;

  const out: Record<string, unknown> = { enabled: true };

  const liveBg = isRecord(live?.background) ? live.background : null;
  const serverBg = isRecord(server?.background) ? server.background : null;
  if (liveBg || serverBg) {
    out.background =
      liveBg && serverBg
        ? mergeMediaFields(liveBg, serverBg)
        : (liveBg ?? serverBg)!;
  }

  const liveLogo = isRecord(live?.logo) ? live.logo : null;
  const serverLogo = isRecord(server?.logo) ? server.logo : null;
  if (liveLogo || serverLogo) {
    out.logo =
      liveLogo && serverLogo
        ? mergeMediaFields(liveLogo, serverLogo)
        : (liveLogo ?? serverLogo)!;
  }

  return out;
}

/**
 * Sobreposição do nativeConfig local (shell do editor) no preview-payload do servidor.
 * Mesma regra do filmstrip: durante a edição o servidor fica stale.
 * URLs `/public/present/.../media/` do servidor vencem admin/blob do live.
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
