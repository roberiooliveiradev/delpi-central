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

  it("evita duplicar sufixo (cópia) no título colado", () => {
    expect(pasteTitleFromClipboard({ slideType: "native", title: "Comunicado (cópia)" })).toBe(
      "Comunicado (cópia)",
    );
    expect(pasteTitleFromClipboard({ slideType: "native", title: "Comunicado" })).toBe(
      "Comunicado (cópia)",
    );
  });
});
