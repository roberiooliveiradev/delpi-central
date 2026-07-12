import { describe, expect, it } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import {
  buildFilmstripSlidesWithThumbnailCache,
  buildSlideThumbnailNative,
  externalSlideHost,
  serializeComunicadoConfigForThumbnail,
} from "./slideCardPreview";

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

  it("serializeComunicadoConfigForThumbnail preserva resolved do chart_view", () => {
    const config = {
      version: 4 as const,
      background: { type: "color" as const, value: "#ffffff" },
      blocks: [],
    };
    const blocks = [
      {
        id: "chart-1",
        type: "chart_view" as const,
        chartType: "line" as const,
        frame: { x: 10, y: 20, w: 80, h: 50 },
        style: {},
        chartOptions: { title: "OTD — série temporal" },
        resolved: {
          label: "OTD — série temporal",
          chart: {
            points: [
              { label: "11/06/26", value: 42 },
              { label: "10/07/26", value: 100 },
            ],
          },
        },
      },
    ];
    const serialized = serializeComunicadoConfigForThumbnail(config as never, blocks as never);
    const outBlocks = serialized.blocks as Array<{
      id?: string;
      resolved?: { chart?: { points?: unknown[] } };
    }>;
    expect(outBlocks[0]?.id).toBe("chart-1");
    expect(outBlocks[0]?.resolved?.chart?.points).toHaveLength(2);

    const slide: Slide = {
      id: "s1",
      playlistId: "p1",
      sortOrder: 0,
      slideType: "native",
      title: "Personalizado",
      nativeScreenKey: "custom_message",
      nativeConfig: serialized,
      isActive: true,
    };
    const native = buildSlideThumbnailNative(slide, "playlist-1");
    const data = native?.data as {
      blocks?: Array<{ resolved?: { chart?: { points?: unknown[] } } }>;
    };
    expect(data.blocks?.[0]?.resolved?.chart?.points).toHaveLength(2);
  });

  it("extrai host de URL externa", () => {
    expect(externalSlideHost("https://app.powerbi.com/view?r=abc")).toBe("app.powerbi.com");
  });

  it("buildFilmstripSlidesWithThumbnailCache preserva resolved ao trocar de slide", () => {
    const cache: Record<string, Record<string, unknown>> = {};
    const chartConfig = serializeComunicadoConfigForThumbnail(
      {
        version: 4 as const,
        background: { type: "color" as const, value: "#ffffff" },
        blocks: [],
      } as never,
      [
        {
          id: "chart-1",
          type: "chart_view" as const,
          chartType: "line" as const,
          frame: { x: 10, y: 20, w: 80, h: 50 },
          style: {},
          resolved: {
            label: "OTD",
            chart: { points: [{ label: "A", value: 1 }] },
          },
        },
      ] as never,
    );
    const blankConfig = {
      version: 4,
      background: { type: "color", value: "#ffffff" },
      blocks: [],
    };
    const slides: Slide[] = [
      {
        id: "s1",
        playlistId: "p1",
        sortOrder: 0,
        slideType: "native",
        title: "Com gráfico",
        nativeScreenKey: "custom_message",
        nativeConfig: { version: 4, blocks: [] },
        isActive: true,
      },
      {
        id: "s2",
        playlistId: "p1",
        sortOrder: 1,
        slideType: "native",
        title: "Em branco",
        nativeScreenKey: "custom_message",
        nativeConfig: blankConfig,
        isActive: true,
      },
    ];

    buildFilmstripSlidesWithThumbnailCache({
      slides,
      selectedSlideId: "s1",
      liveThumbnailConfig: chartConfig,
      cache,
    });

    const afterSwitch = buildFilmstripSlidesWithThumbnailCache({
      slides,
      selectedSlideId: "s2",
      liveThumbnailConfig: blankConfig,
      cache,
    });

    const chartBlocks = afterSwitch[0]?.nativeConfig?.blocks as Array<{
      resolved?: { chart?: { points?: unknown[] } };
    }>;
    expect(chartBlocks?.[0]?.resolved?.chart?.points).toHaveLength(1);
    expect(afterSwitch[1]?.nativeConfig?.background).toEqual({ type: "color", value: "#ffffff" });
  });

  it("tela vazia na miniatura usa fundo branco explícito", () => {
    const slide: Slide = {
      id: "s2",
      playlistId: "p1",
      sortOrder: 1,
      slideType: "native",
      title: "Personalizado 2",
      nativeScreenKey: "custom_message",
      nativeConfig: { version: 4, blocks: [] },
      isActive: true,
    };
    const native = buildSlideThumbnailNative(slide, "playlist-1", undefined, {
      enabled: true,
      background: { type: "color", value: "#0f172a" },
    });
    const data = native?.data as { background?: { type?: string; value?: string } };
    expect(data.background).toEqual({ type: "color", value: "#ffffff" });
  });
});
