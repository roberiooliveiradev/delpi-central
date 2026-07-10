import { describe, expect, it } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import { buildSlideThumbnailNative, externalSlideHost } from "./slideCardPreview";

describe("slideCardPreview", () => {
  it("comunicado ignora previewSlide.native stale e usa nativeConfig local", () => {
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
            type: "heading",
            content: "Ao vivo",
            frame: { x: 10, y: 10, w: 80, h: 20 },
          },
        ],
      },
      isActive: true,
    };
    const native = buildSlideThumbnailNative(slide, "playlist-1", {
      id: "s1",
      native: {
        screenKey: "custom_message",
        config: {},
        data: {
          version: 2,
          blocks: [
            {
              id: "b1",
              type: "heading",
              content: "Desatualizado",
              frame: { x: 0, y: 0, w: 100, h: 100 },
            },
          ],
        },
      },
    });
    const data = native?.data as { blocks?: Array<{ content?: string }> };
    expect(data.blocks?.[0]?.content).toBe("Ao vivo");
  });

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

  it("preenche placeholder de texto vazio na miniatura do editor", () => {
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
            type: "heading",
            content: "",
            frame: { x: 10, y: 5, w: 80, h: 15 },
          },
        ],
      },
      isActive: true,
    };
    const native = buildSlideThumbnailNative(slide, "playlist-1");
    const data = native?.data as { blocks?: Array<{ content?: string }> };
    expect(data.blocks?.[0]?.content).toBe("Título");
  });

  it("extrai host de URL externa", () => {
    expect(externalSlideHost("https://app.powerbi.com/view?r=abc")).toBe("app.powerbi.com");
  });
});
