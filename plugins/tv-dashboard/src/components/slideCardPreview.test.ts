import { describe, expect, it } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import { buildSlideThumbnailNative, externalSlideHost } from "./slideCardPreview";

describe("slideCardPreview", () => {
  it("monta preview de comunicado com URL admin para mídia", () => {
    const slide: Slide = {
      id: "s1",
      playlistId: "p1",
      sortOrder: 0,
      slideType: "native",
      title: "Comunicado",
      nativeScreenKey: "custom_message",
      nativeConfig: {
        version: 2,
        blocks: [
          {
            id: "b1",
            type: "image",
            assetId: "asset-1",
            frame: { x: 0, y: 0, w: 100, h: 100 },
          },
        ],
      },
      isActive: true,
    };
    const native = buildSlideThumbnailNative(slide, "playlist-1");
    expect(native?.screenKey).toBe("custom_message");
    const data = native?.data as { blocks?: Array<{ url?: string }> };
    expect(data.blocks?.[0]?.url).toBe("/apps/tv-dashboard-api/playlists/playlist-1/media/asset-1");
  });

  it("extrai host de URL externa", () => {
    expect(externalSlideHost("https://app.powerbi.com/view?r=abc")).toBe("app.powerbi.com");
  });
});
