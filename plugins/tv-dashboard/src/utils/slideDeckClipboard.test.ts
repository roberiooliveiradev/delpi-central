import { describe, expect, it } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import { pasteTitleFromClipboard, slidePayloadForClipboard } from "./slideDeckClipboard";

describe("slideDeckClipboard", () => {
  it("clona payload sem id para colar como nova tela", () => {
    const slide: Slide = {
      id: "s1",
      playlistId: "p1",
      sortOrder: 0,
      slideType: "native",
      title: "Produção",
      nativeScreenKey: "production_oee",
      nativeConfig: { branch: "01" },
      isActive: true,
    };
    const payload = slidePayloadForClipboard(slide);
    expect(payload).toEqual({
      slideType: "native",
      title: "Produção",
      nativeScreenKey: "production_oee",
      nativeConfig: { branch: "01" },
    });
    expect("id" in payload).toBe(false);
  });

  it("clona nativeConfig em profundidade (vídeo/assetId não compartilham referência)", () => {
    const slide: Slide = {
      id: "s1",
      playlistId: "p1",
      sortOrder: 0,
      slideType: "native",
      title: "Vídeo inicio",
      nativeScreenKey: "custom_message",
      nativeConfig: {
        version: 2,
        blocks: [{ id: "v1", type: "video", assetId: "asset-video", frame: { x: 0, y: 0, w: 40, h: 40 } }],
      },
      isActive: true,
    };
    const payload = slidePayloadForClipboard(slide);
    expect(payload.nativeConfig).toEqual(slide.nativeConfig);
    expect(payload.nativeConfig).not.toBe(slide.nativeConfig);
    const blocks = (payload.nativeConfig as { blocks: unknown[] }).blocks;
    expect(blocks).not.toBe((slide.nativeConfig as { blocks: unknown[] }).blocks);
    expect(blocks[0]).toMatchObject({ type: "video", assetId: "asset-video" });
  });

  it("evita duplicar sufixo (cópia) no título colado", () => {
    expect(pasteTitleFromClipboard({ slideType: "native", title: "Comunicado (cópia)" })).toBe(
      "Comunicado (cópia)",
    );
    expect(pasteTitleFromClipboard({ slideType: "native", title: "Comunicado" })).toBe(
      "Comunicado (cópia)",
    );
  });
});
