import { describe, expect, it } from "vitest";

import type { PresentationPayload, Playlist } from "../api/tvDashboardApi";
import {
  isPublicPresentMediaUrl,
  overlayLiveCustomMessageSlidesOnPreviewPayload,
  pickPreviewMediaUrl,
} from "./overlayLivePreviewPayload";

describe("overlayLiveCustomMessageSlidesOnPreviewPayload", () => {
  it("aplica blocks do shell local sobre o payload do servidor", () => {
    const live: Playlist = {
      id: "pl-1",
      name: "T",
      slides: [
        {
          id: "s-1",
          title: "Custom",
          slideType: "native",
          nativeScreenKey: "custom_message",
          nativeConfig: {
            blocks: [
              { id: "b1", type: "heading", content: "NOVO", frame: { x: 1, y: 2, w: 3, h: 4 } },
            ],
          },
        } as never,
      ],
    } as Playlist;

    const payload = {
      playlist: { id: "pl-1" },
      slides: [
        {
          id: "s-1",
          title: "Old",
          slideType: "native",
          native: {
            screenKey: "custom_message",
            config: { blocks: [{ id: "b1", type: "heading", content: "VELHO" }] },
            data: {
              blocks: [
                {
                  id: "b1",
                  type: "heading",
                  content: "VELHO",
                  resolved: { kpi: { value: 1 } },
                },
              ],
              master: { enabled: true, logo: { url: "https://x/logo.png" } },
            },
          },
        },
      ],
    } as unknown as PresentationPayload;

    const merged = overlayLiveCustomMessageSlidesOnPreviewPayload(payload, live);
    const blocks = (merged.slides[0].native?.data as { blocks: Array<Record<string, unknown>> })
      .blocks;
    expect(blocks[0].content).toBe("NOVO");
    expect(blocks[0].resolved).toEqual({ kpi: { value: 1 } });
    expect((merged.slides[0].native?.data as { master: unknown }).master).toEqual({
      enabled: true,
      logo: { url: "https://x/logo.png" },
    });
  });

  it("preserva URL pública de imagem quando o live traz URL admin", () => {
    const publicUrl = "/apps/tv-dashboard-api/public/present/tok/media/asset-1";
    const adminUrl = "/apps/tv-dashboard-api/playlists/pl-1/media/asset-1";
    const live: Playlist = {
      id: "pl-1",
      name: "T",
      slides: [
        {
          id: "s-1",
          title: "Custom",
          slideType: "native",
          nativeScreenKey: "custom_message",
          nativeConfig: {
            blocks: [
              {
                id: "logo",
                type: "image",
                assetId: "asset-1",
                url: adminUrl,
                frame: { x: 80, y: 5, w: 15, h: 12 },
              },
            ],
          },
        } as never,
      ],
    } as Playlist;

    const payload = {
      playlist: { id: "pl-1" },
      slides: [
        {
          id: "s-1",
          title: "Custom",
          slideType: "native",
          native: {
            screenKey: "custom_message",
            config: {},
            data: {
              blocks: [
                {
                  id: "logo",
                  type: "image",
                  assetId: "asset-1",
                  url: publicUrl,
                  frame: { x: 80, y: 5, w: 15, h: 12 },
                },
              ],
              master: {
                enabled: true,
                logo: { assetId: "asset-1", url: publicUrl, frame: { x: 2, y: 2, w: 12, h: 10 } },
              },
            },
          },
        },
      ],
    } as unknown as PresentationPayload;

    const merged = overlayLiveCustomMessageSlidesOnPreviewPayload(payload, live);
    const data = merged.slides[0].native?.data as {
      blocks: Array<{ url?: string; frame?: { x: number } }>;
      master: { logo: { url?: string } };
    };
    expect(data.blocks[0].url).toBe(publicUrl);
    expect(data.blocks[0].frame?.x).toBe(80);
    expect(data.master.logo.url).toBe(publicUrl);
  });

  it("preserva URL pública do master quando live só tem assetId", () => {
    const publicUrl = "/apps/tv-dashboard-api/public/present/tok/media/logo-1";
    const live: Playlist = {
      id: "pl-1",
      name: "T",
      slides: [
        {
          id: "s-1",
          title: "Custom",
          slideType: "native",
          nativeScreenKey: "custom_message",
          nativeConfig: {
            blocks: [],
            master: {
              enabled: true,
              logo: { assetId: "logo-1", frame: { x: 3, y: 3, w: 10, h: 8 } },
            },
          },
        } as never,
      ],
    } as Playlist;

    const payload = {
      playlist: { id: "pl-1" },
      slides: [
        {
          id: "s-1",
          slideType: "native",
          native: {
            screenKey: "custom_message",
            data: {
              blocks: [],
              master: {
                enabled: true,
                logo: { assetId: "logo-1", url: publicUrl, frame: { x: 2, y: 2, w: 12, h: 10 } },
              },
            },
          },
        },
      ],
    } as unknown as PresentationPayload;

    const merged = overlayLiveCustomMessageSlidesOnPreviewPayload(payload, live);
    const master = (merged.slides[0].native?.data as { master: { logo: Record<string, unknown> } })
      .master;
    expect(master.logo.url).toBe(publicUrl);
    expect(master.logo.frame).toEqual({ x: 3, y: 3, w: 10, h: 8 });
  });
});

describe("pickPreviewMediaUrl", () => {
  it("prioriza URL pública do servidor", () => {
    expect(
      pickPreviewMediaUrl(
        "/apps/tv-dashboard-api/playlists/p/media/a",
        "/apps/tv-dashboard-api/public/present/t/media/a",
      ),
    ).toBe("/apps/tv-dashboard-api/public/present/t/media/a");
    expect(isPublicPresentMediaUrl("/apps/tv-dashboard-api/public/present/t/media/a")).toBe(true);
  });

  it("ignora blob do live quando há URL do servidor", () => {
    expect(
      pickPreviewMediaUrl("blob:http://localhost/x", "/apps/tv-dashboard-api/playlists/p/media/a"),
    ).toBe("/apps/tv-dashboard-api/playlists/p/media/a");
  });
});
