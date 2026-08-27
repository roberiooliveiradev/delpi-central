import { useEffect, useMemo } from "react";

import { parseComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import type { PlaylistMasterConfig, Slide } from "../api/tvDashboardApi";
import { resolveEditorMediaUrl } from "../components/slideCardPreview";
import { prefetchAuthenticatedBlobUrl } from "./authenticatedBlobUrlCache";

function collectBackgroundMediaUrls(
  playlistId: string,
  slides: readonly Slide[],
  masterConfig?: PlaylistMasterConfig,
): string[] {
  const urls = new Set<string>();

  for (const slide of slides) {
    const cfg = parseComunicadoConfig(slide.nativeConfig);
    const background = cfg.background;
    if (background?.type === "image" && background.assetId) {
      const url = resolveEditorMediaUrl(playlistId, background.assetId, background.url);
      if (url) urls.add(url);
    }
  }

  const masterBackground = masterConfig?.enabled ? masterConfig.background : undefined;
  if (masterBackground?.type === "image" && masterBackground.assetId) {
    const url = resolveEditorMediaUrl(playlistId, masterBackground.assetId, masterBackground.url);
    if (url) urls.add(url);
  }

  return [...urls];
}

/** Aquece blobs de fundo de todos os slides da playlist (cache compartilhado). */
export function useComunicadoBackgroundPreload(options: {
  playlistId: string;
  slides: readonly Slide[];
  masterConfig?: PlaylistMasterConfig;
}) {
  const mediaUrls = useMemo(
    () => collectBackgroundMediaUrls(options.playlistId, options.slides, options.masterConfig),
    [options.masterConfig, options.playlistId, options.slides],
  );

  useEffect(() => {
    const releases = mediaUrls.map((url) => prefetchAuthenticatedBlobUrl(url));
    return () => {
      for (const release of releases) release();
    };
  }, [mediaUrls]);
}

export { collectBackgroundMediaUrls };
