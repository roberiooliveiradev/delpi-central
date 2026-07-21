import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  applyComunicadoSlideDraft,
  applyServerPlaylistPreservingLocalEdits,
  clearComunicadoSlideDraft,
  clearComunicadoSlideDraftIfCoveredBySave,
  comunicadoDraftIncludesPartKeys,
  hasLocalComunicadoEdits,
  mergePlaylistSlidesWithComunicadoDrafts,
  normalizeComunicadoSlideDraft,
  readComunicadoSlideDraft,
  writeComunicadoSlideDraft,
} from "./comunicadoSlideDraftPreferences";

describe("comunicadoSlideDraftPreferences", () => {
  const store = new Map<string, string>();

  beforeEach(() => {
    store.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("persiste e relê draft versionado por playlist+slide", () => {
    writeComunicadoSlideDraft("pl-1", "s-1", { blocks: [{ id: "b1", type: "text" }] }, 1000, 3);
    const draft = readComunicadoSlideDraft("pl-1", "s-1");
    expect(draft?.updatedAt).toBe(1000);
    expect(draft?.version).toBe(3);
    expect(draft?.nativeConfig).toEqual({ blocks: [{ id: "b1", type: "text" }] });
    expect(readComunicadoSlideDraft("pl-1", "s-2")).toBeNull();
  });

  it("normaliza payload inválido e version legado = 0", () => {
    expect(normalizeComunicadoSlideDraft(null)).toBeNull();
    expect(normalizeComunicadoSlideDraft({ updatedAt: 1 })).toBeNull();
    expect(
      normalizeComunicadoSlideDraft({ updatedAt: 1, nativeConfig: { blocks: [] } })?.version,
    ).toBe(0);
  });

  it("save antigo não apaga draft mais novo (causa raiz F5)", () => {
    writeComunicadoSlideDraft("pl-1", "s-1", { blocks: [{ id: "ABC" }] }, 1, 1);
    // Usuário editou de novo enquanto updateSlide(v1) ainda voava.
    writeComunicadoSlideDraft("pl-1", "s-1", { blocks: [{ id: "ABCD" }] }, 2, 2);
    expect(clearComunicadoSlideDraftIfCoveredBySave("pl-1", "s-1", 1)).toBe(false);
    expect(readComunicadoSlideDraft("pl-1", "s-1")?.nativeConfig).toEqual({
      blocks: [{ id: "ABCD" }],
    });
    expect(clearComunicadoSlideDraftIfCoveredBySave("pl-1", "s-1", 2)).toBe(true);
    expect(readComunicadoSlideDraft("pl-1", "s-1")).toBeNull();
  });

  it("aplica e limpa draft", () => {
    writeComunicadoSlideDraft("pl-1", "s-1", { blocks: [] }, 50, 1);
    const slide = applyComunicadoSlideDraft(
      { id: "s-1", nativeConfig: { blocks: [{ id: "old" }] } },
      readComunicadoSlideDraft("pl-1", "s-1"),
    );
    expect(slide.nativeConfig).toEqual({ blocks: [] });
    clearComunicadoSlideDraft("pl-1", "s-1");
    expect(readComunicadoSlideDraft("pl-1", "s-1")).toBeNull();
  });

  it("mergePlaylistSlidesWithComunicadoDrafts só em custom_message", () => {
    writeComunicadoSlideDraft("pl-1", "custom-1", { blocks: [{ id: "draft" }] }, 1, 1);
    const merged = mergePlaylistSlidesWithComunicadoDrafts("pl-1", {
      id: "pl-1",
      slides: [
        {
          id: "custom-1",
          nativeScreenKey: "custom_message",
          nativeConfig: { blocks: [] },
        },
        {
          id: "native-1",
          nativeScreenKey: "oee",
          nativeConfig: { foo: 1 },
        },
      ],
    });
    expect(merged.slides?.[0]?.nativeConfig).toEqual({ blocks: [{ id: "draft" }] });
    expect(merged.slides?.[1]?.nativeConfig).toEqual({ foo: 1 });
  });

  it("applyServerPlaylistPreservingLocalEdits: draft + pending + live", () => {
    writeComunicadoSlideDraft("pl-1", "s-1", { blocks: [{ id: "draft" }] }, 1, 1);
    const merged = applyServerPlaylistPreservingLocalEdits({
      playlistId: "pl-1",
      remote: {
        id: "pl-1",
        slides: [
          {
            id: "s-1",
            nativeScreenKey: "custom_message",
            nativeConfig: { blocks: [{ id: "server" }] },
          },
        ],
      },
      pending: { slideId: "s-1", nativeConfig: { blocks: [{ id: "pending" }] } },
      live: { slideId: "s-1", nativeConfig: { blocks: [{ id: "live" }] } },
    });
    // Pending tem prioridade sobre draft; live só se não houver pending.
    expect(merged.slides?.[0]?.nativeConfig).toEqual({ blocks: [{ id: "pending" }] });
  });

  it("hasLocalComunicadoEdits detecta draft ou pending", () => {
    expect(hasLocalComunicadoEdits({ playlistId: "pl-1", slideId: "s-1" })).toBe(false);
    writeComunicadoSlideDraft("pl-1", "s-1", { blocks: [] }, 1, 1);
    expect(hasLocalComunicadoEdits({ playlistId: "pl-1", slideId: "s-1" })).toBe(true);
    expect(
      hasLocalComunicadoEdits({
        playlistId: "pl-1",
        slideId: "s-2",
        pendingSlideId: "s-2",
      }),
    ).toBe(true);
  });

  it("reconhece kpiParts/chartParts no config (subitens)", () => {
    expect(
      comunicadoDraftIncludesPartKeys({
        blocks: [{ id: "k1", type: "kpi_view", kpiParts: { title: { frame: { x: 1 } } } }],
      }),
    ).toBe(true);
    expect(
      comunicadoDraftIncludesPartKeys({
        blocks: [{ id: "c1", type: "chart_view", chartParts: { title: {} } }],
      }),
    ).toBe(true);
    expect(comunicadoDraftIncludesPartKeys({ blocks: [{ id: "t", type: "text" }] })).toBe(false);
  });
});
