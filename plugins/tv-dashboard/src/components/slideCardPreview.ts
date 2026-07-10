import type { ComunicadoConfig, ComunicadoBlock, NativeSlidePayload } from "@delpi/tv-dashboard-presentation";
import { parseComunicadoConfig, resolveTextBlockDisplayRuns } from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, type Slide } from "../api/tvDashboardApi";
import type { PresentationPayload } from "../api/tvDashboardApi";

export function buildSlideThumbnailNative(
  slide: Slide,
  playlistId: string,
  previewSlide?: PresentationPayload["slides"][number],
): NativeSlidePayload | null {
  if (slide.slideType !== "native" || !slide.nativeScreenKey) return null;

  // Comunicado: sempre montar a partir do nativeConfig local (editor / save recente).
  // previewSlide.native do servidor fica stale durante a edição.
  if (slide.nativeScreenKey === "custom_message") {
    return {
      screenKey: "custom_message",
      config: slide.nativeConfig ?? {},
      data: buildComunicadoPreviewData(slide.nativeConfig ?? {}, playlistId),
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
  return {
    version: 2,
    headline: cfg.headline,
    subtitle: cfg.subtitle,
    background: resolvedBackground,
    blocks,
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
