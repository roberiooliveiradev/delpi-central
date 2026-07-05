import type { NativeSlidePayload } from "@delpi/tv-dashboard-presentation";
import { parseComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import { adminMediaUrl, type Slide } from "../api/tvDashboardApi";
import type { PresentationPayload } from "../api/tvDashboardApi";

export function buildSlideThumbnailNative(
  slide: Slide,
  playlistId: string,
  previewSlide?: PresentationPayload["slides"][number],
): NativeSlidePayload | null {
  if (slide.slideType !== "native" || !slide.nativeScreenKey) return null;

  if (previewSlide?.native) {
    return previewSlide.native;
  }

  if (slide.nativeScreenKey === "custom_message") {
    return {
      screenKey: "custom_message",
      config: slide.nativeConfig ?? {},
      data: buildComunicadoPreviewData(slide.nativeConfig ?? {}, playlistId),
    };
  }

  return {
    screenKey: slide.nativeScreenKey,
    config: slide.nativeConfig ?? {},
    data: { label: slide.title },
  };
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
  const blocks = (cfg.blocks ?? []).map((block) => {
    if ((block.type === "image" || block.type === "video") && block.assetId) {
      return {
        ...block,
        url: adminMediaUrl(playlistId, block.assetId),
      };
    }
    return block;
  });
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
