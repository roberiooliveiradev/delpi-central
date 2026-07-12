import type { ComunicadoConfig, ComunicadoBlock, NativeSlidePayload } from "@delpi/tv-dashboard-presentation";
import {
  parseComunicadoConfig,
  resolveTextBlockDisplayRuns,
  serializeComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, type PlaylistMasterConfig, type Slide } from "../api/tvDashboardApi";
import type { PresentationPayload } from "../api/tvDashboardApi";

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

export function resolveMasterForPreview(
  master: PlaylistMasterConfig | undefined,
  playlistId: string,
): Record<string, unknown> | undefined {
  if (!master?.enabled) return undefined;
  const out: Record<string, unknown> = { enabled: true };
  const background = master.background;
  if (background) {
    if (background.type === "image" && background.assetId) {
      out.background = {
        ...background,
        url: background.url ?? adminMediaUrl(playlistId, background.assetId),
      };
    } else {
      out.background = background;
    }
  }
  const logo = master.logo;
  if (logo) {
    const logoOut: Record<string, unknown> = { ...logo };
    if (logo.assetId && !logo.url) {
      logoOut.url = adminMediaUrl(playlistId, logo.assetId);
    }
    out.logo = logoOut;
  }
  return out;
}

export function buildSlideThumbnailNative(
  slide: Slide,
  playlistId: string,
  previewSlide?: PresentationPayload["slides"][number],
  masterConfig?: PlaylistMasterConfig,
): NativeSlidePayload | null {
  if (slide.slideType !== "native" || !slide.nativeScreenKey) return null;

  // Comunicado: sempre montar a partir do nativeConfig local (editor / save recente).
  // previewSlide.native do servidor fica stale durante a edição.
  if (slide.nativeScreenKey === "custom_message") {
    return {
      screenKey: "custom_message",
      config: slide.nativeConfig ?? {},
      data: buildComunicadoPreviewData(slide.nativeConfig ?? {}, playlistId, masterConfig),
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
): Record<string, unknown> {
  const cfg = parseComunicadoConfig(raw);
  const background = cfg.background;
  let resolvedBackground = background;
  if (background?.type === "image" && background.assetId) {
    resolvedBackground = {
      ...background,
      url: adminMediaUrl(playlistId, background.assetId),
    };
  }
  const blocks = enrichBlocksForEditorThumbnail(cfg.blocks ?? [], playlistId);
  const master = resolveMasterForPreview(masterConfig, playlistId);
  return {
    version: cfg.version ?? 2,
    headline: cfg.headline,
    subtitle: cfg.subtitle,
    background: resolvedBackground,
    blocks,
    ...(cfg.dataFilters ? { dataFilters: cfg.dataFilters } : {}),
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
): ComunicadoBlock[] {
  return blocks.map((block) => {
    if ((block.type === "image" || block.type === "video") && block.assetId) {
      return {
        ...block,
        url: adminMediaUrl(playlistId, block.assetId),
      };
    }
    // chart_view / table_view / data_*: preservar `resolved` (print do palco).
    if (
      block.type === "chart_view" ||
      block.type === "table_view" ||
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
