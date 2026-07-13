import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  applyComunicadoSlideDraft,
  clearComunicadoSlideDraft,
  comunicadoDraftIncludesPartKeys,
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

  it("persiste e relê draft por playlist+slide", () => {
    writeComunicadoSlideDraft("pl-1", "s-1", { blocks: [{ id: "b1", type: "text" }] }, 1000);
    const draft = readComunicadoSlideDraft("pl-1", "s-1");
    expect(draft?.updatedAt).toBe(1000);
    expect(draft?.nativeConfig).toEqual({ blocks: [{ id: "b1", type: "text" }] });
    expect(readComunicadoSlideDraft("pl-1", "s-2")).toBeNull();
  });

  it("normaliza payload inválido", () => {
    expect(normalizeComunicadoSlideDraft(null)).toBeNull();
    expect(normalizeComunicadoSlideDraft({ updatedAt: 1 })).toBeNull();
  });

  it("aplica e limpa draft", () => {
    writeComunicadoSlideDraft("pl-1", "s-1", { blocks: [] }, 50);
    const slide = applyComunicadoSlideDraft(
      { id: "s-1", nativeConfig: { blocks: [{ id: "old" }] } },
      readComunicadoSlideDraft("pl-1", "s-1"),
    );
    expect(slide.nativeConfig).toEqual({ blocks: [] });
    clearComunicadoSlideDraft("pl-1", "s-1");
    expect(readComunicadoSlideDraft("pl-1", "s-1")).toBeNull();
  });

  it("mergePlaylistSlidesWithComunicadoDrafts só em custom_message", () => {
    writeComunicadoSlideDraft("pl-1", "custom-1", { blocks: [{ id: "draft" }] }, 1);
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
