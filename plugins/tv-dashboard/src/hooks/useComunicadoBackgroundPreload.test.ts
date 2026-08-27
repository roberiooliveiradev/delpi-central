import { describe, expect, it } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import { collectBackgroundMediaUrls } from "./useComunicadoBackgroundPreload";

describe("useComunicadoBackgroundPreload", () => {
  it("coleta assetIds de fundo de todos os slides e master", () => {
    const slides: Slide[] = [
      {
        id: "s1",
        playlistId: "pl-1",
        sortOrder: 0,
        slideType: "custom_message",
        title: "A",
        isActive: true,
        nativeConfig: {
          background: { type: "image", assetId: "bg-a" },
        },
      },
      {
        id: "s2",
        playlistId: "pl-1",
        sortOrder: 1,
        slideType: "custom_message",
        title: "B",
        isActive: true,
        nativeConfig: {
          background: { type: "color", value: "#003866" },
        },
      },
      {
        id: "s3",
        playlistId: "pl-1",
        sortOrder: 2,
        slideType: "custom_message",
        title: "C",
        isActive: true,
        nativeConfig: {
          background: { type: "image", assetId: "bg-c" },
        },
      },
    ];

    const urls = collectBackgroundMediaUrls("pl-1", slides, {
      enabled: true,
      background: { type: "image", assetId: "bg-master" },
    });

    expect(urls).toEqual([
      "/apps/tv-dashboard-api/playlists/pl-1/media/bg-a",
      "/apps/tv-dashboard-api/playlists/pl-1/media/bg-c",
      "/apps/tv-dashboard-api/playlists/pl-1/media/bg-master",
    ]);
  });
});
