import type { ComunicadoConfig, ComunicadoBlock, NativeSlidePayload } from "@delpi/tv-dashboard-presentation";
import {
  parseComunicadoConfig,
  resolveTextBlockDisplayRuns,
  serializeComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import { withBrowserMediaAccessToken } from "../api/browserSafeMediaUrl";
import {
  adminMediaUrl,
  publicPresentMediaUrl,
  type PlaylistMasterConfig,
  type PresentationPayload,
  type Slide,
} from "../api/tvDashboardApi";
import { isPublicPresentMediaUrl } from "../utils/overlayLivePreviewPayload";

/** URL de mídia para render nativo (miniatura / CSS / img). */
function displayMediaUrl(
  playlistId: string,
  assetId: string,
  publicToken?: string | null,
): string {
  const token = typeof publicToken === "string" ? publicToken.trim() : "";
  // Mesmo contrato da prévia admin /present — access_token em URL admin é frágil.
  if (token) {
    return publicPresentMediaUrl(token, assetId);
  }
  return withBrowserMediaAccessToken(adminMediaUrl(playlistId, assetId));
}

/**
 * Resolve URL de exibição no editor a partir de `assetId` (preferencial) ou `url`.
 * Serialize omite `url` — sem isso o bloco fica no placeholder até re-enrich (troca de slide).
 * Editor carrega via Bearer→blob; mantém URL admin (sem token na query).
 */
export function resolveEditorMediaUrl(
  playlistId: string,
  assetId?: string | null,
  url?: string | null,
): string | undefined {
  const trimmedAsset = typeof assetId === "string" ? assetId.trim() : "";
  if (playlistId && trimmedAsset) {
    return adminMediaUrl(playlistId, trimmedAsset);
  }
  const trimmedUrl = typeof url === "string" ? url.trim() : "";
  return trimmedUrl || undefined;
}

/**
 * Garante `url` de mídia no config em memória do editor (não persistido).
 * Cobre insert/upload, undo via snapshot sem url e eco do pai só com assetId.
 */
export function ensureComunicadoEditorMediaUrls(
  config: ComunicadoConfig,
  playlistId: string,
): ComunicadoConfig {
  if (!playlistId) return config;

  let changed = false;

  let background = config.background;
  if (background?.type === "image" && background.assetId) {
    const url = adminMediaUrl(playlistId, background.assetId);
    if (background.url !== url) {
      background = { ...background, url };
      changed = true;
    }
  }

  let blocks = config.blocks;
  if (blocks?.length) {
    let blocksChanged = false;
    const nextBlocks = blocks.map((block) => {
      if ((block.type === "image" || block.type === "video") && block.assetId) {
        const url = adminMediaUrl(playlistId, block.assetId);
        if (block.url !== url) {
          blocksChanged = true;
          return { ...block, url };
        }
      }
      return block;
    });
    if (blocksChanged) {
      blocks = nextBlocks;
      changed = true;
    }
  }

  let customFonts = config.customFonts;
  if (customFonts?.length) {
    let fontsChanged = false;
    const nextFonts = customFonts.map((font) => {
      const url = adminMediaUrl(playlistId, font.assetId);
      if (font.url !== url) {
        fontsChanged = true;
        return { ...font, url };
      }
      return font;
    });
    if (fontsChanged) {
      customFonts = nextFonts;
      changed = true;
    }
  }

  if (!changed) return config;
  return {
    ...config,
    ...(background !== config.background ? { background } : {}),
    ...(blocks !== config.blocks ? { blocks } : {}),
    ...(customFonts !== config.customFonts ? { customFonts } : {}),
  };
}
/**
 * Serializa o config do editor com `resolved` dos blocos de dados/views —
 * necessário para o filmstrip ser o print do palco (gráficos/tabelas ao vivo).
 * Não usar em save persistente (resolved é efêmero).
 */
export function serializeComunicadoConfigForThumbnail(
  config: ComunicadoConfig,
  blocksWithResolved: ComunicadoBlock[],
): Record<string, unknown> {
  const serialized = serializeComunicadoConfig({ ...config, blocks: blocksWithResolved });
  const byId = new Map(blocksWithResolved.map((block) => [block.id, block]));
  const rawBlocks = Array.isArray(serialized.blocks) ? serialized.blocks : [];
  serialized.blocks = rawBlocks.map((raw) => {
    if (!raw || typeof raw !== "object") return raw;
    const row = raw as Record<string, unknown>;
    const id = typeof row.id === "string" ? row.id : "";
    const live = byId.get(id);
    if (!live || !("resolved" in live) || !live.resolved) return row;
    return { ...row, resolved: live.resolved };
  });
  return serialized;
}

/** True se algum bloco do nativeConfig carrega `resolved` (print com dados). */
export function nativeConfigHasResolvedData(config: Record<string, unknown> | null | undefined): boolean {
  if (!config || typeof config !== "object") return false;
  const blocks = config.blocks;
  if (!Array.isArray(blocks)) return false;
  return blocks.some(
    (block) =>
      block != null &&
      typeof block === "object" &&
      "resolved" in block &&
      (block as { resolved?: unknown }).resolved != null,
  );
}

const DATAISH_BLOCK_TYPES = new Set([
  "chart_view",
  "table_view",
  "kpi_view",
  "data_source",
  "data_kpi",
  "data_chart",
  "data_table",
  "data_metric",
]);

/** True se o config tem blocos de dados/visão que ainda precisam de `resolved` no print. */
export function nativeConfigNeedsResolvedData(config: Record<string, unknown> | null | undefined): boolean {
  if (!config || typeof config !== "object") return false;
  const blocks = config.blocks;
  if (!Array.isArray(blocks)) return false;
  return blocks.some((block) => {
    if (block == null || typeof block !== "object") return false;
    const type = String((block as { type?: unknown }).type ?? "");
    return DATAISH_BLOCK_TYPES.has(type);
  });
}

/**
 * Fingerprint estrutural (ids/tipos + background) — não inclui `resolved` nem frames.
 * Usado para impedir que print de outro slide seja preservado como «preview carregando».
 */
export function nativeConfigStructureFingerprint(
  config: Record<string, unknown> | null | undefined,
): string {
  if (!config || typeof config !== "object") return "";
  const background = config.background;
  const bgKey =
    background && typeof background === "object"
      ? JSON.stringify(background)
      : String(background ?? "");
  const blocks = Array.isArray(config.blocks) ? config.blocks : [];
  const blockKeys = blocks
    .map((block) => {
      if (block == null || typeof block !== "object") return "";
      const row = block as { id?: unknown; type?: unknown };
      return `${String(row.id ?? "")}:${String(row.type ?? "")}`;
    })
    .join("|");
  return `${bgKey}#${blockKeys}`;
}

/**
 * Monta a lista do filmstrip: slide ativo usa snapshot ao vivo (com resolved);
 * demais slides reutilizam cache para não “sumir” o gráfico ao trocar de tela.
 *
 * Só associa `liveThumbnailConfig` a `selectedSlideId` quando `liveSlideId` bate —
 * evita gravar o print do slide anterior no slot novo (1 frame de dessinc do React).
 *
 * Mantém print anterior só enquanto o live tem a **mesma estrutura** e ainda falta
 * `resolved` (preview carregando).
 */
export function buildFilmstripSlidesWithThumbnailCache(params: {
  slides: Slide[];
  selectedSlideId: string;
  liveThumbnailConfig: Record<string, unknown>;
  /**
   * Id do slide cujo config o editor já aplicou.
   * Se omitido, assume que live = selected (compat).
   * Se diferente de selectedSlideId, não grava o live no cache do selecionado.
   */
  liveSlideId?: string | null;
  cache: Record<string, Record<string, unknown>>;
}): Slide[] {
  const { slides, selectedSlideId, liveThumbnailConfig, cache } = params;
  const liveMatchesSelection =
    params.liveSlideId == null || params.liveSlideId === selectedSlideId;

  const liveIds = new Set(slides.map((slide) => slide.id));
  for (const id of Object.keys(cache)) {
    if (!liveIds.has(id)) delete cache[id];
  }

  if (!liveMatchesSelection) {
    return slides.map((slide) => {
      if (slide.slideType !== "native" || slide.nativeScreenKey !== "custom_message") {
        return slide;
      }
      const cached = cache[slide.id];
      if (cached) {
        return { ...slide, nativeConfig: cached };
      }
      return slide;
    });
  }

  const previous = cache[selectedSlideId];
  const liveHasResolved = nativeConfigHasResolvedData(liveThumbnailConfig);
  const previousHasResolved = nativeConfigHasResolvedData(previous);
  const liveNeedsResolved = nativeConfigNeedsResolvedData(liveThumbnailConfig);
  const structureMatches =
    previous == null ||
    nativeConfigStructureFingerprint(previous) ===
      nativeConfigStructureFingerprint(liveThumbnailConfig);
  const keepPreviousPrint =
    structureMatches && !liveHasResolved && liveNeedsResolved && previousHasResolved;

  if (!keepPreviousPrint) {
    cache[selectedSlideId] = liveThumbnailConfig;
  }

  const selectedNativeConfig = keepPreviousPrint
    ? (previous as Record<string, unknown>)
    : liveThumbnailConfig;

  return slides.map((slide) => {
    if (slide.slideType !== "native" || slide.nativeScreenKey !== "custom_message") {
      return slide;
    }
    if (slide.id === selectedSlideId) {
      return { ...slide, nativeConfig: selectedNativeConfig };
    }
    const cached = cache[slide.id];
    if (cached) {
      return { ...slide, nativeConfig: cached };
    }
    return slide;
  });
}

export function resolveMasterForPreview(
  master: PlaylistMasterConfig | undefined,
  playlistId: string,
  publicToken?: string | null,
): Record<string, unknown> | undefined {
  if (!master?.enabled) return undefined;
  const out: Record<string, unknown> = { enabled: true };
  const background = master.background;
  if (background) {
    if (background.type === "image" && background.assetId) {
      out.background = {
        ...background,
        url: displayMediaUrl(playlistId, background.assetId, publicToken),
      };
    } else if (background.type === "image" && background.url) {
      const url = String(background.url);
      out.background = {
        ...background,
        url: isPublicPresentMediaUrl(url) ? url : withBrowserMediaAccessToken(url),
      };
    } else {
      out.background = background;
    }
  }
  const logo = master.logo;
  if (logo) {
    const logoOut: Record<string, unknown> = { ...logo };
    if (logo.assetId) {
      logoOut.url = displayMediaUrl(playlistId, logo.assetId, publicToken);
    } else if (typeof logoOut.url === "string" && logoOut.url) {
      const url = String(logoOut.url);
      logoOut.url = isPublicPresentMediaUrl(url) ? url : withBrowserMediaAccessToken(url);
    }
    out.logo = logoOut;
  }
  return out;
}

/** Empilha master da seção sob o da playlist (mesma ordem da TV / API). */
export function mergeMasterConfigs(
  playlistMaster: PlaylistMasterConfig | undefined,
  sectionMaster: PlaylistMasterConfig | undefined,
): PlaylistMasterConfig | undefined {
  const pl = playlistMaster;
  const sec = sectionMaster;
  const plOn = Boolean(pl?.enabled);
  const secOn = Boolean(sec?.enabled);
  if (!plOn && !secOn) return undefined;

  let base: PlaylistMasterConfig | undefined = plOn && pl ? { ...pl, enabled: true } : undefined;
  if (!secOn || !sec) return base;

  const merged: PlaylistMasterConfig = {
    ...(base ?? {}),
    ...Object.fromEntries(
      Object.entries(sec).filter(([, value]) => value !== null && value !== undefined),
    ),
    enabled: true,
  };
  if (sec.background) {
    merged.background = {
      ...(base?.background ?? {}),
      ...sec.background,
    };
  }
  if (sec.logo) {
    merged.logo = {
      ...(base?.logo ?? {}),
      ...sec.logo,
    };
  }
  return merged;
}

export function buildSlideThumbnailNative(
  slide: Slide,
  playlistId: string,
  previewSlide?: PresentationPayload["slides"][number],
  masterConfig?: PlaylistMasterConfig,
  publicToken?: string | null,
): NativeSlidePayload | null {
  if (slide.slideType !== "native" || !slide.nativeScreenKey) return null;

  // Comunicado: sempre montar a partir do nativeConfig local (editor / save recente).
  // previewSlide.native do servidor fica stale durante a edição.
  if (slide.nativeScreenKey === "custom_message") {
    return {
      screenKey: "custom_message",
      config: slide.nativeConfig ?? {},
      data: buildComunicadoPreviewData(
        slide.nativeConfig ?? {},
        playlistId,
        masterConfig,
        publicToken,
      ),
    };
  }

  if (previewSlide?.native) {
    return previewSlide.native;
  }

  return {
    screenKey: slide.nativeScreenKey,
    config: slide.nativeConfig ?? {},
    data: { label: slide.title },
  };
}

export function enrichComunicadoConfigForEditor(
  raw: Record<string, unknown>,
  playlistId: string,
): ComunicadoConfig {
  const data = buildComunicadoPreviewData(raw, playlistId);
  return parseComunicadoConfig(data);
}

function buildComunicadoPreviewData(
  raw: Record<string, unknown>,
  playlistId: string,
  masterConfig?: PlaylistMasterConfig,
  publicToken?: string | null,
): Record<string, unknown> {
  const cfg = parseComunicadoConfig(raw);
  const background = cfg.background;
  let resolvedBackground = background ?? { type: "color" as const, value: "#ffffff" };
  if (resolvedBackground.type === "image" && resolvedBackground.assetId) {
    resolvedBackground = {
      ...resolvedBackground,
      url: displayMediaUrl(playlistId, resolvedBackground.assetId, publicToken),
    };
  }
  const blocks = enrichBlocksForEditorThumbnail(cfg.blocks ?? [], playlistId, publicToken);
  const master = resolveMasterForPreview(masterConfig, playlistId, publicToken);
  return {
    version: cfg.version ?? 2,
    headline: cfg.headline,
    subtitle: cfg.subtitle,
    // Sempre enviar fundo explícito — evita thumb preto (stage/#master escuro) em tela vazia.
    background: resolvedBackground,
    blocks,
    ...(cfg.dataFilters ? { dataFilters: cfg.dataFilters } : {}),
    ...(cfg.speakerNotes ? { speakerNotes: cfg.speakerNotes } : {}),
    ...(cfg.customFonts
      ? {
          customFonts: cfg.customFonts.map((font) => ({
            ...font,
            url: displayMediaUrl(playlistId, font.assetId, publicToken),
          })),
        }
      : {}),
    ...(master ? { master } : {}),
  };
}

export function externalSlideHost(url?: string | null): string {
  if (!url) return "Link externo";
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "Link externo";
  }
}

const THUMBNAIL_TEXT_PLACEHOLDER: Record<"heading" | "text", string> = {
  heading: "Título",
  text: "Texto",
};

/** Espelha placeholders visíveis no editor (não altera o config persistido). */
function enrichBlocksForEditorThumbnail(
  blocks: ComunicadoBlock[],
  playlistId: string,
  publicToken?: string | null,
): ComunicadoBlock[] {
  return blocks.map((block) => {
    if ((block.type === "image" || block.type === "video") && block.assetId) {
      return {
        ...block,
        url: displayMediaUrl(playlistId, block.assetId, publicToken),
      };
    }
    // chart_view / table_view / kpi_view / data_*: preservar `resolved` (print do palco).
    if (
      block.type === "chart_view" ||
      block.type === "table_view" ||
      block.type === "kpi_view" ||
      block.type === "data_source" ||
      ("resolved" in block && block.resolved)
    ) {
      return block;
    }
    if (block.type !== "heading" && block.type !== "text") {
      return block;
    }
    const runs = resolveTextBlockDisplayRuns(block);
    if (runs.some((run) => run.text.trim())) {
      return block;
    }
    return {
      ...block,
      content: THUMBNAIL_TEXT_PLACEHOLDER[block.type],
    };
  });
}
